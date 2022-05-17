"""
    Handle Shard Retrival Operations
"""
import mimetypes
import os
from wsgiref.util import FileWrapper
from django.http import HttpResponse, StreamingHttpResponse
import Main.urls as Startup
import requests
from Shared.Util.bucket import range_re, RangeFileWrapper
from Shared.Util.bucket import registerToInstance

def retriveFromShard(request,instance,filename,queryString, signature=None):
    """
        Get the instance Ipv4 
    """

    #check if the file is stored in the local cache
    print("skipped obtaining from local cache")

    #function to get IPv4 from list returned on registration
    def getInstanceIpv4(instance, Startup):
        if instance in Startup.knownInstances:
            return Startup.knownInstances.get(instance)['ipv4']
        return None

    instanceIPv4 = getInstanceIpv4(instance,Startup)
    
    #if instanceIPv4 is None then re-register
    if instanceIPv4 == None:
        if "GOSSIP_INSTANCE" in os.environ:
            gossip_instance_ip = os.environ.get("GOSSIP_INSTANCE")
            registerToInstance(gossip_instance_ip)

        #get the IPv4 from the updated list
        instanceIPv4 = getInstanceIpv4(instance,Startup)
    
    # if instanceIPv4 is still Null update that the instance could not be found in the Shard
    if instanceIPv4 == None:
        return HttpResponse(f"Could not find instance {instance}",status=404)
    
    # get the file
    try:
        with requests.get(f"http://{instanceIPv4}/api/v1/shard_download/{queryString}?signature={signature}",stream=True,headers={"SHARD-KEY":os.environ.get("SHARD_KEY")}) as stream:
            stream.raise_for_status()
            with open(f"./Storage/Cache/{filename}","wb") as cacheFile:
                for chunk in stream.iter_content(chunk_size=8192):
                    cacheFile.write(chunk)
    except:
        return HttpResponse(f"Failed to get {filename} from {instance}",status=404)

    #return the file stream
    path = f"./Storage/Cache/{filename}"
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