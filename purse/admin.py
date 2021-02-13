from django.contrib import admin
from .models import Account, VisitCounter

# Register your models here.
admin.site.register(Account)
admin.site.register(VisitCounter)
