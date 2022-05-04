import imp
import mimetypes
import re
from django.http import HttpResponse, StreamingHttpResponse
from Shared.decorators import PostOnly
from Shared.storage import store as storeFile, cache as cacheFile
from Shared.models import storedFile, registeredInstance, cachedFile
from django.db.models import Sum
from Shared.Util import queryParser
from Shared.Util import shardQueryHelper
from wsgiref.util import FileWrapper
from hurry.filesize import size
from Shared.Util.bucket import get_client_ip, range_re, RangeFileWrapper
import Main.urls as startUp
import psutil
import json
import os 
import time


"""
    (POST) /api/version/store → Stores a file to an instance
	store(file,filename,override=False,mode=False)
	Responses:
		200 → The file was stored 
"""
def store(request):
    # Block other methods 
    if request.method != "POST": 
        return HttpResponse("Invalid Method -> POST Only",status=400)
    
    # Get the file to store
    fileToStore = request.FILES.get("file")

   
    # Check if everything if requered parameters are true 
    if ("filename" not in request.POST or fileToStore == None): 
        return HttpResponse("Missing Parameters",status=400)
        
    #mode -> private or public file 
    publicAccess = True
    if ("mode" in request.POST):
        mode = request.POST.get("mode").lower()
        if (mode == "private"): publicAccess =False
        elif not (mode == "public" or mode == "private"):
            return HttpResponse("Invalid Mode (Options) -> private | public ",status=400)
    
    # Override file
    if ("override" in request.POST):
        if (request.POST["override"].lower() == "true"):
            result = storeFile(fileToStore,request.POST["filename"],override=True,public=publicAccess)
            #Check if successful
            if (result[0] == True):
                return HttpResponse(result[1],status=200)
            else:
                return HttpResponse(result[1],status=500)

    # Override is not defined or is not true
    result = storeFile(fileToStore,request.POST["filename"],public=publicAccess)

    #Check if successful
    if (result[0] == True):
        return HttpResponse(result[1],status=200)
    else:
        return HttpResponse(result[1],status=409)


"""
    (POST) /api/versions/cache → Caches a file to an instance
	cache(file,fileQueryString) 
	Responses:
		200 → File was cached
		* 
"""
def cache(request):
    #Get the file
    file = request.FILES.get("file")

    #check all parameters present 
    if (file is None or  "fileQueryString" not in request.POST):
        return HttpResponse("Missing Parameters")

    fileIsPublic = True
    #check if there is public parameter
    if ("public" in request.POST):
        #check if public is either true or false
        public = request.POST.get("public").lower()
        if (public != "true") or public != "true": return HttpResponse("Public can either be true or false",status=500)
        fileIsPublic =  bool(public)


    #cache 
    result = cacheFile(file,request.POST.get("fileQueryString"),public=fileIsPublic)

    if (result[0] == True):
        return HttpResponse(result[1],status=200)
    else:
        return HttpResponse(result[1],status=500)

"""
    (GET) /api/version/download → 
	download(queryString)
	Responses:
		200 → The file was stored 
		* 
"""
def download(request,queryString):
    # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    
    #check if the instance is not this one
    if instance != os.environ.get("INSTANCE_NAME"): return shardQueryHelper.retriveFromShard(instance,filename)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

    #check if the file is public
    if storedFile.objects.get(filename=filename).public:
        file_path = f'./Storage/Local/{filename}'
        chunk_size = 15 * (1024 * 1024) #15mb
        filename = os.path.basename(file_path)

        response = StreamingHttpResponse(
            FileWrapper(open(file_path, 'rb'), chunk_size),
            content_type="application/octet-stream"
        )
        response['Content-Length'] = os.path.getsize(file_path)    
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    
    #denied
    return HttpResponse(f"Access denied for file {filename} from instance {instance}",status=401)



"""
    GET) /api/versions/stream → Streams the file as chunks (Perfect for video streaming)
	stream(queryString) 
	Responses:
		200 → File was cached
		* 
"""
def stream(request,queryString):
     # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    
    #check if the instance is not this one
    if instance != os.environ.get("INSTANCE_NAME"): return shardQueryHelper.retriveFromShard(instance,filename)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

    #check if the file is public
    if storedFile.objects.get(filename=filename).public:
        path = f'./Storage/Local/{filename}'
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
    
    #file is private
    return HttpResponse(f"Access denied for file {filename} from instance {instance}",status=401)



"""
    Shard Instance Registration - Makes this instance a gossip instance

    (POST) /api/version/register → 
	headers(SHARD_KEY)
	register(params)
	Responses:
		200 → instance was registered 
		* 
"""
def register(request):
    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    data = json.loads(request.body)

    #check if the instance is already registered
    if registeredInstance.objects.filter(instance_name=data["instance_name"]).exists():
        instance = registeredInstance.objects.get(instance_name=data["instance_name"])
        instance.update(
            get_client_ip(request),
            data["total_memory"],
            data["used_memory"],
            data["stored_files_size"],
            data["cached_files_size"],
            data["stored_files_count"],
            data["cached_files_count"],
            data["uptime"])
    
    #register a new instance
    else:
        instance = registeredInstance(
            ipv4=get_client_ip(request),
            total_memory=data["total_memory"],
            used_memory=data["used_memory"],
            stored_files_size=data["stored_files_size"],
            cached_files_size=data["cached_files_size"],
            instance_name=data["instance_name"],
            stored_files_count=data["stored_files_count"],
            cached_files_count=data["cached_files_count"],
            uptime=data["uptime"]
        )
        instance.save()

    
    # return the list of registered instances
    registeredInstances = [instance.toDictionary() for instance in registeredInstance.objects.all()]
    return HttpResponse(json.dumps(registeredInstances),status=200)

"""
    (GET) /api/version/get_registered_instances → 
	Headers: SHARD-KEY
	Responses:
		200 → List of registered instances 
		*
"""
def registeredInstances(request):

    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    instances = [instance.toDictionary() for instance in registeredInstance.objects.all()]
    
    #Add this instance
    hdd = psutil.disk_usage('/')
    instances.append({
        "ipv4":request.get_host(),
        "total_memory": hdd.total / (2**30),
        "used_memory": hdd.used / (2**30),
        "stored_files_size": storedFile.objects.all().aggregate(Sum('size')).get("size_sum") if storedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0 / (2**30),
        "cached_files_size": cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") if cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0 / (2**30),
        "instance_name": os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
        "stored_files_count": storedFile.objects.all().count(),
        "cached_files_count": cachedFile.objects.all().count(),
        "uptime": time.time() - startUp.startupTime
    })

    #return all instances
    return HttpResponse(
        json.dumps(instances),
        status=200
    )

""""
    (GET) /api/version/health -> returns the health of an instance

"""
def health(request):
    response = {
        "status" : "healthy",
        "uptime" : time.time() - startUp.startupTime,
        "instance" : os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
        "known_instances" : startUp.knownInstances
    }

    return HttpResponse(json.dumps(response))