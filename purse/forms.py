from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Account, Expense
from django.utils.translation import gettext_lazy as _


class SignUpForm (UserCreationForm):
	first_name 	= forms.CharField (required = True)
	last_name 	= forms.CharField (required = True)
	email		= forms.EmailField(required = True)
	first_name.label 	= _('First Name')
	last_name.label		= _('Last Name')
	email.label			= _('e-mail')
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
		labels = {
			'username'	: _('User'),
			'password1'	: _('Password'),
			'password2'	: _('Password'),
		}

class PasschForm (UserCreationForm):
	class Meta:
		model = User
		fields = (
			'password1',
			'password2',
			)

class PurseForm (forms.ModelForm):
	resetto = forms.DecimalField (decimal_places = 2, required=False, initial="", label=_('Reset purse to this amount') )
	class Meta:
		model = Account
		fields = ('name','color', 'active', 'currency', 'showexported')
		labels = {
			'name'			:	_('Name'),
			'color'			:	_('Color'),
			#'adjustment'	:	_('Adjustment'),
			'active'		:	_('Active'),
			'currency'		:	_('Currency'),
			'showexported'	:	_('Show exported expenses'),
		}

class ExpenseForm (forms.ModelForm):
	date 	= forms.DateField ( label= _('Date'), required = True, initial=timezone.now)
	class Meta:
		model = Expense
		fields = (
			'date',
			#'info',
			#'payee',
			'wording',
			'amount',
			#'tags',
			'image')
		labels = {
			'info'		:	_('info'),
			'paymode'	:	_('paymode'),
			'payee'		:	_('payee'),
			'wording'	:	_('wording'),
			'amount'	:	_('amount'),
			'tags'		:	_('tags'),
			'image'		:	_('image'),
		}
