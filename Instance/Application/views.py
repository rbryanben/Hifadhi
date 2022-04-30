from django.http import HttpResponse, StreamingHttpResponse
from Shared.decorators import PostOnly
from Shared.storage import store as storeFile, cache as cacheFile
from Shared.models import storedFile
from Shared.Util import queryParser
from Shared.Util import shardQueryHelper
from wsgiref.util import FileWrapper
import os 


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
        chunk_size = 10000
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





