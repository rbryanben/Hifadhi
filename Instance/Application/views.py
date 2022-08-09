from datetime import datetime, timedelta
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from Shared.storage import cacheMemoryManagemenent, store as storeFile, delete, deleteAnyCachedFile
from Shared.models import storedFile, registeredInstance, cachedFile, presignedURL, ipv4Access
from django.db.models import Sum
from Shared.Util import queryParser, shardQueryHelper
from Shared.decorators import shardKeyRequired
from wsgiref.util import FileWrapper
from Shared.Util.bucket import get_client_ip, range_re, RangeFileWrapper, sendCacheRequest
import Main.urls as startUp
import os,json,time,requests,psutil,uuid,pytz,mimetypes
from Shared.Util.bucket import range_re, RangeFileWrapper, registerToInstance
import Main.urls as Startup
from concurrent.futures import ThreadPoolExecutor



@api_view(['GET',])
def landingPage(request):
    context = {
        "instance_name" : os.environ.get("INSTANCE_NAME"),
        "host_ip" : request.get_host(),
        "client_ip" : get_client_ip(request)
    }

    return render(request,"Application/landing.html",context)
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
    (POST) /api/version/cache → cache a file on that instance
	headers(SHARD_KEY)
	Parameters:
		priority: real number 1 to 2^32-1
		query_string: file cache query string
	Responses:
		200 → Success
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
 
    #check if priority is present
    if "priority" not in request.POST: return HttpResponse("Missing parameter priority",status=400)
    priority = request.POST.get("priority")
    #check if the query string is defined 
    if "query_string" not in request.POST: return HttpResponse("Missing parameter query_string",status=400)
    queryString = request.POST.get("query_string")
    #parse query string 
    instance, filename = queryParser.parse(queryString)
    
    #check if this is the instance, cause you can download a file you own 
    if os.environ.get("INSTANCE_NAME") == instance: return HttpResponse("Owns the file")
 

    #check if instance is in shard 
    if "GOSSIP_INSTANCE" not in os.environ: return HttpResponse("Shard Retrival Failure",status=500)

    #function to get the IPv4 from list returned on registration
    def getInstanceIpv4(instance, Startup):
        if instance in Startup.knownInstances:
            return Startup.knownInstances.get(instance)['ipv4']
        return None


    #get the instance ipv4
    instanceIPv4 = getInstanceIpv4(instance,Startup)
    
    #if instanceIPv4 is None then re-register to get an updated list of instances 
    if instanceIPv4 == None:
            gossip_instance_ip = os.environ.get("GOSSIP_INSTANCE")
            registerToInstance(gossip_instance_ip)

    #get the IPv4 from the updated list
    instanceIPv4 = getInstanceIpv4(instance,Startup)
    
    # if instanceIPv4 is still Null update that the instance could not be found in the Shard
    if instanceIPv4 == None:
        return HttpResponse(f"Could not find instance {instance}",status=404)

    # get the file
    try:
        stream = requests.get(f"http://{instanceIPv4}/api/v1/shard_download/{queryString}?internal=true",stream=True,headers={"SHARD-KEY":os.environ.get("SHARD_KEY")})
        
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
                cachedFileRecord = cachedFile(fileQueryName=queryString,priority=priority,public=False,size=int(stream.headers.get("content-length")))
                cachedFileRecord.save()

        #failed to get the file with 404 
        #   -> delete the file 
        if stream.status_code == 404:
            deleteAnyCachedFile(queryString)

        #failed to get the file 
        if stream.status_code != 200: return HttpResponse(stream.text,status=stream.status_code)
            
        #got the file
        stream.raise_for_status()
        
        #cache record does not exist then write the file 
        if not cachedFile.objects.filter(fileQueryName=queryString).exists():
            writeFile(queryString,stream)
        
        
        cacheRecord = cachedFile.objects.get(fileQueryName=queryString)

        #but if file exists in the cache
        #check if the cached file is still valid by checking if the cached dates match
        cachedFileTimestamp = cacheRecord.lastUpdated()
        receivedFileTimestamp = int(stream.headers.get("last-updated"))

        #if hashes do not match rewrite the file and send the file 
        if receivedFileTimestamp > cachedFileTimestamp : writeFile(queryString,stream)

        #Update the priority 
        cacheRecord.priority = priority
        cacheRecord.save()

        #close the stream  
        stream.close() 
    except:
        return HttpResponse(f"Connection to instance {instance} failed")


    return HttpResponse(f"Cached file {queryString} on instance {os.environ.get('INSTANCE_NAME')}")

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

    #file to send after checking authentication
    file = storedFile.objects.get(filename=filename)

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
    if file.public: return sendFile(filename)


    #check if the signature is not null and correct 
    if signature != None and presignedURL.objects.filter(signature=signature,file=file).exists():

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
    if ipv4Access.objects.filter(ipv4=clientIP,file=file).exists():
        accessRecord = ipv4Access.objects.get(ipv4=clientIP,file=file)
        
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

    #The file to stream
    file = storedFile.objects.get(filename=filename)

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
    
    #check if the signature is not null and correct 1
    if signature != None and presignedURL.objects.filter(signature=signature,file=file).exists():

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
    if ipv4Access.objects.filter(ipv4=clientIP,file=file).exists():
        accessRecord = ipv4Access.objects.get(ipv4=clientIP,file=file)
        
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
    (GET) /api/version/shard_download/<queryString> → Used to return files for other instances 
	Parameters:
		signature
		check → Used to check if a file exist. Will only return the response not the file
		internal → Bypass any access control checks : used for internal downloads 
	Headers: 
		SHARD_KEY
	Responses:
		200 → File 
		* 
