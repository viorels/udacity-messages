import logging
from google.appengine.ext import ndb


class User(ndb.Model):
    groups = ndb.StringProperty(repeated=True)


class Message(ndb.Model):
    """Models a one to one message"""
    from_user = ndb.UserProperty()
    to_user = ndb.UserProperty()
    sent_time = ndb.DateTimeProperty(auto_now_add=True)
    subject = ndb.StringProperty(indexed=False)
    content = ndb.TextProperty(indexed=False)
    is_read = ndb.BooleanProperty(indexed=False, default=False)
    is_deleted = ndb.BooleanProperty(indexed=False, default=False)

    def unread_count(self, user):
        """Returns the count of unread messages for specified user"""
        pass

    @classmethod
    def get_messages(self, user, older_then, limit):
        """Returns a list of messages delivered for the specified user"""
        # TODO: use saved cursors for pagination
        cls.query()

    @classmethod
    def send(cls, from_user, to_user, subject, content):
        message = Message(from_user=from_user,
                          to_user=to_user,
                          subject=subject,
                          content=content)
        key = message.put()
        logging.debug('send %s => %s' % (subject, key))

    @classmethod
    def populate(cls, user, count=42):
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

    def send(self, from_user, to_user, subject, content):
        pass
