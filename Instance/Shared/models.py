from django.db import models

"""
    For tracking files stored on the instance
"""
class storedFile(models.Model):
    filename = models.CharField(max_length=512,null=False,primary_key=True)
    stored = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=False,null=False)
    size = models.BigIntegerField(default=0)


def filenameTaken(fileName):
    if storedFile.objects.filter(filename=fileName).exists():
        return True
    return False
        

"""
    For tracking cached files
"""
class cachedFile(models.Model):
    fileQueryName =  models.CharField(max_length=512,null=False,primary_key=True)
    cached = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=True)
    size = models.BigIntegerField(default=0)
    
