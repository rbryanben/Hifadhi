from urllib import response
from django.test import TestCase

class TestDownloadClass(TestCase):

    def setUp(self) -> None:
        pass

    def testFileDownloadAndStream(self):
        self.testFile = open("./Storage/Tests/dog.jpg","rb")

        #upload a file
        self.testFile.seek(0,0)
        result = self.client.post("/api/v1/store",{"file":self.testFile,"filename":"dog.jpg"})
        self.assertEqual(result.status_code,200)
        
        #download the file 
        queryString = result.content.decode("utf8") 
        result = self.client.get(f"/api/v1/download/{queryString}?signature=1XJ32DO7OP23DNDJ32")
        
        self.assertEqual(result.status_code,200)

        # test file streaming
        result = self.client.get(f"/api/v1/stream/{queryString}?signature=1XJ32DO7OP23DNDJ32")
        
        self.assertEqual(result.status_code,200)

        #test downloading a file that does not exists
        tokens = queryString.split("@")
        result = self.client.get(f"/api/v1/download/{tokens[0]}@doesntexist.mp4")
        self.assertEqual(result.status_code,404)


    
