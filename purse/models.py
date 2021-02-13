from django.db import models
from django.contrib.auth.models import User
from os.path import join

# Create your models here.
MYAPPBASE_DIR = 'purse'

class Account (models.Model):
	""" Account, an user can have one or more accounts.
	a expense must have an account
	When there is a new user, a default account is oppened
		"""
	colorchoices = [
		('#FAEBD7','AntiqueWhite'),
		('#7FFFD4','Aquamarine'),
		('#DEB887','BurlyWood'),
		('#FF7F50','Coral'),
		('#FF8C00','DarkOrange'),
		('#FFD700','Gold'),

		]

	user 	= models.ForeignKey ('auth.User', on_delete=models.CASCADE)		# related User object
	name	= models.TextField ('Name', max_length=20, null=False, blank=False)		# Name it
	color	= models.TextField ('color', choices=colorchoices, default="#FFD700")	# background color (default Gold)
	adjustment = models.DecimalField (max_digits=6, decimal_places=2)		# starting amount of the account / adjust your real money
	active = models.BooleanField ('Active', default=True)					# Activate or deactivate the account

class Expense (models.Model):
	""" List of expenses:

	UserFields:
		user
		account
		exported
	Homebank CSV fields:
		date
		paymode
		info
		payee
		wording
		amount
		category
		tags
	Extra info fields
		image
		currency
		"""
	paymodechoice = [
		(3,'Cash'),
		]

	user 	= models.ForeignKey ('auth.User', on_delete=models.CASCADE)
	account	= models.ForeignKey ('Account', on_delete=models.CASCADE, blank=False, null=False)
	exported = models.BooleanField ('exported', default=False)
	date 	= models.DateField ('Date', auto_now_add=True, null=False)
	paymode = models.PositiveIntegerField ('paymode', choices=paymodechoice, default=3)
	info	= models.TextField ('info', max_length=15, default="")
	payee	= models.TextField ('payee', max_length=20, default="")
	wording	= models.TextField ('wording', max_length=200, default="")
	amount	= models.DecimalField (max_digits=6, decimal_places=2)
	tags	= models.TextField ('tags', max_length=20, default="")
	image	= models.ImageField ('image', blank=True, upload_to=join(MYAPPBASE_DIR,'images'))
	currency= models.TextField ('currency', blank=True, default="€", max_length=8)

class VisitCounter (models.Model):
	""" Store visitors counter	"""
	user		= models.TextField ('user', max_length=150)
	ip			= models.TextField ('ip', max_length=50, null= True)
	timevisit	= models.DateTimeField ('Fecha', auto_now_add=True, null=True)

	def __str__(self):
		return self.user + ":" + self.ip

