from datetime import datetime, timedelta
import pytz
import mimetypes
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from Shared.storage import store as storeFile, cache as cacheFile
from Shared.models import storedFile, registeredInstance, cachedFile, presignedURL, ipv4Access
from django.db.models import Sum
from Shared.Util import queryParser
from Shared.Util import shardQueryHelper
from wsgiref.util import FileWrapper
from Shared.Util.bucket import get_client_ip, range_re, RangeFileWrapper, sha256sum
import uuid
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
@api_view(['POST',])
def store(request):

    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

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
@api_view(['POST',])
def cache(request):
    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)
    
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
@api_view(['GET',])
def download(request,queryString):
    # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    
    #check if the instance is not this one
    if instance != os.environ.get("INSTANCE_NAME"): return shardQueryHelper.retriveFromShard(request,instance,filename,queryString,signature=signature)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

    #method to send the file as to avoid repition
    def sendFile(filename):
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

    #check if the file is public
    if storedFile.objects.get(filename=filename).public: return sendFile(filename)


    #check if the signature is not null and correct 
    if signature != None and presignedURL.objects.filter(signature=signature).exists():

        #check if the signature has not exipred 
        signatureRecord = presignedURL.objects.get(signature=signature)
        
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = signatureRecord.expires
        if (current_time < expiration_time): return sendFile(filename)
       
        #delete the record
        signatureRecord.delete()
    
    #check for ipv4Access
    clientIP = get_client_ip(request)
    if ipv4Access.objects.filter(ipv4=clientIP).exists():
        accessRecord = ipv4Access.objects.get(ipv4=clientIP)
        
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = accessRecord.expires
        if (current_time < expiration_time): return sendFile(filename)
       
        #delete the record
        accessRecord.delete()

    
    #denied
    return HttpResponse(f"Access denied for file {filename} from instance {instance}",status=401)



"""
    (GET) /api/versions/stream → Streams the file as chunks (Perfect for video streaming)
	stream(queryString) 
	Responses:
		200 → File was cached
		* 
"""
@api_view(['GET',])
def stream(request,queryString):
     # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    
    #check if the instance is not this one
    if instance != os.environ.get("INSTANCE_NAME"): return shardQueryHelper.retriveFromShard(request,instance,filename,queryString,signature=signature)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

    #function to stream a file 
    def streamFile(filename):
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

    #check if the file is public
    if storedFile.objects.get(filename=filename).public:
        return streamFile(filename)
    
    #check if the signature is not null and correct 
    if signature != None and presignedURL.objects.filter(signature=signature).exists():

        #check if the signature has not exipred 
        signatureRecord = presignedURL.objects.get(signature=signature)
        
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = signatureRecord.expires
        if (current_time < expiration_time): return streamFile(filename)
       
        #delete the record
        signatureRecord.delete()

    #check for ipv4Access
    clientIP = get_client_ip(request)
    if ipv4Access.objects.filter(ipv4=clientIP).exists():
        accessRecord = ipv4Access.objects.get(ipv4=clientIP)
        
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = accessRecord.expires
        if (current_time < expiration_time): return streamFile(filename)
       
        #delete the record
        accessRecord.delete()

    #Denied
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
@api_view(['POST',])
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

    
   #create dict of instances
    instances = {}
    for instance in registeredInstance.objects.all():
        instances.update(instance.toDictionary())
    

    
    #Add this instance
    hdd = psutil.disk_usage('/')
    instances.update(
        {
          os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED":   {
            "ipv4":request.get_host(),
            "total_memory": hdd.total / (2**30),
            "used_memory": hdd.used / (2**30),
            "stored_files_size": storedFile.objects.all().aggregate(Sum('size')).get("size_sum") if storedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0,
            "cached_files_size": cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") if cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0,
            "instance_name": os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
            "stored_files_count": storedFile.objects.all().count(),
            "cached_files_count": cachedFile.objects.all().count(),
            "uptime": time.time() - startUp.startupTime
            }
        }
    )


    #return all instances
    return HttpResponse(
        json.dumps(instances),
        status=200
    )


