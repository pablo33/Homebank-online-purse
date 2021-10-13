import os
from random import randint
from PIL import Image
from decimal import Decimal

from hbpurse import settings
from purse import preferences as pref

from django.db.models import Sum
from django.db import models
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

	def resetto (self, resetto):
		self.adjustment = Decimal(resetto) - (Decimal(self.cuantity) - Decimal(self.adjustment))
		self.save()

	def update_account (self):
		total = (Expense.objects.filter(account=self).aggregate(Sum('amount')))
		sumexpenses = 0
		if total ['amount__sum'] != None:
			sumexpenses = "%.2f"%total ['amount__sum']
		self.cuantity = Decimal(sumexpenses) + Decimal(self.adjustment)
		self.save()

	def purgepurse (self):
		""" Cleans old exported expenses. pk=purse number
			"""
		exported = Expense.objects.filter(account=self ,exported=True).order_by('-date', '-id')
		remain = pref.expenses_purge_exported
		if len (exported) > remain:
			index = 0
			adjustment = 0
			for expense in exported:
				index += 1
				if index > remain:
					adjustment = adjustment + expense.amount
					expense.remove_expense()
			self.adjustment = self.adjustment + adjustment
			self.save()

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
	image	= models.ImageField (blank=True, upload_to=os.path.join(MYAPPBASE_DIR,'expenses'))

	def __str__(self):
		return self.wording
	
	def normalize_image (self):
		def itemcheck(pointer):
			""" returns what kind of a pointer is """
			if not (type(pointer) is str or type(pointer) is unicode):
				raise NotStringError ('Bad input, it must be a string')
			if pointer.find("//") != -1 :
				raise MalformedPathError ('Malformed Path, it has double slashes')
			
			if os.path.isfile(pointer):
				return 'file'
			if os.path.isdir(pointer):
				return 'folder'
			if os.path.islink(pointer):
				return 'link'
			return ""

		def autorotate (imagepath):
			"""
			It will rotate a image if it has an exif orientation data
			Returns True if image is rotated, otherway it return False
			It opens and writes the image file in case it is rotated
			"""
			img = Image.open(imagepath)
			exif = img._getexif()
			if exif == None:
				return False

			orientation_key = 274 # cf ExifTags
			if orientation_key in exif:
				orientation = exif[orientation_key]
				rotate_values = {
					3: Image.ROTATE_180,
					6: Image.ROTATE_270,
					8: Image.ROTATE_90,
				}
				if orientation in rotate_values:
					# Rotate and save the picture
					img = img.transpose(rotate_values[orientation])
					img.save(imagepath)
					return True
			return False

		def resize_image (imagepath, max_size):
			""" Resize an imagefile to a maximum of pixels, width or height.
			It will save the file as jpg and RGB colors
			It will delete oldimage is it is hasn't a jpg as file extension.
			It returns None if there is no conversion
			It returns the (new or entered) imagepath if a conversion is done
				"""
			img = Image.open (imagepath)
			if img.width < max_size and img.height < max_size:
				# Image is smaller than max_size, factor is 1
				factor = 1
			elif img.width > img.height:
				factor = img.width / max_size
			else:
				factor = img.height / max_size
			width = int(img.width // factor)
			height = int(img.height // factor)
			if abs (width - max_size) == 1:
				width = max_size
				height += 1
			if abs (height - max_size) == 1:
				height = max_size
				width += 1
			img = img.resize (( width, height ))
			img.mode = 'RGB'
			newimagepath = os.path.splitext(imagepath)[0] + '.jpg'
			img.save(newimagepath)
			if imagepath != newimagepath and itemcheck (imagepath) == 'file':
				os.remove (imagepath)
			return newimagepath

		def rename_image (imagepath, pk):
			extension = os.path.splitext (imagepath)[1]
			newimagepath = os.path.join( os.path.dirname(imagepath), str(pk) + extension)
			return newimagepath

		if self.image:
			imagepath = settings.BASE_DIR + self.image.url 	#Existent file now is "imagepath"
			autorotate (imagepath)
			newimagepath1 = resize_image (imagepath, 800)		#Existent file now is "imagepath1"
			newimagepath = rename_image (newimagepath1, str(self.pk) + str(randint(0, 999999)).zfill(6))	#file has been renamed to "newimagepath"
			if newimagepath != imagepath:
				self.image = newimagepath [len(settings.MEDIA_ROOT)+1:]
				os.rename (newimagepath1, newimagepath)
				self.save()

	def delete_media (self):
		if os.path.isfile (self.image.path):
			os.remove (self.image.path)

	def remove_expense (self):
		if self.image != "":
			self.delete_media()
		self.delete()

	def cleanmyfile (self, oldimage):
		""" Checks old image filename and deletes it if it is needed
			"""
		if oldimage != "":
			if self.image == "":
				if os.path.isfile (oldimage):
					os.remove (oldimage)
			elif oldimage != self.image.path:
					if os.path.isfile (oldimage):
						os.remove (oldimage)

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
