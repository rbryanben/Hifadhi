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
    - Delete signature
    - Delete ipv4 access 
"""
from django.test import TestCase
import os

class testAccessControl(TestCase):
    def setUp(self) -> None:
        #file to upload
        self.file = open("./Storage/Tests/puppy.png","rb")

        #upload the file
        result = self.client.post("/api/v1/store",{"file":self.file,"filename":"rex_the_dog.jpg","mode":"private","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        return

    def testObtainingSignatureWithoutKey(self):
        result = self.client.get(f"/api/v1/presign/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60})
        self.assertEqual(result.status_code,400) #Bad Request

    def testObtainingIpv4WithoutKey(self):
        result = self.client.get(f"/api/v1/ipv4access/{os.environ.get('INSTANCE_NAME')}@rex_the_dog.jpg",{"duration":60
            ,"ipv4":"127.0.0.1"})
        self.assertEqual(result.status_code,400) #Bad Request
    

        

    

