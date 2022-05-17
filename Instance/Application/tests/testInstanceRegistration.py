from email import header
import json
from django.test import TestCase

class testInstanceRegistration(TestCase):

    def setUp(self):
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

        self.instance_neptune = {
            "total_memory":7618,
            "used_memory": 67,
            "stored_files_size":323,
            "cached_files_size":10,
            "instance_name":"PLANET_NEPTUNE",
            "stored_files_count":13234,
            "cached_files_count":1034,
            "uptime":1322
        }
    
    def testInstanceRegistration(self):
        #register Mars
        response = self.client.post("/api/v1/register",self.instance_mars,content_type="application/json",HTTP_SHARD_KEY="2022RBRYANBEN")
        self.assertEqual(response.status_code,200)
        
        
        #register Pluto
        response = self.client.post('/api/v1/register',self.instance_pluto,content_type="application/json",HTTP_SHARD_KEY="2022RBRYANBEN")
        self.assertEqual(response.status_code,200)

        #register Neptune 
        response = self.client.post('/api/v1/register',self.instance_neptune,content_type="application/json",HTTP_SHARD_KEY="2022RBRYANBEN")
        self.assertEqual(response.status_code,200)

        #check if all the instances where registered from the last response
        instancesRegistered = json.loads(response.content.decode("utf8"))


    def testRegistrationWithoutShardKey(self):
        response = self.client.post("/api/v1/register",self.instance_neptune)
        self.assertEqual(response.status_code,400)

    def testRegistrationWithInvalidShardKey(self):
        response = self.client.post("/api/v1/register",self.instance_neptune,HTTP_SHARD_KEY="INVALIDKEY")
        self.assertEqual(response.status_code,401)

