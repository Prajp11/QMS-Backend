# Register your models here.
from django.contrib import admin
from .models import Item

# Register the Item model to be displayed in the admin interface
admin.site.register(Item)
