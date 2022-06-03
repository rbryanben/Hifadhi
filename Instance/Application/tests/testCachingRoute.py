from django.test import TestCase
import os

class testCachingRoute(TestCase):
    
    def setUp(self) -> None:
        self.cacheFile = open("./Storage/Tests/puppy.png","rb")

    def testCachingFileWithoutKey(self):
        self.cacheFile.seek(0,0)
        result = self.client.post("/api/v1/cache",{"fileQueryString":"namib@puppy.png","file" : self.cacheFile},
            HTTP_SHARD_KEY="WRONGKEY")
        self.assertEqual(result.status_code,401)

    def testCachingFileWithKey(self):
        self.cacheFile.seek(0,0)
        result = self.client.post("/api/v1/cache",{"fileQueryString":"namib@puppy.png","file" : self.cacheFile},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(result.status_code,200)