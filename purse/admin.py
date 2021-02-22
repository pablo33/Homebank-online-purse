from django.contrib import admin
from .models import Account, VisitCounter, UserConfig

# Register your models here.
admin.site.register(Account)
admin.site.register(VisitCounter)
admin.site.register(UserConfig)
