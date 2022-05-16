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
    #try get from list returned on registration
    print(Startup.knownInstances)
    if instance in Startup.knownInstances:
        print(Startup.knownInstances.get(instance))

    return HttpResponse(f"Should get {filename} from {instance}",status=501)