import os
import unittest
from mongomock import MongoClient
from moto import mock_s3
import boto3
from server import FileHandler
from PIL import Image


class TestDB(unittest.TestCase):

    def setUp(self):
        self.filehandler = FileHandler()

    # Tests that correct values are stored with the add_filenames_to_db
    def test_add_filenames_to_db(self):
        self.filehandler.db_files = MongoClient().db.collection
        names = ["name1", "name2", "name3"]
        for name in names:
            self.filehandler.add_filename_to_db(name)
        for name in names:
            found_name = self.filehandler.db_files.find_one({"filename": name})['filename']
            self.assertEqual(name, found_name)

    # Tests that correct values are returned from the get_db_filenames
    def test_get_db_filenames(self):
        self.filehandler.db_files = MongoClient().db.collection
        names = ["name1", "name2", "name3"]
        for name in names:
            self.filehandler.db_files.insert_one({"filename": name})
        found_names = self.filehandler.get_db_filenames()
        for found_name in found_names:
            self.assertTrue(found_name['filename'] in names)

    # Tests that correct number of values are stored with the add_filenames_to_db
    def test_add_filenames_to_db_count(self):
        self.filehandler.db_files = MongoClient().db.collection
        names = ["name1", "name2", "name3"]
        for name in names:
            self.filehandler.add_filename_to_db(name)
        found_names = self.filehandler.db_files.find()
        nbr_found_names = 0
        for _ in found_names:
            nbr_found_names += 1
        self.assertEqual(len(names), nbr_found_names)

    # Tests that correct number of values are returned from the get_db_filenames
    def test_get_db_filenames_count(self):
        self.filehandler.db_files = MongoClient().db.collection
        names = ["name1", "name2", "name3"]
        for name in names:
            self.filehandler.db_files.insert_one({"filename": name})
        found_names = self.filehandler.get_db_filenames()
        nbr_found_names = 0
        for _ in found_names:
            nbr_found_names += 1
        self.assertEqual(len(names), nbr_found_names)


class TestMinio(unittest.TestCase):

    @mock_s3
    def setUp(self):
        self.filehandler = FileHandler()
        self.filehandler.setup_s3()
        path = os.getcwd() + f'/minio_upload/testfile.jpg'
        img = Image.new(mode="RGB", size=(10, 10))
        img.save(path)

    def tearDown(self):
        path = os.getcwd() + f'/minio_upload/testfile.jpg'
        os.remove(path)

    @mock_s3
    def test_upload_image(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')

        status = self.filehandler.upload_image("testfile.jpg", 1)
        self.assertTrue(status)

    @mock_s3
    def test_upload_not_existing_file(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')
        status = self.filehandler.upload_image("wrong_filename.jpg", 1)
        self.assertFalse(status)

    @mock_s3
    def test_upload_negative_ratio(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')
        status = self.filehandler.upload_image("testfile.jpg", -1)
        self.assertFalse(status)

    @mock_s3
    def test_upload_zero_ratio(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')
        status = self.filehandler.upload_image("testfile.jpg", 0)
        self.assertFalse(status)

    @mock_s3
    def test_upload_ratio_as_string(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')
        status = self.filehandler.upload_image("testfile.jpg", "string")
        self.assertFalse(status)

    @mock_s3
    def test_upload_ratio_as_number_as_string(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')
        status = self.filehandler.upload_image("testfile.jpg", "string")
        self.assertFalse(status)

    @mock_s3
    def test_download_image(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')

        filename = "testfile.jpg"
        path = os.getcwd() + f'/minio_upload/{filename}'
        self.filehandler.s3.Bucket('image').upload_file(path, filename)

        status = self.filehandler.download_image(filename)
        self.assertTrue(status)

        file_exists = os.path.isfile(path)
        self.assertTrue(file_exists)

        if file_exists:
            path = os.getcwd() + f'/minio_download/{filename}'
            os.remove(path)

    @mock_s3
    def test_download_not_existing_file(self):
        self.filehandler.s3 = boto3.resource('s3', region_name='us-east-1')
        self.filehandler.s3.create_bucket(Bucket='image')

        filename = "wrong_filename.jpg"
        status = self.filehandler.download_image(filename)
        self.assertFalse(status)

        path = os.getcwd() + f'/minio_download/{filename}'
        file_exists = os.path.isfile(path)
        self.assertFalse(file_exists)
