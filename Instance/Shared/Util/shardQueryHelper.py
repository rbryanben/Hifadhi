"""
    Handle Shard Retrival Operations
"""
from django.http import HttpResponse

def retriveFromShard(instance,filename):
    return HttpResponse(f"Should get {filename} from {instance}",status=501)