"""
@api_view(['GET',])
@shardKeyRequired
def shardDownload(request,queryString):
    clientIp = request.headers.get("Http-X-Forwarded-For")

    # Get Signature
    signature = request.GET.get("signature") if "signature" in request.GET else None

    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

    #check if the file exists
    if not storedFile.objects.filter(filename=filename).exists(): 
        return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)
    
    file = storedFile.objects.get(filename=filename)

    #check parameter is present
    if "check" in request.GET:
        return HttpResponse(f"File {filename} exists on instance {instance}",status=200)

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
    if storedFileObject.public:
        return sendFile(filename,storedFileObject.lastUpdated())

    #check if internal is defined
    if "internal" in request.GET: return sendFile(filename,storedFileObject.lastUpdated())

    # check if the signature is not null and correct 
    if signature != None and presignedURL.objects.filter(signature=signature,file=file).exists():

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

    #check if there is ipv4 access to that file
    if ipv4Access.objects.filter(ipv4=clientIp,file=file).exists():
        accessRecord = ipv4Access.objects.filter(ipv4=clientIp,file=file)[0]
        
        utc = pytz.UTC
        current_time = datetime.now().replace(tzinfo=utc)
        expiration_time = accessRecord.expires
        if (current_time < expiration_time): return sendFile(filename,storedFileObject.lastUpdated())
       
        #delete the record
        accessRecord.delete()

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
@shardKeyRequired
def preSignedAccess(request,queryString):
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
@shardKeyRequired
def IPv4Access(request,queryString):

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
        if file.public: return HttpResponse(ipv4,status=200)

        #create the IPv4 Access after deleting all previous one 
        ipv4Access.objects.filter(ipv4=ipv4,file=file).delete()
        access = ipv4Access(ipv4=ipv4,created=datetime.now()+timedelta(seconds=0),
            file=file,expires=datetime.now()+timedelta(seconds=int(duration)))
        access.save()

        return HttpResponse(ipv4,status=200)

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
    

"""
    (POST) /api/version/shard_cache → (Gossip) cache a file on all registered instances 
	headers(SHARD_KEY)
	Parameters:
		priority: real number 1 to 2^32-1
		query_string: file cache query string
	Responses:
		200 → Success
		* 
"""
@api_view(['POST',])
@shardKeyRequired
def shardCache(request):
    #check if all parameters are defined 
    if "priority" not in request.POST: return HttpResponse("Missing parameter priority",status=400)
    if "query_string" not in request.POST: return HttpResponse("Missing parameter query_string", status=400)
    priority,queryString = int(request.POST.get("priority")),request.POST.get("query_string")
   
    # Parse the queryString
    instance, filename = queryParser.parse(queryString)

   
    # Instance is this one 
    if os.environ.get("INSTANCE_NAME") == instance:
        #check if the file exists
        if not storedFile.objects.filter(filename=filename).exists():
            return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)
    # Instance is not this one
    else:
        #check if the instance is registered
        if not registeredInstance.objects.filter(instance_name=instance).exists():
            return HttpResponse(f"Could not find instance {instance}",status=404)

        #check if the file exists on that instance 
        instanceIPv4 = registeredInstance.objects.get(instance_name=instance).ipv4
        try:
            with requests.get(f"http://{instanceIPv4}/api/v1/shard_download/{queryString}?check=true",headers={"SHARD-KEY":os.environ.get("SHARD_KEY")}) as resp:
                if resp.status_code != 200: return HttpResponse(resp.text,resp.status_code)
        except:
            return HttpResponse(f"Network error finding instance",status=500)

    # Send request to cache the file on registered instances
    cachedOn = []

    #cache on other instances (Turn this to async)
    instances = [{
        "ipv4": instance.ipv4,
        "priority" : priority,
        "query_string": queryString,
        "name" : instance.instance_name
    } for instance in registeredInstance.objects.all()]

    with ThreadPoolExecutor() as ex:
        res = ex.map(sendCacheRequest,instances)
        for result in res: 
            cachedOn.append(result)


    return HttpResponse(json.dumps(cachedOn))

"""
    (POST) /api/version/delete → delete file 
	    headers(SHARD_KEY)
        Parameters:
            query_string: file cache query string
        Responses:
            200 → Success (Query String Attached)
            * 
