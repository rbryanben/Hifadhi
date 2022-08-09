"""
    - Obtain signature without SHARD-KEY
    - Obtain ipv4 without SHARD-KEY
    - Obtain ipv4 and signature with missing parameters
    - Obtain signature with invalid SHARD-KEY
    - Obtain ipv4 with invalid SHARD-KEY
    - Obtain Signature for public file 
    - Obtain Signature for private file
    - Obtain ipv4 access for public file 
    - Obtain ipv4 access for private file 
    - Delete signature without key
    - Delete signature with invalid Key
    - Delete signature with missing signature parameter
    - Delete signature
    - Delete ipv4 access without key
    - Delete ipv4 access with invalid key
    - Delete ipv4 with missing parameters
    - Delete ipv4 access
    - One to one signature access 
    - One to one ipv4 access 
"""
from unittest import result
from django.test import TestCase
import os

class testAccessControl(TestCase):
    def setUp(self) -> None:
        #file to upload
        self.file = open("./Storage/Tests/puppy.png","rb")

        #upload the file as private 
        result = self.client.post("/api/v1/store",{"file":self.file,"filename":"rex_the_dog.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,200)

        #upload a second private file for cross checking One to One access 
        result = self.client.post("/api/v1/store",{"file":self.file,"filename":"rex_the_dog_second.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)

        #upload a public file
        result = self.client.post("/api/v1/store",{"file":self.file,"filename":"rex_the_dog_public.jpg","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))    
        self.assertEqual(result.status_code,200)
        return

    """
        Obtain signature without SHARD-KEY
    """
    def testObtainingSignatureWithoutKey(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60})
        self.assertEqual(result.status_code,400) #Bad Request

    """
        Obtain ipv4 without SHARD-KEY
    """
    def testObtainingIpv4WithoutKey(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"})
        self.assertEqual(result.status_code,400) #Bad Request
    
    """
        Obtain ipv4 and signature with missing parameters
    """
    def testObatiningAccessWithMissingParameters(self):
        #Signature
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg")
        self.assertEqual(result.status_code,400) #Bad Request
        
        #Ipv4 
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60})
        self.assertEqual(result.status_code,400) #Bad Request
    
    """
       Test Obtain signature with invalid SHARD-KEY 
    """
    def testObtainingSignatureInvalidKey(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(result.status_code,401) #Denied
    
    
    """
        Test Obtain ipv4 with invalid SHARD-KEY
    """
    def testObtainingIpv4InvalidKey(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(result.status_code,401) #Denied

    """
        Test Obtain Signature for public file 
    """
    def testObtainingSignaturePublicFile(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog_public.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(f"{os.environ.get('INSTANCE_NAME')}@rex_the_dog_public.jpg",result.content.decode("utf8")) #200 Without Signature
    
    """
        Obtain Signature for private file
    """
    def testObtainingSignaturePrivateFile(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertNotEqual(f"{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",result.content.decode("utf8")) #200 Without Signature
    
    """
        Obtain ipv4 access for public file 
    """
    def testObtainingIpv4PublicFile(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog_public.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

    """
        Obtain ipv4 access for private file
    """
    def testObtainingIpv4PrivateFile(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

    """
        Delete signature Without Key
    """
    def testDeleteSignatureWithoutKey(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        tokens = result.content.decode("utf8").split("=")

        #delete
        result = self.client.delete(f"http://localhost:8000/api/v1/presign?signature={tokens[1]}")
        self.assertEqual(result.status_code,400)

    """
        Delete signature Invalid Key
    """
    def testDeleteSignatureInvalidKey(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        tokens = result.content.decode("utf8").split("=")

        #delete
        result = self.client.delete(f"http://localhost:8000/api/v1/presign?signature={tokens[1]}",HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(result.status_code,401)

    """
        Delete signature Missing Parameters
    """
    def testDeleteSignatureMissingParameter(self):
        #delete
        result = self.client.delete(f"http://localhost:8000/api/v1/presign",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,400)

    """
        Delete signature
    """
    def testDeleteSignature(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        tokens = result.content.decode("utf8").split("=")

        #delete
        result = self.client.delete(f"http://localhost:8000/api/v1/presign?signature={tokens[1]}",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,200)

    """
        Delete ipv4 access without key
    """
    def testDeleteIpv4AccessWithoutKey(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

        #delete
        result = self.client.delete(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"})

        self.assertEqual(result.status_code,400)

    """
        Delete ipv4 access with invalid key
    """
    def testDeleteIpv4InvalidKey(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

        #delete
        result = self.client.delete(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY="INVALDKEY")

        self.assertEqual(result.status_code,401)

    """
        Delete ipv4 with missing parameters
    """
    def testDeleteIPv4MissingParameters(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

        #delete
        result = self.client.delete(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,400)
    
    """5
        Delete ipv4 access
    """
    def testDeleteIPv4(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

        #delete
        result = self.client.delete(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",
            body={"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        #self.assertEqual(result.status_code,200)

    """
        One to one signature access 
    """
    def testOneToOneSignatureAccess(self):
        #generate sigature for the first file  
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60}
            ,HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertEqual(result.status_code,200)
        
        #Signature
        fileOneSignature = result.content.decode("utf8")
        signatureOnly = fileOneSignature.split("?")[1]

        #check the signature works 
        signatureWorksResult = self.client.get(f'/api/v1/stream/{os.environ.get("INSTANCE_NAME")}@rex_the_dog.jpg?{signatureOnly}')
        self.assertEqual(signatureWorksResult.status_code,200)

        signatureWorksResult = self.client.get(f"/api/v1/stream/{os.environ.get('INSTANCE_NAME')}@rex_the_dog_second.jpg?{signatureOnly}")
        self.assertEqual(signatureWorksResult.status_code,401)

    """
        One to one ipv4 access 
    """
    def testOneToOneIPv4Access(self):
        #generate IPv4 access for file one 
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
            
        self.assertEqual(result.content.decode("utf8"),"127.0.0.1") #200

        #check if ipv4 access is working for the first file
        fileOneQueryResult = self.client.get(f"/api/v1/download/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg")
        self.assertEqual(fileOneQueryResult.status_code,200)

        #check if ipv4 acces is not working for the second file 
        fileOneQueryResult = self.client.get(f"/api/v1/download/{os.environ.get('INSTANCE_NAME')}@rex_the_dog_second.jpg")
        self.assertEqual(fileOneQueryResult.status_code,401)

