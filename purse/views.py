from .models import Account, Expense, VisitCounter, UserConfig, Statistics
from .forms import SignUpForm, PasschForm, PurseForm, ExpenseForm

from decimal import Decimal
from datetime import timedelta

from hbpurse import settings
from purse import preferences as pref

from django.shortcuts import HttpResponse, render,redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.translation import gettext as _
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import get_template
from django.urls import reverse


# __@@ Decorators @@__

def need_login(fx):
	def decorator (*args, **kw_args):
		request = args[0]
		if request.user.is_authenticated:
			return fx(*args, **kw_args)
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	return decorator

def need_group(fx):
	def decorator (*args, **kw_args):
		request = args[0]
		if request.user.groups.filter(name=pref.app_auser_group).exists():
			return fx(*args, **kw_args)
		return HttpResponse ("Need permission to use the app, please contact to the administrator.")
		#return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	return decorator

def force_logout(fx):
	def decorator (*args, **kw_args):
		request = args[0]
		if request.user.is_authenticated:
			logout (request)
		return fx(*args, **kw_args) 
	return decorator

def add_visitor(fx):
	app = 'purse'
	def get_client_ip(request):
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[-1].strip()
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip

	def decorator (*args, **kw_args):
		request = args[0]
		ip = get_client_ip (request)
		user = request.user
		now = timezone.now()
		v = VisitCounter (user = user, ip = ip, timevisit = now, app=app)
		lastminutes = now - timedelta (minutes = 60)

		lastvisits = VisitCounter.objects.filter (ip = ip, app=app, timevisit__gt=lastminutes)
		if lastvisits.count() > 0:
			if not user.is_authenticated:
				if lastvisits.filter(user = 'AnonymousUser').count() > 1:
					lastvisits.filter(user = 'AnonymousUser').delete()
				return fx(*args, **kw_args)
			else:	
				lastvisits.filter(user = user).delete()
				lastvisits.filter(user = 'AnonymousUser').delete()
		v.save ()
		return fx(*args, **kw_args)
	return decorator

def need_staff(fx):
	def decorator (*args, **kw_args):
		request = args[0]
		if request.user.is_staff:
			return fx(*args, **kw_args)
		logout (request)
		return redirect (request.path)
	return decorator

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

def makecsv (expenseslist):
	output = 'date;paymode;info;payee;wording;amount;category;tags\n'
	for e in expenseslist:
		mylist = [str(e.date), str(e.paymode), e.info.replace(";",","), e.payee.replace(";",","), e.wording.replace(";",","), str(e.amount), "", e.tags.replace(";",",")]
		output += '%s\n'%(";".join(mylist))
	return output

@add_visitor
def basecontext (request):
	""" Refresh user session pannels. For now, only takes the last data at DB.
		"""
	return {
			'statistics'		:	Statistics(),
			}

# ----------------------------------------------------------------------------
# Your views here.

def welcome (request):
	next = request.GET.get('next', '')
	if request.user.is_authenticated and request.user.groups.filter(name=pref.app_auser_group).exists():
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

@need_login
@need_group
def new_purse (request):
	if request.method == "POST":
		form = PurseForm(request.POST)
		resetto = request.POST ['resetto']
		if resetto == '':
			resetto = 0
		resetto = Decimal(resetto)
		if form.is_valid():
			newaccount = form.save (commit = False)
			newaccount.user = request.user
			newaccount.cuantity = resetto
			newaccount.save()
		return redirect ('purse:welcome')
	context = { 'form' : PurseForm }
	context.update (basecontext (request) )
	return render (request, 'purse/new_purse.html', context)

@need_login
@need_group
def modify_purse (request, pk):
	account = get_object_or_404 (Account, pk = pk)
	if request.user != account.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	if request.method == "POST":
		form = PurseForm(request.POST, instance=account)
		resetto = request.POST ['resetto']
		if form.is_valid():
			account = form.save (commit=False)
			account.user = request.user
			if resetto != '':
				account.resetto(resetto)
			account.update_account()
		return redirect ('purse:expenses', pk=pk)
	form = PurseForm (instance=account)
	context = { 'form' : form,
				'purse': account,
			 }
	context.update (basecontext (request) )
	return render (request, 'purse/modify_purse.html', context)