"""
@api_view(['POST',])
@shardKeyRequired
def deleteFile(request):
    # Check if query string is defined
    if "query_string" not in request.POST: return HttpResponse("Missing parameter query_string",status=400)

    # Parse the query string
    queryString = request.POST.get("query_string")
    instance, filename = queryParser.parse(queryString)


    # Instance is this one
    if os.environ.get("INSTANCE_NAME") == instance:
        #Check if the file exists 
        if not storedFile.objects.filter(filename=filename).exists():
            return HttpResponse(f"Does not exist {filename} on instance {instance}",status=404)

        # Delete the file
        delete(filename)

        # Delete the record 
        storedFile.objects.filter(filename=filename).delete()

        # Instance not in shard and is not gossip
        if registeredInstance.objects.all().count() == 0 and (Startup.registeredOnGossip == [] or Startup.registeredOnGossip[0] == False):
            return HttpResponse(queryString)
        
        # Delete on other instances 
        return shardQueryHelper.deleteCachedFileOnOtherInstances(queryString)
    
    # Instance is not this one 
    
    # Delete cached file if any 
    deleteAnyCachedFile(queryString)

    # Remove any cached files records 
    cachedFile.objects.filter(fileQueryName=queryString).delete()

    return shardQueryHelper.deleteFileOnAnotherInstance(queryString,instance)

"""
    (POST) /api/version/delete_cache → deleted a file from the cache
	headers(SHARD_KEY)
	Parameters:
		query_string: file cache query string
	Responses:
		200 → Success
		* 
"""
@api_view(['POST',])
@shardKeyRequired
def deleteCached(request):
    # Check if query string is defined
    if "query_string" not in request.POST: return HttpResponse("Missing parameter query_string",status=400)

    queryString = request.POST.get("query_string")

    # Remove any cached files records 
    cachedFile.objects.filter(fileQueryName=queryString).delete()

    # Remove any file if cached
    deleteAnyCachedFile(queryString)

    return HttpResponse(queryString,status=200)

"""
    (GET) /api/version/information → 
	headers(SHARD_KEY)
	Parameters:
		count: The information retrieval count
	Responses:
		200 → Success
		* 
"""
@shardKeyRequired
@api_view(['GET',])
def information(request):
    hdd = psutil.disk_usage('/')
    data = {
            "name" : os.environ.get("INSTANCE_NAME"),
            "uptime" : time.time() - startUp.startupTime,
            "total_memory": hdd.total,
            "free_memory" : hdd.total - hdd.used,
            "cached_memory": cachedFile.objects.all().aggregate(Sum('size')).get("size__sum"),
            "stored": storedFile.objects.all().aggregate(Sum('size')).get("size__sum"),
            "cached_files": [
                record.toDictionary() for record in cachedFile.objects.all()
            ],
            "stored_files": [
                record.toDictionary() for record in storedFile.objects.all()
            ]
        }

    return HttpResponse(json.dumps(data),status=200)


"""
    (GET) /api/version/logs → 
	headers(SHARD_KEY)
	Parameters:
		count: The information retrieval count
	Responses:
		200 → Success
		* 
"""
@shardKeyRequired
@api_view(['GET','DELETE',])
def logs(request):
    if request.method == "GET":
        with open("./logs/application.log","rb") as logFile:
                logs = logFile.read()
        
        return HttpResponse(logs,status=200)
    else:
        with open("./logs/application.log","w") as logFile:
            logFile.flush()
        return HttpResponse("Flushed log file",status=200)