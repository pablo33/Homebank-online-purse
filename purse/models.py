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

	user 	= models.ForeignKey ('auth.User', on_delete=models.CASCADE, blank=False, null=False)		# related User object
	name	= models.CharField ('Name', max_length=40, null=False, blank=False, default='my purse')		# Name it
	color	= models.CharField ('color', max_length=7, choices=colorchoices, default="#FFD700")	# background color (default Gold)
	adjustment = models.DecimalField (max_digits=6, decimal_places=2, default=0)		# starting amount of the account / adjust your real money
	active = models.BooleanField ('Active', default=True)					# Activate or deactivate the account
	cuantity = models.DecimalField (max_digits=6, decimal_places=2, default=0)		# Cuantity for this account

	def __str__ (self):
		return self.name

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
	info	= models.CharField ('info', max_length=15, default="")
	payee	= models.CharField ('payee', max_length=20, default="")
	wording	= models.CharField ('wording', max_length=200, default="")
	amount	= models.DecimalField (max_digits=6, decimal_places=2)
	tags	= models.CharField ('tags', max_length=20, default="")
	image	= models.ImageField ('image', blank=True, upload_to=join(MYAPPBASE_DIR,'images'))
	currency= models.CharField ('currency', max_length=8, blank=True, default="€")

class VisitCounter (models.Model):
	""" Store visitors counter	"""
	user		= models.CharField ('user', max_length=150)
	ip			= models.CharField ('ip', max_length=50, null= True)
	timevisit	= models.DateTimeField ('Fecha', auto_now_add=True, null=True)

	def __str__(self):
		return self.user + ":" + self.ip

