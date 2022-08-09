import json
import os 
import re
import psutil
import time
import hashlib
from requests import request
import requests
import Main.urls as startUp
from django.db.models import Sum
from Shared.models import storedFile, cachedFile
range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

"""
    Gets a client IPv4 from a requset
"""
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


"""
    Register to an instance method
"""
def registerToInstance(instance_ip):
    #check if shard key is defined
    if "SHARD_KEY" not in os.environ: 
        startUp.registeredOnGossip = [False,"SHARD_KEY Not Defined"]
        return

    info = getInstanceInfo()

    #try on http
    try:
        result = requests.post(f"http://{instance_ip}/api/v1/register",json=info,headers={"SHARD-KEY":os.environ.get("SHARD_KEY")})
        startUp.registeredOnGossip = [True,f"http://{instance_ip}"]
        startUp.knownInstances = json.loads(result.text)

        # Update to the terminal 
        print(f"Registered on gossip instance http://{instance_ip}\n\n")
        return
    except Exception as e:
        print(f"Failed to connect to http://{instance_ip}: {e}")
        startUp.registeredOnGossip = [False,f"Failed To Connect {e}"]

    #try on https 
    try:
        result = requests.post(f"https://{instance_ip}/api/v1/register",json=info,headers={"SHARD-KEY":os.environ.get("SHARD_KEY")})
        startUp.knownInstances =json.loads(result.text)
        startUp.registeredOnGossip = [True,f"https://{instance_ip}"]
         # Update to the terminal 
        print(f"Registered on gossip instance https://{instance_ip}\n\n")
        return
    except Exception as e:
        print(f"Failed to connect to https://{instance_ip}: {e}")
        startUp.registeredOnGossip = [False,f"Failed To Connect {e}"]

    print("Failed To Connect To Gossip Instance -> Exception: " + startUp.registeredOnGossip[1] + "\n\n")


"""
    Function to return information about this current instance 
"""
def getInstanceInfo():
    hdd = psutil.disk_usage('/')
    return {
        "total_memory": hdd.total / (2**30), #2**30 == 1024*3
        "used_memory": hdd.used / (2**30),
        "stored_files_size": storedFile.objects.all().aggregate(Sum('size')).get("size__sum") if storedFile.objects.all().aggregate(Sum('size')).get("size__sum") != None else 0 ,
        "cached_files_size": cachedFile.objects.all().aggregate(Sum('size')).get("size__sum") if cachedFile.objects.all().aggregate(Sum('size')).get("size__sum") != None else 0,
        "instance_name": os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
        "stored_files_count": storedFile.objects.all().count(),
        "cached_files_count": cachedFile.objects.all().count(),
        "uptime": time.time() - startUp.startupTime
    }

"""
    Streaming Class 
"""
class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            print("Stream ended")
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data
        


"""
    Function to send a request to another instance to cache a file 
"""
def sendCacheRequest(params):
    # Headers and form data
    headers = {'SHARD-KEY': '2022RBRYANBEN',}
    files = {
        'priority': (None, params["priority"]),
        'query_string': (None, params["query_string"]),
    }

    # Send the requests
    try:
        result = requests.post(f'http://{params["ipv4"]}/api/v1/cache', headers=headers, files=files)
        status = result.status_code
    except:
        status = "Connection Failed"

    # Return the result 
    return {
        params["name"]: {
            "ipv4" : params["ipv4"],
            "status" : status
        }
    }
