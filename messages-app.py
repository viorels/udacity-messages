import cgi
import logging
import os
import webapp2
import jinja2
from google.appengine.api import users

from models import Message

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

app_path = os.path.dirname(__file__)
templates_path = os.path.join(app_path, 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
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
            'logout_url': users.create_logout_url(self.request.uri),
            'application_name': 'Udacity Messages',
        }
        values.update(template_values)
        template = JINJA_ENVIRONMENT.get_template(template_name)
        self.response.out.write(template.render(values))


class MainPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.render('home.html')
        else:
            self.redirect(users.create_login_url(self.request.uri))


class InboxPage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        self.render("inbox.html", {'messages': Message.list_for_user(user.email())})


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
    ('/inbox', InboxPage),
    ('/compose', ComposePage),
    ('/init', InitPage),
], debug=_DEBUG)
