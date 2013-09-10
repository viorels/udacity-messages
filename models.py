import logging
from google.appengine.ext import ndb


def user_key(user):
    """Constructs a Datastore key based on user's email"""
    return ndb.Key('User', user.email())


class UserProfile(ndb.Model):
    # parent = user_key(user)
    user = ndb.UserProperty()
    groups = ndb.StringProperty(repeated=True)


class Message(ndb.Model):
    """Models a one to one message"""
    # parent = user_key(to_user)
    from_user = ndb.UserProperty()
    to_user = ndb.UserProperty()
    sent_time = ndb.DateTimeProperty(auto_now_add=True)
    subject = ndb.StringProperty(indexed=False)
    content = ndb.TextProperty(indexed=False)
    is_read = ndb.BooleanProperty(indexed=False, default=False)
    is_deleted = ndb.BooleanProperty(indexed=False, default=False)

    def get_url(self):
        return "/message/" + self.key.urlsafe()

    @classmethod
    def get_message(cls, message_key_url):
        message = ndb.Key(urlsafe=message_key_url).get()
        message.is_read = True
        message.put()
        return message

    @classmethod
    def list_for_user(cls, user, limit=20):
        """Returns a list of messages delivered for the specified user"""
        # TODO: use saved cursors for pagination
        return cls.query(ancestor=user_key(user)).order(-Message.sent_time).fetch(limit)

    @classmethod
    def send(cls, from_user, to_user, subject, content):
        message = Message(parent=user_key(to_user),
                          from_user=from_user,
                          to_user=to_user,
                          subject=subject,
                          content=content)
        key = message.put()
        logging.info('send %s => %s' % (subject, key))

    @classmethod
    def populate(cls, user, count=1):
        for i in range(count):
            cls.send(from_user=user, to_user=user,
                     subject="subject %d" % i,
                     content="content %d" % i)


class GroupMessage(ndb.Model):
    """Models a one to one message"""
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
