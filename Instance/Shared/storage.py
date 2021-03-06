from fileinput import filename
import psutil

"""
    Shared.py 

    The module Shared/storage.py contains methods for storing and caching files that will be accessed by API. 
    With the following methods.
"""
from .models import filenameTaken, storedFile, cachedFile
import os

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

    #check if there is space for this operation
    hdd = psutil.disk_usage('/')
    free = hdd.total - hdd.used

    if fileSize > free : return [False,"Insufficient Storage"]

    # Do not Override the file
    if (override == False):
        # If the name is taken return error 
        if (filenameTaken(fileName)):
            return [False,"Filename Taken"]
        # If name is not taken create a db record and store the new file
        newfileRecord = storedFile(filename=fileName,public=public,size=fileSize)
        newfileRecord.save()

        with open(f'{localStorage}/{fileName}','wb') as fileToWrite:
            fileToWrite.write(file.read())
        return [True,f'{instanceName}@{fileName}']

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
    invalidationResult = assertInvalidation(file.tell())
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
    Asset Invalidation -> Checks if the memory allocated to cache is not full. If full finds a file remove
"""
def assertInvalidation(fileSize):
    # Return reponse -> tell if any file was removed from cache
    return [True,"Insufficent Storage"]

    