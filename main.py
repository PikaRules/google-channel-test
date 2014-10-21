import jinja2
import os
import sys
import webapp2
from google.appengine.api import channel
from google.appengine.api import users
import logging
from models import *
import json


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)


"""
-------------- APP -----------------------------------
"""


class GameUpdater():

	def __init__(self, channel_key = '' ):
		self.channel_key = channel_key

	def new_user(self,message,channel_key=''):
		if channel_key == '':
			channel_key = self.channel_key
		channel.send_message(channel_key,json.dumps(message))


class GameSession():

	def create_new_game_connection(self, channel_key):
		game_connection = GameConnection(channel_key=channel_key)
		key = game_connection.put()
		self.game_connection_key = key
		return game_connection

	def restore_game_connection(self, channel_key):
		results = GameConnection.query(GameConnection.channel_key==channel_key).order(-GameConnection.date).fetch(1)
		self.game_connection_key = results[0].key
		return results[0]

	def add_user_client(self,user,client_id=''):
		if self.game_connection_key is not None:
			if client_id == '':
				client_id = os.urandom(16).encode('hex')
			client = UserClient(user=user, client_id=client_id)
			game_connection = self.game_connection_key.get()
			game_connection.users.append(client)
			game_connection.put()
		else:
			logging.warning('there is not game_session_key')

	def is_user_in_game_session(self,user):
		game_connection = self.game_connection_key.get()
		session_users = game_connection.users
		for client in session_users:
			if client.user.email == user.email:
				return True
		return False




"""
 ----------------  REQUEST HANDLERS  ---------------------------------
"""



class MainPage(webapp2.RequestHandler):


	def __init__(self, *args, **kwargs):
		super(MainPage, self).__init__(*args, **kwargs)
		self.game_session = GameSession()
		#self.router.set_dispatcher(self.__class__.custom_dispatcher)

	def get(self):
		try:

			current_user = users.get_current_user()
			client_id = os.urandom(16).encode('hex')
			channel_key = channel.create_channel(current_user.user_id() + client_id)
			game_updater = GameUpdater(channel_key)

			#check if game connection exists
			if 'channel_key' in self.request.GET:
				channel_key = self.request.GET.get('channel_key')
				self.game_session.restore_game_connection(channel_key)
				if not self.game_session.is_user_in_game_session(current_user):
					self.game_session.add_user_client(current_user,client_id)
					message = {
						'key': 'new_user',
						'data':{
							'email': current_user.email()
						}
					}
					game_updater.new_user(message, channel_key)
			else:
				#create game session
				self.game_session.create_new_game_connection(channel_key)
				self.game_session.add_user_client(current_user,client_id)
				message = {
						'key': 'new_user',
						'data':{
							'email': current_user.email()
						}
					}
				game_updater.new_user(message, channel_key)


			#get users in the game channel
			conecction_users = self.game_session.game_connection_key.get().users

			logging.warning(conecction_users)

			template_values = {
				'client_id': client_id,
				'channel_key': channel_key,
				'user': current_user.email(),
				'users': conecction_users
			}

			logging.warning(template_values)

			template = JINJA_ENVIRONMENT.get_template('main.html')
			result = template.render(template_values)
			self.response.write(result)
		except Exception, e:
			#self.show_error_page(e_d)
			raise

	def show_error_page(self, error):
			template_values = {
				'error': str(error)
			}
			template = JINJA_ENVIRONMENT.get_template('error.html')
			result = template.render(template_values)
			self.response.write(result)




app = webapp2.WSGIApplication([
	('/', MainPage),
], debug=True)