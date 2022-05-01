from django.urls import path
from .views import *

urlpatterns = [
    path('v1/store',store,name="Store File API Call"),
    path('v1/cache',cache,name="Cache File API Call"),
    path('v1/download/<str:queryString>',download,name="Download File API Call"),
    path('v1/stream/<str:queryString>',download,name="Stream File API Call"),
    path('v1/files',getFilesList,name="Test API for getting files"),
    path('v1/storage', getStorageDetail, name="Test API for getting storage details"),
]
