"""
    - Retriving public file (Stream & Download)
    - Retriving private file (Stream & Download)
    - Retriving private file with signature
    - Retriving private file with ipv4 
"""

from urllib import response
from django.test import TestCase
import os

class TestDownloadClass(TestCase):

    def setUp(self) -> None:
        self.testFile = open("./Storage/Tests/dog.jpg","rb")
        
        pass
    

    """
        Retriving public file (Stream & Download)
    """
    def testFileDownloadAndStreamPublic(self):
        #upload a file
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
 
        self.assertEqual(result.status_code,200)
        
        
        #download the file 
        queryString = result.content.decode("utf8") 
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,200)

        # test file streaming
        result = self.client.get(f"/api/v1/stream/{queryString}")
        
        self.assertEqual(result.status_code,200)

        #test downloading a file that does not exists
        tokens = queryString.split("@")
        result = self.client.get(f"/api/v1/download/{tokens[0]}@doesntexist.mp4")
        self.assertEqual(result.status_code,404)


    """
        Retriving private file (Stream & Download)
    """
    def testFileDownloadAndStreamPrivate(self):

        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
 
        self.assertEqual(result.status_code,200)

        queryString = result.content.decode("utf8") 

        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,401)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,401)

    
    """
        Retriving private file with signature
    """
    def testFileDownloadAndStreamWithSignature(self):
        
        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)
        queryString = result.content.decode("utf8") 

        #get signature
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":2}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        signature = result.content.decode('utf8')

        #test download       
        result = self.client.get(f"/api/v1/download/{signature}")
        self.assertEqual(result.status_code,200)

        #test download       
        result = self.client.get(f"/api/v1/stream/{signature}")
        self.assertEqual(result.status_code,200)
        

    """
        Retriving private file with ipv4 
    """
    def testRetrivingPrivateFileWithIPv4(self):

        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)
        queryString = result.content.decode("utf8") 

        #get IPv4 access 
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":2
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,200)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,200)
        



    
