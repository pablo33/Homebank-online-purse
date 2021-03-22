from django.db import models
from django.contrib.auth.models import User
from os.path import join
from django.utils.translation import gettext_lazy as _

# Create your models here.
MYAPPBASE_DIR = 'purse'

class Account (models.Model):
	""" Account, an user can have one or more accounts.
	a expense must have an account
	When there is a new user, a default account is oppened
		"""
	colorchoices = [
		('backg01','AntiqueWhite'),
		('backg02','Aquamarine'),
		('backg03','BurlyWood'),
		('backg04','Coral'),
		('backg05','DarkOrange'),
		('backg06','Gold'),
		]

	user 	= models.ForeignKey ('auth.User', on_delete=models.CASCADE, blank=False, null=False)		# related User object
	name	= models.CharField (max_length=40, null=False, blank=False, default=_('my purse'), help_text=_('Purse/wallet name'))		# Name it
	color	= models.CharField (max_length=7, choices=colorchoices, default="#FFD700")	# background color (default Gold)
	adjustment = models.DecimalField (max_digits=6, decimal_places=2, default=0)		# starting amount of the account / adjust your real money
	active = models.BooleanField (default=True)					# Activate or deactivate the account
	cuantity = models.DecimalField (max_digits=6, decimal_places=2, default=0)		# Cuantity for this account
	currency= models.CharField (max_length=8, blank=True, default="€")
	showexported=models.BooleanField (default=False)

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
	exported = models.BooleanField (default=False)
	date 	= models.DateField (null=False, blank=False)
	paymode = models.PositiveIntegerField (choices=paymodechoice, default=3)
	info	= models.CharField (max_length=15, default="", blank=True)
	payee	= models.CharField (max_length=20, default="", blank=True)
	wording	= models.CharField (max_length=200, default="")
	amount	= models.DecimalField (max_digits=6, decimal_places=2)
	tags	= models.CharField (max_length=20, default="", blank=True)
	image	= models.ImageField (blank=True, upload_to=join(MYAPPBASE_DIR,'expenses'))

	def __str__(self):
		return self.wording


class VisitCounter (models.Model):
	""" Store visitors counter	"""
	user		= models.CharField (max_length=150)
	ip			= models.CharField (max_length=50, null= True)
	timevisit	= models.DateTimeField (auto_now_add=True, null=True)
	app			= models.CharField (max_length=50, blank=True, null=True)

	def __str__(self):
		return self.user + ":" + self.ip

class UserConfig (models.Model):
	""" User configuration """
	user 	= models.ForeignKey ('auth.User', on_delete=models.CASCADE)
	showinactive = models.BooleanField ('Show inactive', default=False, help_text=_('Activate to show inactive purses/wallets'))

	def __str__ (self):
		return str(self.user)
