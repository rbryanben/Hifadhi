"""
    Handle Shard Retrival Operations
"""
import imp
from django.http import HttpResponse
import Main.urls as Startup
import requests

def retriveFromShard(request,instance,filename):
    """
        Get the instance Ipv4 
    """

    instanceIPv4 = None

    #check if the file is stored in the local cache
    print("skipped obtaining from local cache")
    
    #try get from list returned on registration
    if instance in Startup.knownInstances:
        instanceIPv4 = Startup.knownInstances.get(instance)['ipv4']

    print(instanceIPv4)

    return HttpResponse(f"Should get {filename} from {instance}",status=501)