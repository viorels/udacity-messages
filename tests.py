import unittest
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

from models import Message, GroupMessage, UserProfile
from google.appengine.api.users import User

class TestModel(db.Model):
  """A model class used for testing."""
  number = db.IntegerProperty(default=42)
  text = db.StringProperty()

class TestEntityGroupRoot(db.Model):
  """Entity group root"""
  pass


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

        self.testbed.init_memcache_stub()

        self.user1 = User('user1@domain.com')
        self.user2 = User('user2@domain.com')

    def tearDown(self):
        self.testbed.deactivate()

    def _sendMessage(self):
        Message.send(from_user=self.user1,
                     to_user=self.user2,
                     subject='subject',
                     content='content')

    def _sendGroupMessage(self):
        GroupMessage.send(from_user=self.user1,
                          to_group='all',
                          subject='subject',
                          content='content')


class MessagesTestCase(BaseTestCase):

    def setUp(self):
        super(MessagesTestCase, self).setUp()
        self.testbed.init_datastore_v3_stub()

    def testSendMessage(self):
        self._sendMessage()
        self.assertEqual(1, Message.query().count())

    def testSendMessageDetails(self):
        self._sendMessage()
        (message,) = Message.query().fetch(1)
        self.assertEqual(message.from_user.email(), self.user1.email())
        self.assertEqual(message.to_user.email(), self.user2.email())
        self.assertEqual(message.subject, 'subject')
        self.assertEqual(message.content, 'content')

    def testInbox(self):
        self._sendMessage()
        self._sendMessage()
        messages = Message.list_for_user(self.user2)
        self.assertEqual(2, len(messages))

    def testSendGroupMessage(self):
        # user logs in for the first time
        UserProfile.for_user(self.user2)

        # send group message and check if it's recorded
        self._sendGroupMessage()
        self.assertEqual(1, GroupMessage.query().count())

        # no 1 to 1 messages are stored until the user checks inbox
        self.assertEqual(0, Message.query().count())

        # after checking messages a copy of the group message is stored in inbox
        messages = Message.list_for_user(self.user2)
        self.assertEqual(1, len(messages))

    def testAnyUserBelongsToAllGroup(self):
        groups = UserProfile.for_user(self.user2).get_all_groups()
        self.assertEqual(groups, ['all'])

    def testAddUserToGroup(self):
        user_profile = UserProfile.for_user(self.user2)
        user_profile.update_groups(['python'])

        # get_all_groups returns the prefered group and 'all'
        groups = user_profile.get_all_groups()
        self.assertEqual(sorted(groups), sorted(['all', 'python']))


class ConsistencyTestCase(BaseTestCase):
    def setUp(self):
        super(ConsistencyTestCase, self).setUp()
        # Create a consistency policy that will simulate the High Replication consistency model.
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
        # Initialize the datastore stub with this policy.
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

    def testEventuallyConsistentGlobalQueryResult(self):
        class TestModel(db.Model):
          pass

        user_key = db.Key.from_path('User', 'ryan')
        # Put two entities
        db.put([TestModel(parent=user_key), TestModel(parent=user_key)])

        # Global query doesn't see the data.
        self.assertEqual(0, TestModel.all().count(3))
        # Ancestor query does see the data.
        self.assertEqual(2, TestModel.all().ancestor(user_key).count(3))


if __name__ == '__main__':
    unittest.main()
