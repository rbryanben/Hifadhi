from fileinput import filename
import os
from django.test import TestCase
from Shared.storage import store, cache
from Shared.models import *




"""
    Storage Module Tests
"""
class testStorageModuleTests(TestCase):
    def setUp(self) -> None:
        #remove files 
        try:
            os.remove("./Storage/Local/banana.txt")
            os.remove("./Storage/Local/banana2.txt")
            os.remove("./Storage/Temp/sahara@banana.txt")
        except FileNotFoundError:
            pass

        self.testfile = open("./Storage/Tests/banana.txt",'rb')
        self.overrideTestFile = open("./Storage/Tests/banana_override.txt",'rb')

    #
    # Storage Tests
    #

    def testStoringFile(self):
        result = store(self.testfile,'banana.txt')
        
        #check if got true
        self.assertTrue(result[0])
        #check if the query name is correct
        self.assertEqual(result[1],f'{os.environ.get("INSTANCE_NAME")}@banana.txt')

        #test if the file was stored 
        savedFile = open('./Storage/Local/banana.txt')
        self.testfile.seek(0,0)
        self.assertEqual(savedFile.read(),self.testfile.read().decode("utf8"))

        #Test database record was kept 
        self.assertIsNotNone(storedFile.objects.get(filename="banana.txt"))
    
    def testStoringPrivateFile(self):
        result = store(self.testfile,'banana3.txt',public=False)

        # Assert the file is private
        self.assertFalse(storedFile.objects.get(filename='banana3.txt').public)

    def testStoringFileWithOverride(self):
        result = store(self.testfile,'banana2.txt',override=True)

        #check if got true
        self.assertTrue(result[0])
        #check if the query name is correct
        self.assertEqual(result[1],f'{os.environ.get("INSTANCE_NAME")}@banana2.txt')

        #test if the file was stored 
        savedFile = open('./Storage/Local/banana2.txt')
        self.testfile.seek(0,0)
        self.assertEqual(savedFile.read(),self.testfile.read().decode("utf8"))

        # Check database
        self.assertIsNotNone(storedFile.objects.get(filename="banana2.txt"))

    def testStoringFileWithConfictingName(self):
        
        #store the first file
        self.testfile.seek(0,0)
        store(self.testfile,'banana.txt')

        result = store(self.testfile,'banana.txt')

        #check if event failed
        self.assertFalse(result[0])

    def testStoringWithConfictingNameFileWithOverride(self):
        self.testfile.seek(0,0)
        store(self.testfile,'banana.txt')

        result = store(self.overrideTestFile,'banana.txt',override=True)

        #test if event was successful
        self.assertTrue(result[0])

        #test if the file was overridden
        fileOverridden = open("./Storage/Local/banana.txt",'rb')
        self.overrideTestFile.seek(0,0)
        self.assertEqual(self.overrideTestFile.read(),fileOverridden.read())

    #
    #  Cache Tests
    #

    def testCachingFile(self):
        #cache the test file 
        result = cache(self.testfile,"sahara@banana.txt")

        #Test if the file was saved
        self.testfile.seek(0,0) 
        with open("./Storage/Temp/sahara@banana.txt","rb") as fileToTest:
            self.assertEqual(fileToTest.read(),self.testfile.read())

        #Test if the result was true
        self.assertTrue(result[0])

    def testCachingFileAlreadyCached(self):
         #cache the test file 
        result = cache(self.overrideTestFile,"sahara@banana.txt")

        #Test if the file was saved
        self.overrideTestFile.seek(0,0) 
        with open("./Storage/Temp/sahara@banana.txt","rb") as fileToTest:
            self.assertEqual(fileToTest.read(),self.overrideTestFile.read())

    def testCachingPrivateFile(self):
        file = self.testfile
        file.seek(0,0)

        cache(file,"sahara@banana_pvt.txt",public=False)

        self.assertFalse(cachedFile.objects.get(fileQueryName="sahara@banana_pvt.txt").public)


  