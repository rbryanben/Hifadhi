from wsgiref import headers
from django.test import TestCase
import os , json 

class testInfomationRetrival(TestCase):
    def setUp(self) -> None:
        #upload 3 files
        self.file1 = open("./Storage/Tests/dog.jpg","rb")
        self.file2 = open("./Storage/Tests/dog.jpg","rb")
        self.file3 = open("./Storage/Tests/dog.jpg","rb")

    def testInfo(self):
        result1 = self.client.post("/api/v1/store",{"file":self.file1,"filename":"file1.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        result2 = self.client.post("/api/v1/store",{"file":self.file2,"filename":"file2.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        result3 = self.client.post("/api/v1/store",{"file":self.file2,"filename":"file3.jpg"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        self.assertTrue(result1.status_code == 200)
        self.assertTrue(result2.status_code == 200)
        self.assertTrue(result3.status_code == 200)

        #get infomation
        getInformationResponse = self.client.get("/api/v1/information",HTTP_SHARD_KEY=os.environ.get('SHARD_KEY'))
        print(getInformationResponse.content)
        
        # Assertions
        self.assertEqual(getInformationResponse.status_code,200)

        resultDict = json.loads(getInformationResponse.content.decode("utf8"))

        self.assertEqual(resultDict.get("name"),os.environ.get("INSTANCE_NAME"))
        self.assertTrue(resultDict.get("uptime") >= 0)
        self.assertTrue(resultDict.get("total_memory") >= 0)
        self.assertTrue("free_memory" in resultDict and "cached_memory" in resultDict and "stored" in resultDict
            and "cached_files" in resultDict)
        self.assertEqual(len(resultDict.get("stored_files")),3)
        





        
