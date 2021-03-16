import os, re
from PIL import Image
from datetime import timedelta
from .models import Account, Expense, VisitCounter, UserConfig
from .forms import SignUpForm, PasschForm, PurseForm, ExpenseForm
from hbpurse import settings
from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import get_template
from django.db.models import Sum, Count

# ------------------------ Utils --------------------------------------------

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

def Nextfilenumber (dest):
	''' Returns the next filename counter as filename(nnn).ext
	input: /path/to/filename.ext
	output: /path/to/filename(n).ext
		'''
	if dest == "":
		raise EmptyStringError ('empty strings as input are not allowed')
	filename = os.path.basename (dest)
	extension = os.path.splitext (dest)[1]
	# extract secuence
	expr = '\(\d{1,}\)'+extension
	mo = re.search (expr, filename)
	try:
		grupo = mo.group()
	except:
		#  print ("No final counter expression was found in %s. Counter is set to 0" % dest)
		counter = 0
		cut = len (extension)
	else:
		#  print ("Filename has a final counter expression.  (n).extension ")
		cut = len (mo.group())
		countergroup = (re.search ('\d{1,}', grupo))
		counter = int (countergroup.group()) + 1
	if cut == 0 :
		newfilename = os.path.join( os.path.dirname(dest), filename + "(" + str(counter) + ")" + extension)
	else:
		newfilename = os.path.join( os.path.dirname(dest), filename [0:-cut] + "(" + str(counter) + ")" + extension)
	return newfilename

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def add_visitor (request):
	ip = get_client_ip (request)
	user = request.user
	now = timezone.now()
	v = VisitCounter (user = user, ip = ip, timevisit = now, app='purse')
	checkin = False
	
	try:
		lastv = VisitCounter.objects.filter (user = user, ip = ip, app='purse').order_by ("-timevisit")[0]
		if now - lastv.timevisit > timedelta (minutes = 60):
			checkin = True # is a returning visitor from the same IP
	except:
		checkin = True # It's a new new visitor
	if checkin:
		v.save ()
	return

class Statistics:
	"""Statistics for database """
	visitor_since_days = 30		# counts the number of visits since las xx days
	visitor_count = None		# visitors counter, a calculated field
	visitor_since = None 		# visitors counted since this time. It's a datetime object, calculated
	users_number  = None 		# Number of users at database
	users_active  = None 		# Active users since "visitor_since_days"
	purses_count  = None 		# Number of purses
	purses_active_count = None # Number of active purses

	def __init__(self):
		self.update()

	def update (self):
		self.__visitor_sumarize__(self.visitor_since_days)
		self.__purses_count__()
		self.__users__ ()

	def __visitor_sumarize__(self, days = visitor_since_days):
		""" number of visitors since xx days
		it returns an integer.
			"""
		if type(days) is not type(int()):
			raise NotIntegerError()
		datesince = timezone.now() - timedelta (days=days)
		self.visitor_count = VisitCounter.objects.filter(timevisit__gt = datesince, app='purse').count()
		self.visitor_since_days = days
		self.visitor_since = datesince
		q = VisitCounter.objects.filter(timevisit__gt = datesince, app='purse').exclude(user = 'AnonymousUser').aggregate(Count('user', distinct=True))
		self.users_active = q['user__count']

	def __purses_count__ (self):
		self.purses_count = Account.objects.count()
		self.purses_active_count = Account.objects.filter(active = True).count()

	def __users__ (self):
		self.users_number = User.objects.count()


STnumbers = Statistics()


def send_user_mail(recipients, title, template, templatecontext, txtcontent = ''):
	""" Sends e-mail based on an django template
		"""
	template = get_template(template)
	htmlcontent = template.render(templatecontext)

	send_mail (	title,						#Título
				txtcontent,					#Text content only
    			settings.EMAIL_HOST_USER, 	#Remitente
    			[recipients], 				#Destinatario
    			html_message = htmlcontent,	#html content
    			)

