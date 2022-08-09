"""
    Handle Shard Retrival Operations
"""
from concurrent.futures import ThreadPoolExecutor
import json
import mimetypes
import os
from urllib import response
from wsgiref.util import FileWrapper
from django.http import HttpResponse, StreamingHttpResponse
import Main.urls as Startup
import requests
from Shared.Util.bucket import get_client_ip, range_re, RangeFileWrapper, registerToInstance
from Shared.models import cachedFile, registeredInstance
from Shared.storage import cacheMemoryManagemenent, deleteAnyCachedFile


"""
    Retrive file from shard
"""
def retriveFromShard(request,instance,filename,queryString, signature=None):
    """
        Get the instance Ipv4 from the GOSSIP instance or from registered instances 
    """
    instanceIPv4 = getInstanceIPv4(instance)
    if instanceIPv4 == None:
        return HttpResponse("Instance Not In Shard",status=500)
    #get the client ipv4 
    clientIPv4 = get_client_ip(request)


    # get the file
    try:
        stream = requests.get(f"http://{instanceIPv4}/api/v1/shard_download/{queryString}?signature={signature}",
            stream=True,
            headers={"SHARD-KEY":os.environ.get("SHARD_KEY"),"HTTP-X-FORWARDED-FOR":clientIPv4})
        
        #lamda function to send the file to the client as a stream
        def sendStream(path):
            #return the file stream
            path = f"./Storage/Temp/{queryString}"
            range_header = request.META.get('HTTP_RANGE', '').strip()
            range_match = range_re.match(range_header)
            size = os.path.getsize(path)
            content_type, encoding = mimetypes.guess_type(path)
            content_type = content_type or 'application/octet-stream'
            if range_match:
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else size - 1
                if last_byte >= size:
                    last_byte = size - 1
                length = last_byte - first_byte + 1
                resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length), status=206, content_type=content_type)
                resp['Content-Length'] = str(length)
                resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
            else:
                resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
                resp['Content-Length'] = str(size)
            resp['Accept-Ranges'] = 'bytes'

            return resp
    
        #lamda function to write the file and then send the file 
        def writeFile(queryString,stream):
            # Memory management
            result = cacheMemoryManagemenent(int(stream.headers.get("Content-Length")))
            if result[0] == False:
                return HttpResponse(result[1],status=409)
            
            with open(f"./Storage/Temp/{queryString}","wb") as cacheFile:
                for chunk in stream.iter_content(chunk_size=8192):
                    cacheFile.write(chunk)
            stream.close()

            #create or update the record for when the file was cached
            if cachedFile.objects.filter(fileQueryName=queryString).exists(): 
                cachedFile.objects.get(fileQueryName=queryString).update(stream.headers.get("content-length"))
            else:
                cachedFileRecord = cachedFile(fileQueryName=queryString,public=False,size=int(stream.headers.get("content-length")))
                cachedFileRecord.save()

            
            #send the file 
            return sendStream(f"./Storage/Temp/{queryString}") 
        
        #failed to get the file with 404 
        #   -> delete the file 
        if stream.status_code == 404:
            deleteAnyCachedFile(queryString)

        #failed to get the file 
        if stream.status_code != 200: return HttpResponse(stream.text,status=stream.status_code)
            
        #got the file
        stream.raise_for_status()

        
        # update the number of reads 
        cachedRecords = cachedFile.objects.filter(fileQueryName=queryString)
        if cachedRecords.exists():
            cachedRecords[0].appendReads()
        
        #file does not exist in the cache then write the file and send it
        if queryString not in os.listdir("./Storage/Temp/"):
            writeFile(queryString,stream)
            
        #but if file exists in the cache
        #check if the cached file is still valid by checking if the cached dates match
        cachedFileTimestamp = cachedFile.objects.get(fileQueryName=queryString).lastUpdated()
        receivedFileTimestamp = int(stream.headers.get("last-updated"))

        #if hashes do not match rewrite the file and send the file 
        if receivedFileTimestamp > cachedFileTimestamp : 
            return writeFile(queryString,stream)

        #close the stream and send the cached file 
        stream.close()
        return sendStream(f"./Storage/Temp/{queryString}") 
    except:
        return HttpResponse(f"Connection to instance {instance} failed")
   

"""
    Delete file on another instance
"""
def deleteFileOnAnotherInstance(queryString,instance):
    # Headers and form data
    headers = {'SHARD-KEY': os.environ.get("SHARD_KEY"),}
    files = {
        'query_string': (None,queryString),
    }

    # Get the ipv4 
    instanceIPv4 = getInstanceIPv4(instance)

    # Check if IPv4 is not None
    if instanceIPv4 == None: return HttpResponse(f"Could not find instance {instance}",status=404)

    # Send the requests
    try: 
        result = requests.post(f'http://{instanceIPv4}/api/v1/delete', headers=headers, files=files,timeout=5)
        return HttpResponse(result.text,status=result.status_code)
    except:
        status = "Connection Failed"
        return HttpResponse(status,status=500)


"""
    Delete cached file on other instances helper 
"""
def deleteCachedFileOnOtherInstances(queryString):
    # Instance is the gossip instance
    if "GOSSIP_INSTANCE" not in os.environ:
        endpoints = [{
                "ipv4" : instance.ipv4,
                "name" : instance.instance_name,
                "query_string" : queryString
            } for instance in registeredInstance.objects.all()]
        
    else:
        # re-register
        gossip_instance_ip = os.environ.get("GOSSIP_INSTANCE")
        registerToInstance(gossip_instance_ip)
        endpoints = [{
                "ipv4" : Startup.knownInstances[instance]["ipv4"],
                "name" : instance,
                "query_string": queryString
            } for instance in Startup.knownInstances]

    response = []

    with ThreadPoolExecutor() as exec:
        res = exec.map(deleteFromCache,endpoints)
        for result in res: 
            response.append(result)

    return HttpResponse(json.dumps(response))

"""
    Get another instance ipv4 
"""
def getInstanceIPv4(instance)-> str :
    """
        Get the instance Ipv4 from the GOSSIP instance or from registered instances 
    """
    if "GOSSIP_INSTANCE" not in os.environ:
        # Not a gossip instance and not registered on any shard return Failure 
        if  registeredInstance.objects.all().count() < 1: return None
        # Set the ipv4
        instanceIPv4 = registeredInstance.objects.get(instance_name=instance).ipv4 if registeredInstance.objects.filter(instance_name=instance).exists() else None

        return instanceIPv4

    #function to get the IPv4 from list returned on registration
    def getInstanceIpv4(instance, Startup):
        if Startup.knownInstances != None and instance in Startup.knownInstances:
            return Startup.knownInstances.get(instance)['ipv4']
        return None

    #get the instance ipv4
    instanceIPv4 = getInstanceIpv4(instance,Startup)
    
    #if instanceIPv4 is None then re-register to get an updated list of instances 
    if instanceIPv4 == None:
            gossip_instance_ip = os.environ.get("GOSSIP_INSTANCE")
            registerToInstance(gossip_instance_ip)

    #get the IPv4 from the updated list
    return getInstanceIpv4(instance,Startup)



"""
    Function to send a delete cache request
"""
def deleteFromCache(params):
    # Headers and form data
    headers = {'SHARD-KEY': os.environ.get("SHARD_KEY"),}
    files = {
        'query_string': (None, params["query_string"]),
    }

    # Send the requests
    try:
        result = requests.post(f'http://{params["ipv4"]}/api/v1/delete_cache', headers=headers, files=files,timeout=5)
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


        
        
            
        