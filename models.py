import logging
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor

def user_key(user):
    """Constructs a Datastore key based on user's email"""
    return ndb.Key('User', user.email())


class UserProfile(ndb.Model):
    user = ndb.UserProperty()
    groups = ndb.StringProperty(repeated=True)  # use update_groups to write property
    last_group_message = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def for_user(cls, user):
        return cls.get_or_insert(user_key(user).id(), user=user)

    def get_unread_count(self, limit):
        return Message.list_query(self.user).filter(Message.is_read == False).count(limit=limit)

    def update_groups(self, groups):
        """ Update user groups. Don't update groups manually in order to avoid
            group messages inconsistencies """
        self.fetch_group_messages()    # preload messages before updating groups
        self.groups = groups
        self.put()

    def is_in_group(self, group):
        """ Check if user is in specified group """
        return group in self.get_all_groups()

    def get_all_groups(self):
        """ Return saved groups and special group 'all' """
        return self.groups + ['all']

    def fetch_group_messages(self):
        """ Method called before listing messages to search for new group messages
            and insert them in users inbox """
        last_time = self.last_group_message
        for group_message in GroupMessage.query(GroupMessage.to_group.IN(self.get_all_groups()),
                                                GroupMessage.sent_time > self.last_group_message):
            Message.send(from_user=group_message.from_user,
                         to_user=self.user,
                         to_group=group_message.to_group,
                         sent_time=group_message.sent_time,
                         subject=group_message.subject,
                         content=group_message.content)
            if group_message.sent_time > last_time:
                last_time = group_message.sent_time
        self.last_group_message = last_time
        self.put()


class Message(ndb.Model):
    """Models a one to one message"""
    # parent = user_key(to_user)
    from_user = ndb.UserProperty()
    to_user = ndb.UserProperty()
    to_group = ndb.StringProperty(indexed=False)
    sent_time = ndb.DateTimeProperty(auto_now_add=True)
    subject = ndb.StringProperty(indexed=False)
    content = ndb.TextProperty(indexed=False)
    is_read = ndb.BooleanProperty(indexed=True, default=False)

    def get_url(self):
        return "/message/" + self.key.urlsafe()

    @classmethod
    def get_message(cls, message_key_url):
        message = ndb.Key(urlsafe=message_key_url).get()
        if message and not message.is_read:
            message.is_read = True
            message.put()
        return message

    @classmethod
    def delete(cls, message_key_url):
        """ Delete message with specified key encoded in url format """
        ndb.Key(urlsafe=message_key_url).delete()

    @classmethod
    def list_for_user(cls, user, cursor_url=None, limit=10):
        """ Returns a list of messages delivered for the specified user """
        cursor = Cursor(urlsafe=cursor_url)
        messages, next_cursor, more = cls.list_query(user).fetch_page(limit, start_cursor=cursor)
        return (messages, next_cursor, more)

    @classmethod
    def list_query(cls, user):
        UserProfile.for_user(user).fetch_group_messages()
        return cls.query(ancestor=user_key(user)).order(-Message.sent_time)

    @classmethod
    def send(cls, from_user, to_user, subject, content, to_group=None, sent_time=None):
        if sent_time is None:
            sent_time = datetime.utcnow()
        message = Message(parent=user_key(to_user),
                          from_user=from_user,
                          to_user=to_user,
                          to_group=to_group,
                          sent_time=sent_time,
                          subject=subject,
                          content=content)
        key = message.put()
        logging.info('send %s => %s' % (subject, key))

    @classmethod
    def populate(cls, user, count=1):
        """ Fill database with some random data """
        for i in range(count):
            cls.send(from_user=user, to_user=user,
                     subject="subject %d" % i,
                     content="content %d" % i)


class GroupMessage(ndb.Model):
    """Models a group message"""
    from_user = ndb.UserProperty()
    to_group = ndb.StringProperty(indexed=True)
    subject = ndb.StringProperty(indexed=False)
    content = ndb.TextProperty(indexed=False)
    sent_time = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def send(cls, from_user, to_group, subject, content):
        message = GroupMessage(from_user=from_user,
                               to_group=to_group,
                               subject=subject,
                               content=content)
        key = message.put()
        logging.info('group send %s => %s' % (subject, key))
