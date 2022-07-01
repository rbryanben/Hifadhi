from django.test import TestCase
import os
import json

class testInstanceRetrival(TestCase):
    def setUp(self) -> None:
        self.SHARD_KEY = os.environ.get("SHARD_KEY")
        
        #register instances
        self.instance_mars = {
            "total_memory":144,
            "used_memory": 110,
            "stored_files_size":323,
            "cached_files_size":10,
            "instance_name":"PLANET_MARS",
            "stored_files_count":13234,
            "cached_files_count":1034,
            "uptime":120
        }

        self.instance_pluto = {
            "total_memory":16,
            "used_memory": 8,
            "stored_files_size":323,
            "cached_files_size":10,
            "instance_name":"PLANET_PLUTO",
            "stored_files_count":13234,
            "cached_files_count":1034,
            "uptime":0
        }

        #register Mars
        response = self.client.post("/api/v1/register",self.instance_mars,content_type="application/json",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(response.status_code,200)
        
        #register Pluto
        response = self.client.post('/api/v1/register',self.instance_pluto,content_type="application/json",HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(response.status_code,200)


    def testInstanceRetrivalWithoutShardKey(self):
        response = self.client.get('/api/v1/registered_instances')
        self.assertEqual(400,response.status_code)

    def testInstanceRetrivalWithInvalidShardKey(self):
        response = self.client.get('/api/v1/registered_instances',HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(401,response.status_code)

    def testInstanceRetrivalWithValidShardKey(self):
        response = self.client.get('/api/v1/registered_instances',HTTP_SHARD_KEY=os.environ.get("SHARD_KEY"))
        self.assertEqual(200,response.status_code)
        
        instances = json.loads(response.content)
        self.assertGreater(len(instances),0)