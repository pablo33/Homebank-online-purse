from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Account

class SignUpForm (UserCreationForm):
	first_name 	= forms.CharField (required = True)
	last_name 	= forms.CharField (required = True)
	email		= forms.EmailField(required = True)
	class Meta:
		model = User
		fields = (
			'username',
			'email',
			'first_name',
			'last_name',
			'password1',
			'password2',
			)

class PasschForm (UserCreationForm):
	class Meta:
		model = User
		fields = (
			'password1',
			'password2',
			)

class PurseForm (forms.ModelForm):
	class Meta:
		model = Account
		fields = ('name','color','adjustment', 'active')