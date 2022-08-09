from django.test import TestCase
import os

class testCachingRoute(TestCase):
    
    def setUp(self) -> None:
        self.cacheFile = open("./Storage/Tests/puppy.png","rb")
