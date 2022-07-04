from doctest import testfile
from fileinput import filename
from django.test import TestCase
from Shared.models import cachedFile, storedFile
import os

"""
    Test class to test deletion of a file 

    List:
        - Test invalid shard key 
        - Test valid shard key
        - Test missing query string 
        - Test file does not exist
        - Test Deletion API
"""
class testDeletion(TestCase):
    def setUp(self):
        # Upload a file
        self.testFile = open("./Storage/Tests/dog.jpg","rb")
        self.testFilename = "dog_to_delete.jpg"
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":self.testFilename},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        self.assertEqual(result.status_code,200)

    """
        Test invalid shard key 
    """
    def testInvalidKey(self):
        res = self.client.post("/api/v1/delete",HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(res.status_code,401)

    """
        Test valid shard key
    """
    def testValidKey(self):
        res = self.client.post("/api/v1/delete",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(res.status_code,400)

    """
       Test missing query string  
    """
    def testMissingParams(self):
        res = self.client.post("/api/v1/delete",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(res.status_code,400)

    """
       Test missing query string  
    """
    def testFileDoesNotExist(self):
        queryString = f"{os.environ.get('INSTANCE_NAME')}@does_not_exist.at_all"
        res = self.client.post("/api/v1/delete",{"query_string":queryString},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(res.status_code,404)

    """
       Test deleting a file 
    """
    def testDeletion(self):
        queryString = f"{os.environ.get('INSTANCE_NAME')}@{self.testFilename}"
        res = self.client.post("/api/v1/delete",{"query_string":queryString},HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(storedFile.objects.filter(filename=self.testFilename).count(),0)
        self.assertEqual(res.status_code,200)

    """
        Test deletion API
    """
    def testDeletionAPI(self):
        self.testFile.seek(0,0) #reset file 
        # Add the file to the cache directory 
        with open("./Storage/Temp/Uranus@dog.jpg","wb") as file:
            file.write(self.testFile.read())

        # Add the cached file record 
        cachedFileRecord = cachedFile(fileQueryName="Uranus@dog.jpg")
        cachedFileRecord.save()

        # Test API
        resp = self.client.post("/api/v1/delete_cache",{"query_string":"Uranus@dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        self.assertEqual(resp.status_code,200)




    