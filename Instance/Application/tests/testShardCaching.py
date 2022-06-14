from django.test import TestCase
import Main.urls as Startup
import os 

class testShardCaching(TestCase):
    
    #Setup Function
    def setUp(self) -> None:
        return

    #Test Caching Router
    def testCachingRoute(self):
        response = self.client.post("/api/v1/shard_cache",{"priority":7,"query_string":"KALAHARI@music.mp4"},
            HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))

        print(response.content)