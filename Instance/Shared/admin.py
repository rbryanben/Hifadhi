from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(storedFile)
admin.site.register(cachedFile)
admin.site.register(presignedURL)
admin.site.register(ipv4Access)
admin.site.register(registeredInstance)