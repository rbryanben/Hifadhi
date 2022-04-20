from django.urls import path
from .views import *

urlpatterns = [
    path('v1/store',store,name="Store File API Call"),
    path('v1/cache',cache,name="Cache File API Call")
]
