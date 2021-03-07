""" purse urls """
from django.urls import path
from . import views 

from django.conf import settings
from django.conf.urls.static import static

app_name = 'purse'

urlpatterns = [
	path('',								views.welcome, 				name='welcome'),
	path('accounts/login/',			views.login_user,			name='login_user'),
	path('accounts/logout/', 			views.logout_user,			name='logout_user'),
	path('accounts/signup/',        	views.SignUpView,           name='signup_user'),
	path('accounts/user/<int:pk>',  	views.editdata_user,        name='editdata_user'),
	path('accounts/password_change/<int:pk>',   views.changepass_user,     name='changepass_user'),
	path('accounts/password_reset/',            views.resetmypassw,        name='sendmypassw'),
	path('accounts/<uidb64>/<token>',           views.resetconfirm,        name='resetconfirm'),
	path('new',						views.new_purse,			name='add_new_purse'),
	path('modify/<int:pk>',			views.modify_purse,			name='modify_purse'),
	path('expenses/<int:pk>',			views.expenses_purse,		name='expenses'),
	path('expenses/modify/<int:pk>', 	views.expenses_modify, 		name='expenses_modify'),
	path('expenses/delete/<int:pk>', 	views.expenses_delete, 		name='expenses_delete'),
	path('expenses/export/<int:pk>', 	views.expenses_export, 		name='expenses_export'),
	path('expenses/image/<int:pk>' , 	views.expenses_image, 		name='expenses_image'),
	path('expenses/markexported/<int:pk>', views.mark_exported, 	name='expenses_mark'),
    ]
