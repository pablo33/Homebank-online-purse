""" purse urls """
from django.urls import path
from . import views 

from django.conf import settings
from django.conf.urls.static import static

app_name = 'purse'

urlpatterns = [
	path('',						views.welcome, 				name='welcome'),
	path('accounts/login/',			views.login_user,			name='login_user'),
	path('accounts/logout/', 		views.logout_user,			name='logout_user'),
	path('accounts/signup/',        views.SignUpView,           name='signup_user'),
	path('accounts/user/<int:pk>',  views.editdata_user,        name='editdata_user'),
	path('accounts/password_change/<int:pk>',   views.changepass_user,     name='changepass_user'),
	path('accounts/password_reset/',            views.resetmypassw,        name='sendmypassw'),
	path('accounts/<uidb64>/<token>',           views.resetconfirm,        name='resetconfirm'),
	path('purse/new',				views.new_purse,			name='add_new_purse'),
	path('purse/modify/<int:pk>',	views.modify_purse,			name='modify_purse'),
	path('purse/expenses/<int:pk>',	views.expenses_purse,		name='expenses'),
    ]
