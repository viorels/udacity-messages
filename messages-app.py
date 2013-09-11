import cgi
import logging
import os
import webapp2
import jinja2
from google.appengine.api import users

from models import Message, GroupMessage, UserProfile

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

app_path = os.path.dirname(__file__)
templates_path = os.path.join(app_path, 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(templates_path),
    extensions=['jinja2.ext.autoescape'])


class BaseRequestHandler(webapp2.RequestHandler):
    """Supplies a common template rendering function.
    When you call render(), we augment the template variables supplied with
    common ones like logged in 'user' and 'request' context
    """

    def render(self, template_name, template_values={}):
        self.response.headers['Content-Type'] = 'text/html'
        values = {
            'request': self.request,
            'user': users.get_current_user(),
            'login_url': users.create_logout_url(self.request.uri),
            'logout_url': users.create_logout_url('/'),
            'nav_active': self.page_name(),
            'application_name': 'Udacity Messages',
            'unread_count': self.unread_messages_count(),
        }
        values.update(template_values)
        template = JINJA_ENVIRONMENT.get_template(template_name)
        self.response.out.write(template.render(values))

    def page_name(self):
        return self.request.path.lstrip('/')

    def unread_messages_count(self):
        user = users.get_current_user()
        unread_limit = 99
        unread_count = UserProfile.for_user(user).get_unread_count(unread_limit)
        if unread_count == unread_limit:
            unread_count = '%s+' % unread_limit
        return unread_count


class MainPage(BaseRequestHandler):
    def get(self):
        self.render('home.html')


class InboxPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        self.render("inbox.html", {'messages': Message.list_for_user(user)})


class MessagePage(BaseRequestHandler):
    def get(self, message_key_url):
        message = Message.get_message(message_key_url)
        if message is not None:
            if message.to_user.user_id() == users.get_current_user().user_id():
                self.render("message.html", {'message': message})
            else:
                self.error(403)
        else:
            self.error(404)

    def post(self, message_key_url):
        action = self.request.get('action')
        if action == 'delete':
            message = Message.get_message(message_key_url)
            if message is not None:
                if message.to_user.user_id() == users.get_current_user().user_id():
                    Message.delete(message_key_url)
                    self.redirect("/inbox")
                else:
                    self.error(403)
            else:
                self.error(404)


class ComposePage(BaseRequestHandler):
    def get(self):
        self.render('compose.html')

    def post(self):
        # TODO: users.is_current_user_admin() ? can he send a group message ?
        to = self.request.get('to')
        subject = self.request.get('subject')
        content = self.request.get('content')
        from_user = users.get_current_user()

        if self.is_valid_group(to):
            group = to
            GroupMessage.send(from_user=from_user,
                              to_group=group,
                              subject=subject,
                              content=content)
        else:   # assume 'to' is an email
            to_user = users.User(to)
            Message.send(from_user=from_user,
                         to_user=to_user,
                         subject=subject,
                         content=content)

        self.render('compose.html', {'sent': True,
                                     'subject': subject,
                                     'to': to})

    def is_valid_group(self, destination):
        """Return true if destination is a valid known group"""
        # TODO: for now we just check if this is not an email
        if '@' in destination:  # is this an email ?
            return False
        else:
            return True


class ProfilePage(BaseRequestHandler):
    def get(self):
        groups = UserProfile.for_user(users.get_current_user()).groups
        groups_text = ', '.join(groups)
        self.render('profile.html', {'groups': groups_text})

    def post(self):
        groups_text = self.request.get('groups')
        groups = [group.strip() for group in groups_text.split(',')]
        UserProfile.for_user(users.get_current_user()).update_groups(groups)
        self.render('profile.html', {'saved': True, 'groups': groups_text})


class SetupPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        Message.populate(user, 7)
        UserProfile.for_user(user).update_groups(['python'])
        self.render('home.html', {'setup': True})


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/inbox', InboxPage),
    ('/message/(.*)', MessagePage),
    ('/compose', ComposePage), 
    ('/profile', ProfilePage),
    ('/setup', SetupPage),
], debug=_DEBUG)
