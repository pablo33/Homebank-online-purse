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
		fields = ('name','color','adjustment', 'active', 'currency', 'showexported')
		labels = {
			'name'			:	_('Name'),
			'color'			:	_('Color'),
			'adjustment'	:	_('Adjustment'),
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
