from django.http import HttpResponse
import os

def shardKeyRequired(func,*args,**kwargs):
    def inner(*args,**kwargs):
        request = args[0]
        #check if the SHARD_KEY is defined in the enviroment variables
        if "SHARD_KEY" not in os.environ: return HttpResponse("SHARD_KEY is not defined in the enviroment variables",status=500)
        
        #check shard key is specified
        if "SHARD-KEY" not in request.headers: return HttpResponse("Missing Header SHARD-KEY ",status=400)

        #check if the SHARD_KEY is correct
        if request.headers["SHARD-KEY"] != os.environ["SHARD_KEY"]: return HttpResponse("Denied",status=401)
        
        return func(*args,**kwargs)
    
    return inner