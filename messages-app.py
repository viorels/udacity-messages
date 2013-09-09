import cgi
import logging
import os
import webapp2
from google.appengine.api import users
from google.appengine.ext.webapp import template

from models import Message

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True


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
            'logout_url': users.create_logout_url(self.request.uri),
            'application_name': 'Udacity messages',
        }
        values.update(template_values)
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', template_name))
        self.response.out.write(template.render(path, values, debug=_DEBUG))


class MainPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.render('base.html')
        else:
            self.redirect(users.create_login_url(self.request.uri))


class MessagesPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.headers['Content-Type'] = 'text/html'
        text = 'Hello, %s<br>' % user.nickname()
        self.response.write(text)

        for message in Message.list_for_user(user):
            message_info = "%s (%s)" % (message.subject, message.from_user)
            self.response.write(cgi.escape(message_info) + '<br>')


class ComposePage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        self.render('compose.html')

    def post(self):
        to_user = self.request.get('to')
        subject = self.request.get('subject')
        content = self.request.get('content')
        Message.send(from_user=users.get_current_user().email(),
                     to_user=to_user,
                     subject=subject,
                     content=content)
        self.render('compose.html', {'done': True})


class InitPage(BaseRequestHandler):
    def get(self):
        Message.populate(users.get_current_user().email())
        self.response.write('ok')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/messages', MessagesPage),
    ('/init', InitPage),
], debug=_DEBUG)
