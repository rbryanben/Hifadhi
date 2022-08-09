from fileinput import filename
from unittest import result
from django.test import TestCase
from Shared.models import storedFile
import os

# Create your tests here.
"""
    Tests the /api/version/store url
"""
class TestStoreRoute(TestCase):

    def setUp(self) -> None:
        self.testFile = open("./Storage/Tests/dog.jpg","rb")
        self.overrideFile = open("./Storage/Tests/puppy.png","rb")

        #get the file size 
        self.testFileSize = self.testFile.tell()


    def testStoringPublicFile(self):
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,200)
        self.assertIsNotNone(storedFile.objects.get(filename="dog.jpg"))


    def testStoringFileThatExists(self):
        # First file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        # Second file with the same name
        self.overrideFile.seek(0,0)
        self.assertGreater(storedFile.objects.all().count(),0)

        # Check if conflict is raised
        result = self.client.post("/api/v1/store",{"file":self.overrideFile,"filename":"dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,409)


    def testStoringFileWithOverride(self):
        # First file 
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        # Override File
        self.overrideFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.overrideFile,"filename":"dog.jpg","override":"true"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        
        self.assertEqual(result.status_code,200)


    def tearDown(self) -> None:
        self.testFile.close()
        self.overrideFile.close()