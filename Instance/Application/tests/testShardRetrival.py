from django.test import TestCase
import os

class testShardRetrival(TestCase):
    def setUp(self):
        self.instance_name = os.environ.get("INSTANCE_NAME")
    
    def testInstanceIpv4Retrival(self):
        #check if the gossip instance is defined
        if "GOSSIP_INSTANCE" not in os.environ: return

        #retrieve the IPv4
        response = self.client.post(f'http://{os.environ.get("GOSSIP_INSTANCE")}/api/v1/shard_instance',{"instance_name":self.instance_name},HTTP_SHARD_KEY="2022RBRYANBEN")
        self.assertEqual(response.status_code,200)