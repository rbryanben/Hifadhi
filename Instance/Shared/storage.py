from fileinput import filename
from django.db.models import Sum
import psutil
from .models import filenameTaken, storedFile, cachedFile
import os


"""
    Shared.py 

    The module Shared/storage.py contains methods for storing and caching files that will be accessed by API. 
    With the following methods.
"""

# Vars 
localStorage = './Storage/Local'
cacheStorage = './Storage/Temp'
instanceName = os.environ.get("INSTANCE_NAME")

"""
    store(file,fileName) → Stores a file to the local storage directory.
	Responses: 
		[true,queryString] → File was saved successfully
		[false,error] → File was not saved.
"""
def store(file,fileName,override=False,public=True): 
    # Get the file size
    file.read()
    fileSize = file.tell()
    file.seek(0,0)

    # memory management
    memoryValidation = storeMemoryManagement(fileSize)

    # Check if we can store
    if memoryValidation[0] == False:
        return memoryValidation

    # Override is false
    if (override == False):
        # Is file name taken ?
        if (filenameTaken(fileName)):
            return [False,"Filename Taken"]
        # File name is not taken
        newfileRecord = storedFile(filename=fileName,public=public,size=fileSize)
        newfileRecord.save()

        with open(f'{localStorage}/{fileName}','wb') as fileToWrite:
            fileToWrite.write(file.read())
        return [True,f'{instanceName}@{fileName}']

    # Override if true
    if (filenameTaken(fileName)):
        # Create a new record
        prevFileRecord = storedFile.objects.get(filename=fileName)
        prevFileRecord.delete()
    
    # Create a record
    newFileRecord = storedFile(filename=fileName,public=public,size=fileSize)
    newFileRecord.save()
    
    # Write to the file
    with open(f'{localStorage}/{fileName}','wb') as fileToWrite:
        fileToWrite.write(file.read())
    return [True,f'{instanceName}@{fileName}']


"""
    cache(file,fileQueryName) → Caches a file to the cache directory.
	Responses:
		[true,fileQueryName] → File was cached.
		[false,error] → File was not cached.
"""
def cache(file,fileQueryName,public=True,priority=0):
    # Get the file size
    file.read()
    fileSize = file.tell()
    file.seek(0,0)

    #check if there is space for this operation
    hdd = psutil.disk_usage('/')
    free = hdd.total - hdd.used

    if fileSize > free : return [False,"Insufficient Storage"]
    
    #delete any previous records 
    cachedFile.objects.filter(fileQueryName=fileQueryName).delete()

    #create a new record 
    newCachedFileRecord = cachedFile(fileQueryName=fileQueryName,public=public,size=fileSize,priority=priority)
    newCachedFileRecord.save()

    #check if the memory is full 
    file.read()
    invalidationResult = cacheMemoryManagemenent(file.tell())
    file.seek(0,0)

    if invalidationResult[0] != True:
        return [False,invalidationResult[1]]
    
    #save the file 
    with open(f"{cacheStorage}/{fileQueryName}","wb") as fileToWrite:
        fileToWrite.write(file.read())

    return [True,fileQueryName]


"""
    delete(filename) -> Deletes a file from the storage directory
"""
def delete(filename):
    if filename in os.listdir(localStorage):
        try:
            os.remove(f"{localStorage}/{filename}")
        except:
            pass 
        

"""
    delete(cache) -> Deletes a cached file
"""
def deleteAnyCachedFile(filename):
    if filename in os.listdir(cacheStorage):
        try:
            os.remove(f"{cacheStorage}/{filename}") 
        except:
            pass 

"""
    Memory management fot the store option
    -> if the memory is full find cached files to delete if the cache is over 20GB
"""
def storeMemoryManagement(requiredFileSize):
    #get from environ
    cache_size = 40 if "CACHE_LIMIT" not in os.environ else int(os.environ.get("CACHE_LIMIT"))
    disk = psutil.disk_usage('/')
    free = disk.free / 1024 ** 3 
    required = requiredFileSize / 1024 ** 3
    cached = round(cachedFile.objects.all().aggregate(Sum('size')).get("size__sum") / 1024 ** 3 ) if cachedFile.objects.all().count() > 0 else 0 

    # there is no free space
    if free < required:
        # is the cache overlapping
        if cached > cache_size:
            # check if the file to delete is just way to big 
            if cached - required < cache_size:
                return [False,"Wont Be Enough Space For Cache"]
            
            # find a files to delete // Buffer this thing
            allFiles = cachedFile.objects.extra(select={'compute':'reads * (1+priority)'},order_by=('compute',))
            s = 0
            to_delete = [] 

            #find file to delete
            for file in allFiles:
                s += file.size 
                to_delete.append(file)
                #check that it does not eat into cache
                if cached - (s/1024**3) < cache_size:
                    return [False,"Storing file will eat into the cache reserve"] 
                #check if we have met the required size 
                if s >= required + 10 *1024**2:
                    break

            # Delete files
            for file in to_delete:
                deleteAnyCachedFile(file.fileQueryName)
                file.delete()


            return [True,"Store"]
        else:
            return [False,"Insufficent Storage"]
    # there is free space
    else:
        # cache is full -> then all the space is reserved for storage
        if cached >= 20:
            return [True,"Store"]
        # cache is not full -> after storing is there room for cached
        else:
            if free - (cache_size - cached) <= required:
                return [False,"Will consume the cache "]
            else:
                return [True,"Store"]





"""
    Memory management fot the cache option
    -> If the cache is used up and there is no free memory, find cached files to delete
"""
def cacheMemoryManagemenent(requiredfileSize):
    disk = psutil.disk_usage('/')
    free = disk.free

    if free > requiredfileSize:
        return [True,"Store"]
    
    # find a files to delete // Buffer this thing
    allFiles = cachedFile.objects.extra(select={'compute':'reads * (1+priority)'},order_by=('compute',))
    s = 0
    to_delete = [] 

    #find file to delete
    for file in allFiles:
        s += file.size 
        to_delete.append(file)

        #check if we have met the required size 
        if s >= requiredfileSize:
            break

    # Delete files
    for file in to_delete:
        deleteAnyCachedFile(file.fileQueryName)
        file.delete()
        pass

    return [True,"Store"]

            