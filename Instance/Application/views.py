from urllib.request import Request
from django.http import HttpResponse
from Shared.decorators import PostOnly
from django.views.decorators.csrf import csrf_exempt
from Shared.storage import store as storeFile, cache as cacheFile


"""
    (POST) /api/version/store → Stores a file to an instance
	store(file,filename,override=False,mode=False)
	Responses:
		200 → The file was stored 
"""
@csrf_exempt
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
@csrf_exempt
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