"""
    (GET) /api/version/get_registered_instances → 
	Headers: SHARD-KEY
	Responses:
		200 → List of registered instances 
		*
"""
@api_view(['GET',])
def registeredInstances(request):

    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    #create dict of instances
    instances = {}
    for instance in registeredInstance.objects.all():
        instances.update(instance.toDictionary())
    

    
    #Add this instance
    hdd = psutil.disk_usage('/')
    instances.update(
        {
          os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED":   {
            "ipv4":request.get_host(),
            "total_memory": hdd.total / (2**30),
            "used_memory": hdd.used / (2**30),
            "stored_files_size": storedFile.objects.all().aggregate(Sum('size')).get("size_sum") if storedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0,
            "cached_files_size": cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") if cachedFile.objects.all().aggregate(Sum('size')).get("size_sum") != None  else 0,
            "instance_name": os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
            "stored_files_count": storedFile.objects.all().count(),
            "cached_files_count": cachedFile.objects.all().count(),
            "uptime": time.time() - startUp.startupTime
            }
        }
    )


    #return all instances
    return HttpResponse(
        json.dumps(instances),
        status=200
    )

""""
    (GET) /api/version/health -> returns the health of an instance

"""
@api_view(['GET',])
def health(request):
    response = {
        "status" : "healthy",
        "uptime" : time.time() - startUp.startupTime,
        "instance" : os.environ.get("INSTANCE_NAME") if "INSTANCE_NAME" in os.environ else "UNNAMED",
        "known_instances" : startUp.knownInstances
    }

    return HttpResponse(json.dumps(response))

"""
    (POST) /api/version/shard_instance →  Queries the IPv4 of an instance from the gossip instance
	headers(SHARD_KEY)
	shard_instance(instance_name)
	Responses:
		200 → Success
		* 
"""
@api_view(['GET',])
def shardInstance(request):
    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    #check if instance_name is defined 
    if not "instance_name" in request.POST: return HttpResponse("Missing instance_name parameter",status=400)

    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    #check if the instance exists 
    instance_name = request.POST.get("instance_name")
    if not registeredInstance.objects.filter(instance_name=instance_name).exists():
        return HttpResponse(f"Instance {instance_name} not found",status=404)
    
    #return the ipv4 of the instance
    instance = registeredInstance.objects.get(instance_name=instance_name)
    return HttpResponse(instance.ipv4,status=200)


"""
    (GET) /api/version/shard_download/<queryString> → Downloads a file from a shard instance
	headers: 
        SHARD_KEY
	Responses:
		200 → File 
		* 
"""
@api_view(['GET',])
def shardDownload(request,queryString):
    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

    #function to send the file 
    def sendFile(filename,last_updated):
        file_path = f'./Storage/Local/{filename}'
        chunk_size = 80 * (1024 * 1024) #80mb
        filename = os.path.basename(file_path)

        response = StreamingHttpResponse(
            FileWrapper(open(file_path, 'rb'), chunk_size),
            content_type="application/octet-stream"
        )
        response['Content-Length'] = os.path.getsize(file_path)    
        response['Last-Updated'] = last_updated
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response

    #check if the file is public
    storedFileObject = storedFile.objects.get(filename=filename)
    if storedFileObject:
        return sendFile(filename,storedFileObject.lastUpdated())


    # check if the signature is not null and correct 
    if signature != None and presignedURL.objects.filter(signature=signature).exists():

        #check if the signature has not exipred 
        signatureRecord = presignedURL.objects.get(signature=signature)
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = signatureRecord.expires
        print(current_time)
        print(expiration_time)

        if (current_time < expiration_time): return sendFile(filename,storedFileObject.lastUpdated())
       
        #delete the record
        signatureRecord.delete() 

    return HttpResponse(f"Access denied for file {filename} from instance {instance}",status=401)



