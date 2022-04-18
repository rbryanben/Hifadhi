"""
    Shared.py 

    The module Shared/storage.py contains methods for storing and caching files that will be accessed by API. 
    With the following methods.
"""
from .models import filenameTaken, storedFile, cachedFile
import os

# Vars 
localStorage = './Storage/Local'
cacheStorage = './Storage/Cache'
instanceName = os.environ.get("INSTANCE_NAME")

"""
    store(file,fileName) → Stores a file to the local storage directory.
	Responses: 
		[true,queryString] → File was saved successfully
		[false,error] → File was not saved.
"""
def store(file,fileName,override=False):
    # Do not Override the file
    if (not override):
        # If the name is taken return error 
        if (filenameTaken(fileName)):
            return [False,"Filename Taken"]
        # If name is not taken create a db record and store the new file
        newfileRecord = storedFile(filename=fileName)
        newfileRecord.save()

        with open(f'{localStorage}/{fileName}','wb') as fileToWrite:
            fileToWrite.write(file.read())
        return [True,f'{instanceName}@{fileName}']

    # Override the file 
    if (filenameTaken(fileName)):
        # Create a new record
        storedFile.objects.get(filename=fileName).delete()

    # Create a record
    newFileRecord = storedFile(filename=fileName)
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
def cache(file,fileQueryName):
    #delete any previous records 
    cachedFile.objects.filter(fileQueryName=fileQueryName).delete()

    #create a new record 
    newCachedFileRecord = cachedFile(fileQueryName=fileQueryName)
    newCachedFileRecord.save()

    # Remove any previous files
    try:
        os.remove(f"{cacheStorage}/{fileQueryName}")
    except FileNotFoundError:
        pass

    #check if the memory is full 
    file.read()
    invalidationResult = assertInvalidation(file.tell())
    file.seek(0,0)

    #save the file 
    with open(f"{cacheStorage}/{fileQueryName}","wb") as fileToWrite:
        fileToWrite.write(file.read())

    return [True,invalidationResult]



"""
    Asset Invalidation -> Checks if the memory allocated to cache is not full. If full finds a file remove
"""
def assertInvalidation(fileSize):
    # Return reponse -> tell if any file was removed from cache
    return "File Cached"

    