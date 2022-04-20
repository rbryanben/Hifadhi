from urllib.request import Request
from django.http import HttpResponse
from Shared.decorators import PostOnly
from django.views.decorators.csrf import csrf_exempt
from Shared.storage import store as storeFile, cache as cacheFile


"""
    (POST) /api/version/store → Stores a file to an instance
	store(file,filename,override=False)
	Responses:
		200 → The file was stored 
"""
@csrf_exempt
def store(request):
    # Block other methods 
    if request.method != "POST": 
        return HttpResponse("Invalid Method -> POST Only",status=403)
    
    # Get the file to store
    fileToStore = request.FILES.get("file")

    # Check if everything if requered parameters are true 
    if ("filename" not in request.POST or fileToStore == None): 
        return HttpResponse("Missing Parameters",status=403)
    
    # Override file
    if ("override" in request.POST):
        if (request.POST["override"].lower() == "true"):
            result = storeFile(fileToStore,request.POST["filename"],override=True)
            #Check if successful
            if (result[0] == True):
                return HttpResponse(result[1],status=200)
            else:
                return HttpResponse(result[1],status=500)

    # Override is not defined or is not true
    result = storeFile(fileToStore,request.POST["filename"])

    #Check if successful
    if (result[0] == True):
        HttpResponse(result[1],status=200)
    else:
        return HttpResponse(result[1],status=500)


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

    #cache 
    result = cacheFile(file,request.POST.get("fileQueryString"))

    if (result[0] == True):
        return HttpResponse(result[1],status=200)
    else:
        return HttpResponse(result[1],status=500)