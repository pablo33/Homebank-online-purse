from django.contrib import admin
from .models import Account, VisitCounter, UserConfig

# Register your models here.
class AccountAdmin (admin.ModelAdmin):
	list_display	= ('user', 'name','color', 'active')
	list_per_page	= 20
	ordering		= ('user',)
admin.site.register(Account, AccountAdmin)


class VisitCounterAdmin (admin.ModelAdmin):
	list_display	= ('timevisit', 'user', 'ip')
	list_per_page	= 100
	ordering		= ('-timevisit',)
	search_fields	= ('user',)
admin.site.register(VisitCounter, VisitCounterAdmin)


class UserConfigAdmin (admin.ModelAdmin):
	list_display	= ('user', 'showinactive')
	list_per_page	= 20
	ordering		= ('user',)
admin.site.register(UserConfig, UserConfigAdmin)