"""
    (GET) /api/version/pre-sign/queryString → request for a presigned URL 
	headers(SHARD_KEY)
	Parameters:
		duration: Time in seconds
	Responses:
		200 → Success
		* 
"""
@api_view(['GET',])
def preSignedAccess(request,queryString):
    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    #check if the duration is defined 
    if "duration" not in request.GET: return HttpResponse("Value duration is not defined",status=400)

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)
    
    file = storedFile.objects.get(filename=filename)
    duration = request.GET.get("duration")

    #if file is public dont generate simply return the query string
    if file.public: return HttpResponse(queryString,status=200)

    #generate presigned url
    signature = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) 
    while presignedURL.objects.filter(signature=signature).exists():
        signature = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) 
    
    #create a presigned url object
    record = presignedURL(signature=signature,created=datetime.now()+timedelta(seconds=0),file=file,expires=datetime.now()+timedelta(seconds=int(duration)))
    record.save()

    return HttpResponse(f"{queryString}?signature={signature}")


"""    
    (GET) /api/version/ipv4access/<queryString> → requests IPv4 access for a file
        Parameters:
            ipv4: The clients IPv4 address 
            duration: Time in seconds
        Headers: 
            SHARD_KEY
        Responses:
            200 → File 
            * 
"""
@api_view(['GET','DELETE'])
def IPv4Access(request,queryString):

    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    """
        (GET) ipv4Access
    """
    if request.method == "GET":
        #check if the duration is defined 
        if "duration" not in request.GET: return HttpResponse("Value duration is not defined",status=400)

        #check if the ipv4 is defined 
        if "ipv4" not in request.GET: return HttpResponse("Value ipv4 is not defined",status=400)

        # Parse the queryString
        instance, filename = queryParser.parse(queryString)

        #check if the file exists
        if not storedFile.objects.filter(filename=filename).exists(): 
            return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)
        
        file = storedFile.objects.get(filename=filename)
        duration = request.GET.get("duration")
        ipv4 = request.GET.get("ipv4")

        #if file is public dont generate simply return the query string
        if file.public: return HttpResponse(queryString,status=200)

        #create the IPv4 Access 
        access = ipv4Access(ipv4=ipv4,created=datetime.now()+timedelta(seconds=0),
            file=file,expires=datetime.now()+timedelta(seconds=int(duration)))
        access.save()

        return HttpResponse(ipv4)

    """
        (DELETE) ipv4Acess
    """
    if request.method == "DELETE":
        
        #check if the ipv4 is defined 
        if "ipv4" not in request.GET: return HttpResponse("Value ipv4 is not defined",status=400)

        # Parse the queryString
        instance, filename = queryParser.parse(queryString)

        #check if the file exists
        if not storedFile.objects.filter(filename=filename).exists(): 
            return HttpResponse(f"Does not exist {filename} on instance {instance}",status=200)
        

        #delete the access object
        file = storedFile.objects.get(filename=filename)
        ipv4 = request.GET["ipv4"]
        ipv4Access.objects.filter(ipv4=ipv4,file=file).delete()

        return HttpResponse(f"Revoked Access To {queryString} from IP Address {ipv4}")

"""
    (DELETE) /api/version/presign → delete presigned URL access 
	headers(SHARD_KEY)
	Parameters:
		signature
	Responses:
		200 → Success
		* 
"""
@api_view(['DELETE',])
def preSignedAccessDelete(request):

    #check if the SHARD_KEY is defined in the enviroment variables
    if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
    
    #check shard key is specified
    if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

    
    #check if the SHARD_KEY is correct
    if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)

    #check if signature parameter is present in the request
    if "signature" not in request.GET: return HttpResponse("Missing parameter signature",status=400)

    #delete the signature
    signature = request.GET["signature"]
    presignedURL.objects.filter(signature=signature).delete()
    return HttpResponse(signature,status=200)
    
