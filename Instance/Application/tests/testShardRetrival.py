"""
    - Retriving file when instance is not in a shard 
    - Retring file from an instance that does not exist
    - Retriving file that does not exist from another instance
    - Retriving public file from a shard (Download & Stream)
    - Retriving private file from a shard without signature or ipv4 access  
    - Retriving private file from a shard with signature
    - Retriving private file from a shard with ipv4Access 
    - Retriving private file from a shard with deleted signature
    - Retriving private file from a shard with expired signature
    - Retriving private file from a shard with deleted ipv4Access
    - Retriving private file from a shard with expired ipv4Access 
    - Retrive file after it has been updated on the other instance
"""
from django.test import TestCase
import os, json, requests
from requests_toolbelt.multipart import encoder

#decorator for shard registreation 
def shardRequired(func):
    if "GOSSIP_INSTANCE" not in os.environ: return
    
    def inner(*args,**kwargs):
        func(*args,**kwargs)
    
    return inner

def  shardNotRequired(func):
    if "GOSSIP_INSTANCE" in os.environ: return
    def inner(*args,**kwargs):
        func(*args,**kwargs)

    return inner


class testShardRetrival(TestCase):
    @classmethod
    def setUp(self):
        if "GOSSIP_INSTANCE" not in os.environ: return

        self.instance_name = os.environ.get("INSTANCE_NAME")
        self.gossip_instance_ip = os.environ.get("GOSSIP_INSTANCE")
        
        #get the instance name
        registeredInstances = requests.get(f'http://{self.gossip_instance_ip}/api/v1/registered_instances',
            headers={"SHARD-KEY":os.environ.get("SHARD_KEY")})

  
        #load all instances to a dictionary
        self.instances = json.loads(registeredInstances.text)

        for instance in self.instances:
            if self.instances[instance]["ipv4"] == self.gossip_instance_ip:
                self.test_instance = instance 
                break
        
        #test file
        self.testFile = open("./Storage/Tests/dog.jpg","rb")
        self.public_test_file_name = "rex_public.jpg"
        self.private_test_file_name = "rex_private.jpg"

        #upload a public file 
        self.testFile.seek(0,0)
        

        form = encoder.MultipartEncoder({
            "file": ("file",self.testFile, "application/octet-stream"),
            "filename":self.public_test_file_name,
            "override":"true"
        })

        result = requests.post(f"http://{self.gossip_instance_ip}/api/v1/store",data=form,
            headers={"SHARD-KEY":os.environ.get("SHARD_KEY"),"Prefer": "respond-async", "Content-Type": form.content_type})

        #upload a private file
        self.testFile.seek(0,0)
        

        form = encoder.MultipartEncoder({
            "file": ("file",self.testFile, "application/octet-stream"),
            "filename":self.private_test_file_name,
            "override":"true",
            "mode": "private"
        })

        result = requests.post(f"http://{self.gossip_instance_ip}/api/v1/store",data=form,
            headers={"SHARD-KEY":os.environ.get("SHARD_KEY"),"Prefer": "respond-async", "Content-Type": form.content_type})


       
    
    """
        Retriving file when instance is not in a shard 
    """
    @shardNotRequired
    def testRetrivingWhenNotInShard(self):
        result = self.client.get('/api/v1/download/KALAHARIANONYMOUS@demo.mp4')
        self.assertEqual(500,result.status_code)

    """
        Retriving file from an instance that does not exist (With and Without Key)
    """
    @shardRequired
    def testShardRetrivalInvalidInstance(self):
        result = self.client.get('/api/v1/download/KALAHARIANONYMOUS@demo.mp4')
        self.assertEqual(result.status_code,404)
        
    """
        Retriving file that does not exist from another instance
    """
    @shardRequired
    def testRetrivingNonExistingFileFromShard(self):
        result = self.client.get(f'/api/v1/download/{self.test_instance}@shouldNotExist.mp4')
        self.assertEqual(result.status_code,404)

    """
        Retriving public file from a shard
    """
    @shardRequired
    def testRetrivingPublicFileFromShard(self):
        pass 


""""
    These test cases where hard to implement no lie
"""

    