def create_purse (user):
	""" Create a new empty purses
	it uses defaults values from models
		"""
	Purse = Account (user = user)
	Purse.save()

def adduserdefaults (user):
	""" Set default configuration """
	try:
		config = UserConfig.objects.GET(user = user)
	except:
		config = UserConfig (user = user)
	config.showinactive = False
	config.save()

def update_account (account):
	total = (Expense.objects.filter(account=account).aggregate(Sum('amount')))
	sumexpenses = 0
	if total ['amount__sum'] != None:
		sumexpenses = "%.2f"%total ['amount__sum']
	account.cuantity = float( sumexpenses ) + float(account.adjustment)
	account.save()

def remove_expense (expense):
	if expense.image != "":
		delete_media (expense.image.url)
	expense.delete()
	return

def basecontext (request):
	""" Refresh user session pannels. It takes the last data at DB.
		"""
	add_visitor (request)
	STnumbers.update()
	return {
			'statistics'		:	STnumbers,
			}

def cleanmyfile (oldimage,imgfield ):
	""" Checks new image filename and deletes oldimage
		"""
	targetfile = settings.BASE_DIR + oldimage
	if oldimage != "":
		if imgfield == "":
			if itemcheck (targetfile) == 'file':
				os.remove (targetfile)
			return True
		else:
			if (os.path.basename(oldimage) != os.path.basename(imgfield.url)) or os.path.basename(imgfield.url).startswith(oldimage):
				delete_media (oldimage)
				##if itemcheck (targetfile) == 'file':
				##	os.remove (settings.BASE_DIR + oldimage)
				return True
	return False

