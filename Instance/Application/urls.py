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
    path('v1/presign',preSignedAccessDelete,name="Delete presigned access signature"),
    path('v1/presign/<str:queryString>',preSignedAccess,name="Obtains a pre-signed url"),
    path('v1/ipv4access/<str:queryString>',IPv4Access,name="Gives IPv4 Access to a file for some time"),
    path('v1/shard_cache',shardCache,name="Instructs all instances to cache a file"),
]
