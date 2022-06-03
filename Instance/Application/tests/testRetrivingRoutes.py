"""
    - Retriving public file (Stream & Download)
    - Retriving private file (Stream & Download)
    - Retriving private file with signature
    - Retriving private file with ipv4 
    - Retriving private file deleted signature 
    - Retriving private file expired signature
    - Retriving private file deleted ipv4 access
    - Retriving private file expired ipv4 access
"""

from urllib import response
from django.test import TestCase
import os, time

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

    """
        Retriving private file deleted signature 
    """
    def testRetrivingPrivateFileAfterSignatureDelete(self):

        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)


        #get presigned URL 
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":2}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        presignedURL_ = result.content.decode('utf8')

        #test download (200)    
        result = self.client.get(f"/api/v1/download/{presignedURL_}")
        self.assertEqual(result.status_code,200)

        #test stream  (200)
        result = self.client.get(f"/api/v1/stream/{presignedURL_}")
        self.assertEqual(result.status_code,200)


        #delete the signature
        tokens = presignedURL_.split("=")

        #delete
        result = self.client.delete(f"http://localhost:8000/api/v1/presign?signature={tokens[1]}",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,200)

        #test download (200)    
        result = self.client.get(f"/api/v1/download/{presignedURL_}")
        self.assertEqual(result.status_code,401)

        #test stream  (200)
        result = self.client.get(f"/api/v1/stream/{presignedURL_}")
        self.assertEqual(result.status_code,401)
        
    """
       Retriving private file expired signature 
    """
    def testRetrivalSignatureExpired(self):

        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)


        #get presigned URL 
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":1}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        presignedURL_ = result.content.decode('utf8')

        #test download (200)    
        result = self.client.get(f"/api/v1/download/{presignedURL_}")
        self.assertEqual(result.status_code,200)

        #test stream  (200)
        result = self.client.get(f"/api/v1/stream/{presignedURL_}")
        self.assertEqual(result.status_code,200)

        #sleep for 2 seconds
        time.sleep(1)

        #test download (200)    
        result = self.client.get(f"/api/v1/download/{presignedURL_}")
        self.assertEqual(result.status_code,401)

        #test stream  (200)
        result = self.client.get(f"/api/v1/stream/{presignedURL_}")
        self.assertEqual(result.status_code,401)


    """
        Retriving private file deleted ipv4 access
    """
    def testRetrivingDeletedIPv4Access(self):

        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)
        queryString = result.content.decode("utf8") 

        #get IPv4 access 
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":1
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,200)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,200)

        #delete the ipv4 Access 
        result = self.client.delete(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":1
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

    
       
        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,200)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,200)

    """
        Retriving private file expired ipv4 access
    """
    def testRetrivalExpiredIPv4(self):
        #upload private file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"rex_private.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)
        queryString = result.content.decode("utf8") 

        #get IPv4 access 
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_private.jpg",{"duration":1
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,200)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,200)

        time.sleep(1)
           
        #test download       
        result = self.client.get(f"/api/v1/download/{queryString}")
        self.assertEqual(result.status_code,401)

        #test stream
        result = self.client.get(f"/api/v1/stream/{queryString}")
        self.assertEqual(result.status_code,401)