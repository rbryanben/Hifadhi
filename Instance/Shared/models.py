from datetime import datetime
from django.db import models
import os 

"""
    For tracking files stored on the instance
"""
class storedFile(models.Model):
    filename = models.CharField(max_length=512,null=False,primary_key=True)
    stored = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=False,null=False)
    size = models.BigIntegerField(default=0)

    @property
    def queryString(self):
        return os.environ.get("INSTANCE_NAME") + "@"+self.filename if os.environ.get("INSTANCE_NAME") else f"None@{self.filename}"

    def toDictionary(self):
        return {
            "filename" : self.filename,
            "stored" : self.stored.strftime("%Y%m%d%H%M%S"),
            "public" : self.public,
            "size"  : self.size,
            "queryString" : self.queryString,
        }

    """
        Returns datetime last updated
    """
    def lastUpdated(self):
        return self.stored.strftime("%Y%m%d%H%M%S") 


def filenameTaken(fileName):
    if storedFile.objects.filter(filename=fileName).exists():
        return True
    return False


"""
    Instance registered 

    Keeps the following attributes ipv4 total_memory used_memory stored_files_size cached_files_size instance_name stored_files_count cached_files_count uptime
"""
class registeredInstance(models.Model):
    ipv4 = models.CharField(max_length=15,null=False)
    total_memory = models.BigIntegerField(default=0)
    used_memory = models.BigIntegerField(default=0)
    stored_files_size = models.BigIntegerField(default=0)
    cached_files_size = models.BigIntegerField(default=0)
    instance_name = models.CharField(max_length=512,null=False,primary_key=True)
    stored_files_count = models.IntegerField(default=0)
    cached_files_count = models.IntegerField(default=0)
    uptime = models.BigIntegerField(default=0)
    last_health_check = models.DateTimeField(auto_now=True)
    healthy  = models.BooleanField(default=True)


    def update(self,ipv4,total_memory,used_memory,stored_files_size,
        cached_files_size,stored_files_count,cached_files_count,
        uptime):
        self.ipv4 = ipv4
        self.total_memory = total_memory
        self.used_memory = used_memory
        self.stored_files_size = stored_files_size
        self.cached_files_size = cached_files_size
        self.stored_files_count = stored_files_count
        self.cached_files_count = cached_files_count
        self.uptime = uptime
        self.last_health_check = datetime.now()
        self.healthy = True
        self.save() 
    
    def toDictionary(self):
        return { 
            self.instance_name: {
                "ipv4" : self.ipv4,
                "total_memory" : self.total_memory,
                "used_memory" : self.used_memory,
                "stored_files_size" : self.stored_files_size,
                "cached_files_size" : self.cached_files_size,
                "instance_name" : self.instance_name,
                "stored_files_count" : self.stored_files_count,
                "cached_files_count" : self.cached_files_count,
                "uptime" : self.uptime,
                "healthy" : self.healthy
            }
        }
        

"""
    For tracking cached files
"""
class cachedFile(models.Model):
    fileQueryName =  models.CharField(max_length=512,null=False,primary_key=True)
    cached = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=True)
    size = models.BigIntegerField(default=0)
    priority = models.IntegerField(default=0)
    reads = models.BigIntegerField(default=1)

    """
        Returns datetime timestamp cached
    """
    def lastUpdated(self):
        return int(self.cached.strftime("%Y%m%d%H%M%S"))
    
    """
        Updates the file 
    """
    def update(self,size):
        self.size = size
        self.cached = datetime.now()
        self.save()

    """
        updates the no of reads
    """
    def appendReads(self):
        self.reads += 1
        self.cached = self.cached
        self.save(update_fields=['reads'])

    """
        converts toDictionary
    """
    def toDictionary(self):
        return {
            "file_query_name" : self.fileQueryName,
            "stored" : self.cached.strftime("%Y%m%d%H%M%S"),
            "public" : self.public,
            "size" : self.size
        }


"""
    Presigned URLs 
"""
class presignedURL(models.Model):
    signature = models.CharField(max_length=256,primary_key=True,null=False)
    expires = models.DateTimeField(null=False)
    created = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(storedFile,on_delete=models.CASCADE)


"""
    ipv4Access
"""
class ipv4Access(models.Model):
    ipv4 = models.CharField(max_length=25,null=False)
    expires = models.DateTimeField(null=False)
    created = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(storedFile,on_delete=models.CASCADE)