@need_login
@need_group
def expenses_purse(request, pk):
	account = get_object_or_404 (Account, pk = pk)
	pagenumber = request.GET.get('page', '1')
	if request.user != account.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	if request.method == 'POST':
		try:
			request.POST ['positive']
			positive = True
		except:
			positive = False
		form = ExpenseForm(request.POST, request.FILES)
		if form.is_valid():
			expense = form.save(commit=False)
			expense.user = request.user
			expense.account = account
			expense.amount = -abs(expense.amount)
			if positive:
				expense.amount = -expense.amount
			expense.save()
			expense.normalize_image()
			account.update_account()

	expenses = Expense.objects.filter (account=account).order_by ('-date', '-id')
	if not account.showexported:
		expenses = expenses.filter(exported=False)
	paginated = Paginator(object_list=expenses, per_page=pref.expenses_list_maxitems , orphans=pref.expenses_list_orphans, allow_empty_first_page=True)
	page = paginated.get_page(pagenumber)
	context = {
			'purse' 	: account,
			'page'		: page,
			'count'		: len (expenses),
			'form'		: ExpenseForm,
			}
	context.update (basecontext (request) )
	return render (request, 'purse/expenses_add.html', context)

@need_login
@need_group
def expenses_modify (request, pk):
	expense = get_object_or_404 (Expense, pk = pk)
	if request.user != expense.account.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	oldimage = ""
	if expense.image != "":
		oldimage = expense.image.path[:] # make a hardcopy of actual value	
	if request.method == "POST":
		try:
			request.POST ['positive']
			positive = True
		except:
			positive = False
		form = ExpenseForm(request.POST, request.FILES, instance=expense)
		if form.is_valid():
			expense = form.save (commit=False)
			expense.cleanmyfile (oldimage)
			expense.amount = -abs(expense.amount)
			if positive:
				expense.amount = -expense.amount
			expense.save()
			expense.normalize_image()
			expense.account.update_account()
		return redirect ('purse:expenses', pk=expense.account.pk)
	form = ExpenseForm (instance=expense)
	context = { 'form' : form,
				'expense': expense,
			 }
	context.update (basecontext (request) )
	return render (request, 'purse/modify_expense.html', context)

@need_login
@need_group
def expenses_delete (request, pk):
	expense = get_object_or_404 (Expense, pk = pk)
	if request.user != expense.account.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	if request.method == 'POST':
		expense.remove_expense()
		expense.account.update_account()
		return redirect ('purse:expenses', pk=expense.account.pk)
	context = {
			'expense'	: expense,
			}
	context.update (basecontext (request) )
	return render (request, 'purse/expenses_delete.html', context)

@need_login
@need_group
def expenses_export(request, pk):
	purse = get_object_or_404 (Account, pk = pk)
	pagenumber = request.GET.get('page', '1')
	if request.user != purse.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	expenseslist = Expense.objects.filter(account = pk, exported=False).order_by ('-date', '-id')
	if request.method == "POST":
		csvcontent = makecsv (expenseslist)
		response = HttpResponse (csvcontent, content_type='text/csv')
		response ['Content-Disposition'] = 'attachment; filename="%s.csv"'%purse.name
		return response
	paginated = Paginator (object_list= expenseslist, per_page=pref.expenses_list_maxitems, orphans=pref.expenses_list_orphans, allow_empty_first_page=True)
	page = paginated.get_page (pagenumber)
	context = { 'page'		: page,
				'purse'		: purse,
				}
	context.update (basecontext (request) )
	purse.purgepurse()
	return render (request, 'purse/expenses_export.html', context)

@need_login
@need_group
def mark_exported (request, pk):
	purse = get_object_or_404 (Account, pk = pk)
	if request.user != purse.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	expenseslist = Expense.objects.filter(account = pk, exported=False)
	for e in expenseslist:
		e.exported = True
		e.save()
	return redirect ('purse:expenses', pk=pk)

@need_login
@need_group
def expenses_image (request, pk):
	expense = get_object_or_404 (Expense, pk = pk)
	if request.user != expense.user:
		return redirect (f"{reverse('pibucket:login_user')}?next={request.path}")
	if request.method == "POST":
		expense.delete_media()
		expense.image = None
		expense.save()
		return redirect ('purse:expenses', pk=expense.account.pk)
	context = {	'expense' : expense,
				'purse'	  : expense.account,}
	context.update (basecontext (request) )
	return render (request, 'purse/showimage.html', context)

# self user management

@force_logout
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
			return render (request, 'purse/msgs/msgconfirm.html',
				{
				'title'	: 'Login',
				'msg' 	: 'Usuario o contraseña incorrecta.',
				'back' 	: True,
				})

	else:
		user, password = ("","")
		if request.user.is_authenticated:
			user = request.user
			password = request.user.password
		return render (request, 'purse/login.html', {
			'user' 		: user,
			'password' 	: password,
			'next' : next,
			})

@force_logout
def logout_user (request):
	return redirect ('purse:welcome')