def resize_image (imagepath, max_size):
	""" Resize an imagefile to a maximus of pixels, width or height.
	None of their sizes will pass the max_size
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
	#if itemcheck (newimagepath) == 'file':
	#	newimagepath = Nextfilenumber (newimagepath)
	img.save(newimagepath)
	if imagepath != newimagepath and itemcheck (imagepath) == 'file':
		os.remove (imagepath)
	return newimagepath

def rename_image (imagepath, pk):
	filename = os.path.basename (imagepath)
	extension = os.path.splitext (imagepath)[1]
	newimagepath = os.path.join( os.path.dirname(imagepath), str(pk) + extension)
	return newimagepath

def normalize_image (expense):
	if expense.image:
		imagepath = settings.BASE_DIR + expense.image.url 	#Existent file now is "imagepath"
		newimagepath1 = resize_image (imagepath, 800)		#Existent file now is "imagepath1"
		newimagepath = rename_image (newimagepath1, expense.pk)	#file has been renamed to "newimagepath"
		if newimagepath != imagepath:
			expense.image = newimagepath [len(settings.MEDIA_ROOT)+1:]
			os.rename (newimagepath1, newimagepath)
			expense.save()
			return True
	return None

def delete_media (projectpath):
	filepath = settings.BASE_DIR + projectpath
	if itemcheck (filepath) == 'file':
		os.remove (filepath)
	return True

def makecsv (expenseslist):
	output = 'date;paymode;info;payee;wording;amount;category;tags\n'
	for e in expenseslist:
		mylist = [str(e.date), str(e.paymode), e.info.replace(";",","), e.payee.replace(";",","), e.wording.replace(";",","), str(e.amount), "", e.tags.replace(";",",")]
		output += '%s\n'%(";".join(mylist))
	return output

def purgepurse (purse):
	""" Cleans old exported expenses. 
		"""
	topurge = purse.objects.filter(exported=True)
	pass

# ----------------------------------------------------------------------------

# Your views here.
#
##############################

def welcome (request):
	next = request.GET.get('next', '')
	if request.user.is_authenticated:
		try:
			activestatus = UserConfig.objects.get(user=request.user).showinactive
		except:
			create_purse (request.user)
			adduserdefaults (request.user)
			activestatus = UserConfig.objects.get(user=request.user).showinactive
		if activestatus:
			accounts = Account.objects.filter(user = request.user).order_by('-active')
		else:
			accounts = Account.objects.filter(user = request.user, active = True).order_by('-active')
		if len (accounts) > 1 or next == 'purses':		
			context = {
						'purses' : accounts,
			}
			context.update (basecontext (request) )
			return render (request, 'purse/purses.html', context) # list of purses
		elif len (accounts) == 1:
			return redirect ('purse:expenses', pk=accounts[0].pk ) # go directly to unique active purse
	context = {}
	context.update (basecontext (request) )
	return render(request, 'purse/welcome.html', context )  # go to welcome page

def new_purse (request):
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.method == "POST":
		form = PurseForm(request.POST)
		if form.is_valid():
			newaccount = form.save (commit = False)
			newaccount.user = request.user
			newaccount.cuantity = newaccount.adjustment
			newaccount.save()
		return redirect ('purse:welcome') 

	context = { 'form' : PurseForm }
	context.update (basecontext (request) )
	return render (request, 'purse/new_purse.html', context)

def modify_purse (request, pk):
	try:
		account = Account.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != account.user:
		return redirect ('purse:welcome')
	if request.method == "POST":
		form = PurseForm(request.POST, instance=account)
		if form.is_valid():
			account = form.save (commit=False)
			account.user = request.user
			account.save ()
			update_account (account)
		return redirect ('purse:expenses', pk=pk)
	form = PurseForm (instance=account)
	context = { 'form' : form,
				'purse': account,
			 }
	context.update (basecontext (request) )
	return render (request, 'purse/modify_purse.html', context)

def expenses_purse(request, pk):
	try:
		account = Account.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != account.user:
		return redirect ('purse:welcome')
	if request.method == 'POST':
		try:
			request.POST ['positive']
			positive = True
		except:
			positive = False
		form = ExpenseForm(request.POST, request.FILES)
		if form.is_valid():
			expense = form.save (commit=False)
			expense.user = request.user
			expense.account = account
			expense.amount = -abs(expense.amount)
			if positive:
				expense.amount = -expense.amount
			expense.save ()
			normalize_image (expense)
			update_account (account)

	expenses = Expense.objects.filter (account = account).order_by ('-date', '-id')
	context = {
			'purse' 	: account,
			'expenses' 	: expenses,
			'count'		: len (expenses),
			'form'		: ExpenseForm,
			}
	context.update (basecontext (request) )
	return render (request, 'purse/expenses_add.html', context)

def expenses_modify (request, pk):
	try:
		expense = Expense.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != expense.account.user:
		return redirect ('purse:welcome')
	oldimage = ""
	if expense.image != "":
		oldimage = expense.image.url[:] # make a hardcopy of actual value	
	if request.method == "POST":
		try:
			request.POST ['positive']
			positive = True
		except:
			positive = False
		form = ExpenseForm(request.POST, request.FILES, instance=expense)
		if form.is_valid():
			expense = form.save (commit=False)
			cleanmyfile (oldimage,expense.image)
			expense.amount = -abs(expense.amount)
			if positive:
				expense.amount = -expense.amount
			expense.save ()
			normalize_image (expense)
			update_account (expense.account)
		return redirect ('purse:expenses', pk=expense.account.pk)
	form = ExpenseForm (instance=expense)
	context = { 'form' : form,
				'expense': expense,
			 }
	context.update (basecontext (request) )
	return render (request, 'purse/modify_expense.html', context)

def expenses_delete (request, pk):
	try:
		expense = Expense.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != expense.account.user:
		return redirect ('purse:welcome')
	if request.method == 'POST':
		remove_expense (expense)
		update_account (expense.account)
		#if expense.image != "":
		#	os.remove (settings.BASE_DIR + expense.image.url)
		return redirect ('purse:expenses', pk=expense.account.pk)
	context = {
			'expense'	: expense,
			}
	context.update (basecontext (request) )
	return render (request, 'purse/expenses_delete.html', context)

def expenses_export(request, pk):
	try:
		purse = Account.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != purse.user:
		return redirect ('purse:welcome')
	expenseslist = Expense.objects.filter(account = pk, exported=False).order_by ('-date', '-id')
	context = { 'expenses'	: expenseslist,
				'count'		: len (expenseslist),
				'purse'		: purse,
				}
	context.update (basecontext (request) )
	if request.method == "POST":
		csvcontent = makecsv (expenseslist)
		response = HttpResponse (csvcontent, content_type='text/csv')
		response ['Content-Disposition'] = 'attachment; filename="%s.csv"'%purse.name
		purgepurse (purse)
		return response
	return render (request, 'purse/expenses_export.html', context)

def mark_exported (request, pk):
	try:
		purse = Account.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != purse.user:
		return redirect ('purse:welcome')
	expenseslist = Expense.objects.filter(account = pk, exported=False)
	for e in expenseslist:
		e.exported = True
		e.save()
	return redirect ('purse:expenses', pk=pk)


def expenses_image (request, pk):
	try:
		expense = Expense.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != expense.user:
		return redirect ('purse:welcome')
	if request.method == "POST":
		delete_media (expense.image.url)
		expense.image = None
		expense.save()
		return redirect ('purse:expenses', pk=expense.account.pk)
	context = {	'expense' : expense,}
	context.update (basecontext (request) )
	return render (request, 'purse/showimage.html', context)

def login_user (request):
	next = request.GET.get('next', '')
	if request.method == "POST":
		username = request.POST ['user']
		password = request.POST ['password']
		next     = request.POST ['next']
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)

			if next == '':
				return redirect ('purse:welcome')
			else:
				return redirect (next)
		else:
			context = {
				'title'	: _('Login'),
				'msg' 	: _('User or password incorrect.'),
				'back' 	: True,
				}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)

	else:
		user, password = ("","")
		if request.user.is_authenticated:
			user = request.user
			password = request.user.password
		context = {
			'user' 		: user,
			'password' 	: password,
			'next' 		: next,
			}
		context.update (basecontext (request) )
		return render (request, 'purse/login.html', context )

def logout_user (request):
	if request.user.is_authenticated:
		logout (request)
	return redirect ('purse:welcome')

def SignUpView (request):
	if request.user.is_authenticated:
		logout (request)
	if request.method == "POST":
		form = SignUpForm(request.POST)
		username = request.POST ['username']
		if len (User.objects.filter (username=username)) >= 1:
			context = { 'title'	: _('Sign up yourself'),
						'msg' 	: _('User already exists.'),
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
		email = request.POST ['email']
		try:
			validate_email (email)
		except :
			return HttpResponse (_('Sign up with a valid e-mail:%(email)s)') % {'email':email})
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			context = {	'title'	: _('Sign up yourself'),
						'msg' 	: _('Passwords does not match.'),
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)

		if form.is_valid():
			newuser = form.save(commit=False)
			newuser.save ()
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
			create_purse (user)
			adduserdefaults (user)
			send_user_mail (	recipients = 	email,
								title = 		_('¡Welcome to your Homebank online Purse!'),
								template = 		'purse/mails/welcome_user.html',
								txtcontent = 	_('%(username)s welcome to your Homebank online Purse.')% {'username': username},
								templatecontext = {
													'domain'	:	settings.TEMPLATE_DOMAIN,
													'user'		:	user,
													'password'	:	password,
													}
								)
			return redirect ('purse:welcome')
		else:
			context = {	'title'	: _('Sign up yourself'),
						'msg' 	: _('Some fields where incorrect.'),
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
	form = SignUpForm
	context = {	'form': form,
				'head': _('Sign up yourself'),
				}
	context.update (basecontext (request) )
	return render (request, 'purse/singup.html', context)

def editdata_user (request, pk):
	try:
		userweb = User.objects.get(pk = pk)
	except:
		# requested user does not exist
		return redirect ('purse:welcome')
	if request.user != userweb:
		# requested user and logged user is not the same
		return redirect ('purse:welcome')
	if request.method == "POST":
		try:
			request.POST ['showinactive']
			showinactive = True
		except:
			showinactive = False
		try:
			userconfig = UserConfig.objects.get(user=request.user)
			userconfig.showinactive = showinactive
			userconfig.save()
		except:
			userconfig = UserConfig.objects.create (user = request.user, showinactive = showinactive)
		
		userdata = User.objects.get (pk = pk)
		userdata.first_name = request.POST ['first_name']
		userdata.last_name	= request.POST ['last_name']
		email = request.POST ['email']
		try:
			validate_email (email)
		except:
			context = {	'title'	: _('Edit your data'),
						'msg' 	: _('Please, set a valid e-mail'),
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context )
		userdata.email = request.POST ['email']
		userdata.save()
		context = { 'title'	: _('Edit your data'),
					'msg' 	: _('Your data has been stored'),
					'ppal'	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context ) 
	context = {	'user'				: 	request.user,
				'userconfig'		: 	UserConfig.objects.get(user=request.user),
			}
	context.update (basecontext (request) )
	return render (request, 'purse/editdata_user.html', context)

def changepass_user (request, pk):
	try:
		userweb = User.objects.get(pk = pk)
	except:
		# requested user does not exist
		return redirect ('purse:welcome')
	if request.user != userweb:
		# requested user and logged user is not the same
		return redirect ('purse:welcome')
	if request.method == "POST":
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return HttpResponse ('Passwords do not match.')
		user = User.objects.get(username = request.user)
		user.set_password (password)
		user.save()
		login(request, user)
		context = {	'title'	: _('Change your password'),
					'msg' 	: _('Your password has changed'),
					'ppal'	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context)

	form = PasschForm (instance = request.user)
	context = {	'form' : form,
				'head' : _('Enter a new password'),
				}
	context.update (basecontext (request) )
	return render (request, 'purse/singup.html', context)

def resetmypassw (request):
	if request.method == "POST":
		username = request.POST ['username']
		email = request.POST ['email']
		try:
			validate_email (email)
		except:
			return HttpResponse ('Please, set a valid e-mail: <strong>%s</strong>'%email)
		try:
			user = User.objects.get(email = email, username = username)
		except:
			context = {	'title'	: _('Reset your password'),
						'msg' 	: _('There is not user with this data'),
						'back'	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		send_user_mail (	recipients = 	user.email,
							title = 		_('Password restore'),
							template = 		'purse/mails/password_reset.html',
							txtcontent = 	_('%(username)s, there is one little step to reset your password.')%{'username', username},
							templatecontext = {
												'domain'	:	settings.TEMPLATE_DOMAIN,
												'user'		:	user,
												'uid'		:	uid,
												'token'		:	token,
												}
							)
		context = {	'title'	: _('Password reset'),
					'msg' 	: _('an e-mail has been send to reset your password'),
					'ppal' 	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context)
	context = {}
	context.update (basecontext (request) )
	return render (request, 'purse/remembermypassword_user.html', context )

def resetconfirm (request, uidb64, token):
	if request.method == "POST":
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return HttpResponse (_('passwords did not match'))
		for user in User.objects.all():
			if default_token_generator.check_token(user, token):
				break
		user.set_password (password)
		user.save()

		login(request, user)
		context = { 'title'	: _('Set your password'),
					'msg' 	: _('Your new password has been stored'),
					'ppal'	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context)
	form = PasschForm ()
	context = {	'form' : form,
				'head' : _('Set your new password')
				}
	context.update (basecontext (request) )
	return render (request, 'purse/singup.html', context)
