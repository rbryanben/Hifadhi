from django.urls import path
from .views import *

urlpatterns = [
    path('v1/health',health,name="Get the health of an instance"),
    path('v1/store',store,name="Store File API Call"),
    path('v1/cache',cache,name="Cache File API Call"),
    path('v1/download/<str:queryString>',download,name="Download File API Call"),
    path('v1/stream/<str:queryString>',stream,name="Stream File API Call"),
    path('v1/register',register,name="Register API Call"),
    path('v1/registered_instances',registeredInstances,name="Retrive Registered Instances"),
    path('v1/shard_instance',shardInstance,name="Get IPv4 of an instance"),
    path('v1/shard_download/<str:queryString>',shardDownload,name="Download endpoint for other instances"),
]
