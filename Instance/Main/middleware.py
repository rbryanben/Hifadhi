"""
    Logs middleware 
"""
from urllib import response
import datetime

class LoggingMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response
    

    def __call__(self,request):
        response = self.get_response(request)
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
        content = response.content if "content" in response else "Stream"
        
        with open("./logs/application.log","a") as logFile:
            logFile.write(f"\n{request.method}\t{request.path}\t{response.status_code}\t{content}\t{current_time}")
        return response