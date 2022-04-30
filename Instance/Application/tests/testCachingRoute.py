from django.test import TestCase

class testCachingRoute(TestCase):
    
    def setUp(self) -> None:
        self.cacheFile = open("./Storage/Tests/puppy.png","rb")

    def testCachingFile(self):
        self.cacheFile.seek(0,0)
        result = self.client.post("/api/v1/cache",{"fileQueryString":"namib@puppy.png","file" : self.cacheFile})
        self.assertEqual(result.status_code,200)