@force_logout
def SignUpView (request):
	if request.method == "POST":
		form = SignUpForm(request.POST)
		username = request.POST ['username']
		if len (User.objects.filter (username=username)) >= 1:
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Date de alta',
						'msg' 	: 'El usuario ya existe.',
						'back' 	: True,
						})
		email = request.POST ['email']
		try:
			validate_email (email)
		except :
			return HttpResponse ('introduce un e-mail válido: <strong>%s</strong>'%email)
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Date de alta',
						'msg' 	: 'Las contraseñas no coinciden.',
						'back' 	: True,
						})

		if form.is_valid():
			newuser = form.save(commit=False)
			newuser.save ()
			user = authenticate(request, username=username, password=password)
			g = Group.objects.get(name=pref.app_auser_group)
			g.user_set.add(user)			
			if user is not None:
				login(request, user)
			send_user_mail (	recipients = 	email,
								title = 		'¡Bienvenido a purse!',
								template = 		'purse/mails/welcome_user.html',
								txtcontent = 	'%s te damos la bienvenida a purse.'%username,
								templatecontext = {
													'domain'	:	settings.TEMPLATE_DOMAIN,
													'user'		:	user,
													'password'	:	password,
													}
								)
			return redirect ('purse:welcome')
		else:
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Date de alta',
						'msg' 	: 'Algunos campos del formulario fueron incorrectos.',
						'back' 	: True,
						})
	form = SignUpForm
	return render (request, 'purse/singup.html',
							 {
							'form': form,
							'head': "Date de alta",
							})

@need_login
def editdata_user (request, pk):
	user = get_object_or_404 (User, pk = pk)
	if request.user != user:
		return redirect (f"{reverse('purse:login_user')}?next={request.path}")
	if request.method == "POST":
		try:
			validate_email (request.POST ['email'])
		except:
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Editar datos de usuario',
						'msg' 	: 'Introduce un e-mail válido',
						'back' 	: True,
						})
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
		userdata = user
		userdata.first_name = request.POST ['first_name']
		userdata.last_name	= request.POST ['last_name']
		userdata.email = request.POST ['email']
		userdata.save()
		return render (request, 'purse/msgs/msgconfirm.html',
				{
				'title'	: 'Actualizar tus datos',
				'msg' 	: 'Tus datos se han guardado.',
				'ppal'	: True,
				})
	try:
		userconfig = UserConfig.objects.get (user = user)
	except:
		userconfig = None

	context = {	'user'					: 	request.user,
				'userconfig'			: 	userconfig,
			}
	return render (request, 'purse/editdata_user.html', context)

@need_login
def changepass_user (request, pk):
	user = get_object_or_404 (User, pk = pk)
	if request.user != user:
		return redirect (f"{reverse('purse:login_user')}?next={request.path}")
	if request.method == "POST":
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return HttpResponse ('Las contraseñas no coinciden')
		user = User.objects.get(username = request.user)
		user.set_password (password)
		user.save()
		login(request, user)
		return render (request, 'purse/msgs/msgconfirm.html',
					{
					'title'	: 'Cambiar contraseña',
					'msg' 	: 'La contraseña ha cambiado',
					'ppal'	: True,
					})

	form = PasschForm (instance = request.user)
	return render (request, 'purse/singup.html', 
				{
				'form' : form,
				'head' : "Ingresa una nueva contraseña"
				})

@force_logout
def resetmypassw (request):
	if request.method == "POST":
		username = request.POST ['username']
		email = request.POST ['email']
		try:
			validate_email (email)
		except:
			return HttpResponse ('introduce un e-mail válido: <strong>%s</strong>'%email)
		try:
			user = User.objects.get(email = email, username = username)
		except:
			return render (request, 'recetas/msgs/msgconfirm.html',
						{
						'title'	: 'Restablecer contraseña',
						'msg' 	: 'No hay ningún usuario registrado con estos datos',
						'back'	: True,
						})
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		send_user_mail (	recipients = 	user.email,
							title = 		'Restablece la contraseña',
							template = 		'purse/mails/password_reset.html',
							txtcontent = 	'%s, aún te queda un paso más para restablecer tu contraseña'%username,
							templatecontext = {
												'domain'	:	settings.TEMPLATE_DOMAIN,
												'user'		:	user,
												'uid'		:	uid,
												'token'		:	token,
												}
							)
		return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Restablecer contraseña',
						'msg' 	: 'Se ha enviado un e-mail para restablecer su contraseña',
						'ppal' 	: True,
						})
	return render (request, 'purse/remembermypassword_user.html', {} )

@force_logout
def resetconfirm (request, uidb64, token):
	if request.method == "POST":
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return HttpResponse ('Las contraseñas no coinciden')
		for user in User.objects.all():
			if default_token_generator.check_token(user, token):
				break
		user.set_password (password)
		user.save()
		login(request, user)
		return render (request, 'purse/msgs/msgconfirm.html',
					{
					'title'	: 'Restablecer la contraseña',
					'msg' 	: 'La contraseña ha sido restablecida',
					'ppal'	: True,
					})
	form = PasschForm ()
	return render (request, 'purse/singup.html', {
				'form' : form,
				'head' : "Ingresa una nueva contraseña"
				})	
