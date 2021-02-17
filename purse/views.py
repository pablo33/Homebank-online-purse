from django.shortcuts import render, HttpResponse, redirect
from .models import Account, Expense, VisitCounter
from .forms import SignUpForm, PasschForm
from hbpurse import settings
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import get_template


def add_visitor (request):
	# TO DO
	pass


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

# Create your views here.

def welcome (request):
	add_visitor (request)
	#return HttpResponse ('Hello world')
	return render(request, 'purse/welcome.html', {} )

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
			'next' 		: next,
			})

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
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Sign up yourself',
						'msg' 	: 'User already exists.',
						'back' 	: True,
						})
		email = request.POST ['email']
		try:
			validate_email (email)
		except :
			return HttpResponse ('Sign up with a valid e-mail: <strong>%s</strong>'%email)
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Sign up yourself',
						'msg' 	: 'Passwords does not match.',
						'back' 	: True,
						})

		if form.is_valid():
			newuser = form.save(commit=False)
			newuser.save ()
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
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
			return render (request, 'purse/msgs/msgconfirm.html',
						{
						'title'	: 'Sign up yourself',
						'msg' 	: 'Some fields where incorrect.',
						'back' 	: True,
						})
	form = SignUpForm
	return render (request, 'purse/singup.html',
							 {
							'form': form,
							'head': "Sign up yourself",
							})

def editdata_user (request, pk):
	try:
		userweb = User.objects.get(pk = pk)
	except:
		# requested user does not exist
		return redirect ('recetas:welcome')
	if request.user != userweb:
		# requested user and logged user is not the same
		return redirect ('recetas:welcome')
	if request.method == "POST":
		try:
			request.POST ['suscr_new']
			suscr_new = True
		except:
			suscr_new = False
		try:
			request.POST ['suscr_my']
			suscr_my = True
		except:
			suscr_my = False
		try:
			request.POST ['suscr_all']
			suscr_all = True
		except:
			suscr_all = False
		try:
			userreg = Userdata.objects.get (user = request.user)
			userreg.suscr_new = suscr_new
			userreg.suscr_all = suscr_all
			userreg.save()
		except:
			userreg = Userdata.objects.create (user = request.user, suscr_new = suscr_new, suscr_all = suscr_all)
		userdata = User.objects.get (pk = pk)
		userdata.first_name = request.POST ['first_name']
		userdata.last_name	= request.POST ['last_name']
		email = request.POST ['email']
		try:
			validate_email (email)
		except:
			return render (request, 'recetas/msgs/msgconfirm.html',
						{
						'secciones' 	: 	secciones (),
						'title'	: 'Editar datos de usuario',
						'msg' 	: 'Introduce un e-mail válido',
						'back' 	: True,
						})
		userdata.email = request.POST ['email']
		userdata.save()
		if suscr_my:
			suscribeme_to_an_user (request.user, request.user)
		return render (request, 'recetas/msgs/msgconfirm.html',
				{
				'secciones' 	: 	secciones (),
				'title'	: 'Actualizar tus datos',
				'msg' 	: 'Tus datos se han guardado.',
				'ppal'	: True,
				})
	try:
		userreg = Userdata.objects.get (user = request.user)
	except:
		userreg = None

	context = {	'secciones' 		: 	secciones (),
				'user'				: 	request.user,
				'tip_random'		:	fetch_tip("Opciones de suscripción"),
				'userreg'			: 	userreg,
			}
	return render (request, 'recetas/editdata_user.html', context)

def changepass_user (request, pk):
	try:
		userweb = User.objects.get(pk = pk)
	except:
		# requested user does not exist
		return redirect ('recetas:welcome')
	if request.user != userweb:
		# requested user and logged user is not the same
		return redirect ('recetas:welcome')
	if request.method == "POST":
		password  = request.POST ['password1']
		password2 = request.POST ['password2']
		if password != password2:
			return HttpResponse ('Las contraseñas no coinciden')
		user = User.objects.get(username = request.user)
		user.set_password (password)
		user.save()
		login(request, user)
		return render (request, 'recetas/msgs/msgconfirm.html',
					{
					'secciones' 	: 	secciones (),
					'title'	: 'Cambiar contraseña',
					'msg' 	: 'La contraseña ha cambiado',
					'ppal'	: True,
					})

	form = PasschForm (instance = request.user)
	return render (request, 'recetas/singup.html', {
				'secciones' 	: 	secciones (),
				'form' : form,
				'head' : "Ingresa una nueva contraseña"
				})

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
						'secciones' 	: 	secciones (),
						'title'	: 'Restablecer contraseña',
						'msg' 	: 'No hay ningún usuario registrado con estos datos',
						'back'	: True,
						})
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		send_user_mail (	recipients = 	user.email,
							title = 		'Restablece la contraseña',
							template = 		'recetas/mails/password_reset.html',
							txtcontent = 	'%s, aún te queda un paso más para restablecer tu contraseña'%username,
							templatecontext = {
												'domain'	:	settings.TEMPLATE_DOMAIN,
												'user'		:	user,
												'uid'		:	uid,
												'token'		:	token,
												}
							)
		return render (request, 'recetas/msgs/msgconfirm.html',
						{
						'secciones' 	: 	secciones (),
						'title'	: 'Restablecer contraseña',
						'msg' 	: 'Se ha enviado un e-mail para restablecer su contraseña',
						'ppal' 	: True,
						})
	return render (request, 'recetas/remembermypassword_user.html', {'secciones' 	: 	secciones ()} )

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
		return render (request, 'recetas/msgs/msgconfirm.html',
					{
					'secciones' 	: 	secciones (),
					'title'	: 'Restablecer la contraseña',
					'msg' 	: 'La contraseña ha sido restablecida',
					'ppal'	: True,
					})
	form = PasschForm ()
	return render (request, 'recetas/singup.html', {
				'secciones' 	: 	secciones (),
				'form' : form,
				'head' : "Ingresa una nueva contraseña"
				})	
