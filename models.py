from google.appengine.api import users
from google.appengine.ext import ndb



class UserClient(ndb.Model):
	user = ndb.UserProperty(required=True)
	client_id = ndb.StringProperty()

class GameConnection(ndb.Model):
    author = ndb.UserProperty(auto_current_user_add=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    channel_key = ndb.StringProperty()
    users = ndb.StructuredProperty(UserClient, repeated=True)
    