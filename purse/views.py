import os
from datetime import timedelta
from .models import Account, Expense, VisitCounter, UserConfig
from .forms import SignUpForm, PasschForm, PurseForm, ExpenseForm
from hbpurse import settings
from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import get_template
from django.db.models import Sum

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
	v = VisitCounter (user = user, ip = ip, timevisit = now)
	checkin = False
	
	try:
		lastv = VisitCounter.objects.filter (user = user, ip = ip).order_by ("-timevisit")[0]
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
	purses_count  = None 		# Number of purses
	purses_active_count = None # Number of active purses

	def __init__(self):
		self.update()
		self.__users__ ()
		self.__purses_count__ ()

	def update (self):
		self.__visitor_sumarize__(self.visitor_since_days)
		self.__purses_count__()

	def __visitor_sumarize__(self, days = visitor_since_days):
		""" number of visitors since xx days
		it returns an integer.
			"""
		if type(days) is not type(int()):
			raise NotIntegerError()
		datesince = timezone.now() - timedelta (days=days)
		self.visitor_count = VisitCounter.objects.filter(timevisit__gt = datesince).count()
		self.visitor_since_days = days
		self.visitor_since = datesince

	def __users__ (self):
		self.users_number = User.objects.count()

	def __purses_count__ (self):
		self.purses_count = Account.objects.count()
		self.purses_active_count = Account.objects.filter(active = True).count()

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
	it uses defaults values
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
		os.remove (settings.BASE_DIR + expense.image.url)
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


# Create your views here.
#
##############################

def welcome (request):
	next = request.GET.get('next', '')
	if request.user.is_authenticated:
		activestatus = UserConfig.objects.get(user=request.user).showinactive
		if activestatus:
			accounts = Account.objects.filter(user = request.user)
		else:
			accounts = Account.objects.filter(user = request.user, active = True)
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
		return redirect ('purse:welcome')
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
		form = ExpenseForm(request.POST)
		if form.is_valid():
			expense = form.save (commit=False)
			expense.user = request.user
			expense.account = account
			expense.save ()
			update_account (account)

	expenses = Expense.objects.filter (account = account, exported=False).order_by ('-date', '-id')
	context = {
			'purse' 	: account,
			'expenses' 	: expenses,
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
	if request.method == "POST":
		form = ExpenseForm(request.POST, instance=expense)
		if form.is_valid():
			expense = form.save (commit=False)
			expense.save ()
			update_account (expense.account)
		return redirect ('purse:expenses', pk=expense.account.pk)
	form = ExpenseForm (instance=expense)
	context = { 'form' : form,
				'expense': expense,
			 }
	context.update (basecontext (request) )
	return render (request, 'purse/modify_expense.html', context)

def expenses_delete (request, pk):
	next = request.GET.get('next', False)
	try:
		expense = Expense.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != expense.account.user:
		return redirect ('purse:welcome')
	remove_expense (expense)
	context = {
			'title'	: 'Expense deleted',
			'msg' 	: 'The expense has been deleted',
			'next'	: next,
			}
	context.update (basecontext (request) )
	return render (request, 'purse/msgs/msgconfirm.html', context)

def makecsv (expenseslist):
	output = 'date;paymode;info;payee;wording;amount;category;tags\n'
	for e in expenseslist:
		mylist = [str(e.date), str(e.paymode), e.info, e.payee, e.wording, str(e.amount), "", e.tags]
		output += '%s\n'%(";".join(mylist))
	return output

def expenses_export(request, pk):
	try:
		purse = Account.objects.get(pk = pk)
	except:
		return redirect ('purse:welcome')
	if not request.user.is_authenticated:
		return redirect ('purse:login_user')
	if request.user != purse.user:
		return redirect ('purse:welcome')
	expenseslist = Expense.objects.filter(account = pk, exported=False)
	context = { 'expenses'	: expenseslist,
				'count'		: len (expenseslist),
				'purse'		: Account.objects.get(pk=pk),
				}
	context.update (basecontext (request) )
	if request.method == "POST":
		csvcontent = makecsv (expenseslist)
		response = HttpResponse (csvcontent, content_type='text/csv')
		response ['Content-Disposition'] = 'attachment; filename="%s.csv"'%purse.name
		for e in expenseslist:
			e.exported = True
			e.save()
		return response

	return render (request, 'purse/expenses_export.html', context)


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
				'title'	: 'Login',
				'msg' 	: 'Usuario o contraseña incorrecta.',
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
			context = { 'title'	: 'Sign up yourself',
						'msg' 	: 'User already exists.',
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
		email = request.POST ['email']
		try:
			validate_email (email)
		except :
			return HttpResponse ('Sign up with a valid e-mail: <strong>%s</strong>'%email)
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			context = {	'title'	: 'Sign up yourself',
						'msg' 	: 'Passwords does not match.',
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
								title = 		'¡Welcome to your Homebank online Purse!',
								template = 		'purse/mails/welcome_user.html',
								txtcontent = 	'%s welcome to your Homebank online Purse.'%username,
								templatecontext = {
													'domain'	:	settings.TEMPLATE_DOMAIN,
													'user'		:	user,
													'password'	:	password,
													}
								)
			return redirect ('purse:welcome')
		else:
			context = {	'title'	: 'Sign up yourself',
						'msg' 	: 'Some fields where incorrect.',
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
	form = SignUpForm
	context = {	'form': form,
				'head': "Sign up yourself",
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
			context = {	'title'	: 'Edit your data',
						'msg' 	: 'Please, set a valid e-mail',
						'back' 	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context )
		userdata.email = request.POST ['email']
		userdata.save()
		context = { 'title'	: 'Edit your data',
					'msg' 	: 'Your data has been stored',
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
		context = {	'title'	: 'Change your password',
					'msg' 	: 'Your password has changed',
					'ppal'	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context)

	form = PasschForm (instance = request.user)
	context = {	'form' : form,
				'head' : "Enter a new password"
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
			context = {	'title'	: 'Reset your password',
						'msg' 	: 'There is not user with this data',
						'back'	: True,
						}
			context.update (basecontext (request) )
			return render (request, 'purse/msgs/msgconfirm.html', context)
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		send_user_mail (	recipients = 	user.email,
							title = 		'Password restore',
							template = 		'purse/mails/password_reset.html',
							txtcontent = 	'%s, there is one little step to reset your password.'%username,
							templatecontext = {
												'domain'	:	settings.TEMPLATE_DOMAIN,
												'user'		:	user,
												'uid'		:	uid,
												'token'		:	token,
												}
							)
		context = {	'title'	: 'Password reset',
					'msg' 	: 'an e-mail has been send to reset your password',
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
			return HttpResponse ('passwords did not match')
		for user in User.objects.all():
			if default_token_generator.check_token(user, token):
				break
		user.set_password (password)
		user.save()

		login(request, user)
		context = { 'title'	: 'Set your password',
					'msg' 	: 'Your new password has been stored',
					'ppal'	: True,
					}
		context.update (basecontext (request) )
		return render (request, 'purse/msgs/msgconfirm.html', context)
	form = PasschForm ()
	context = {	'form' : form,
				'head' : "Set your new password"
				}
	context.update (basecontext (request) )
	return render (request, 'purse/singup.html', context)
		
