import asyncio
import logging
import os
import grpc
import app_pb2, app_pb2_grpc
from pymongo import MongoClient
from PIL import Image
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

_cleanup_coroutines = []


class FileHandler:

    def __init__(self):
        self.minio_client = None
        self.db_client = None
        self.db_files = None
        self.s3 = None

    def setup_s3(self):
        self.s3 = boto3.resource('s3',
                            endpoint_url='http://localhost:9000',
                            aws_access_key_id='minioadmin',
                            aws_secret_access_key='minioadmin',
                            config=Config(signature_version='s3v4'),
                            region_name='us-east-1')

    def setup_db(self):
        self.db_client = MongoClient('mongodb://localhost:27017/',
                                serverSelectionTimeoutMS=3000,
                                username="root",
                                password="1234")
        db = self.db_client["mydatabase"]
        self.db_files = db.saved_files

    def add_filename_to_db(self, filename):
        input = {"filename": filename}
        return self.db_files.insert_one(input)

    def get_db_filenames(self):
        filenames = self.db_files.find()
        return filenames

    def resize_img(self, filename, ratio):
        try:
            path = os.getcwd() + f'/minio_upload/{filename}'
            img = Image.open(path)
            print("img", img.size)
            new_img = img.resize((int(img.width * ratio), int(img.height * ratio)))
            print("new_img", new_img.size)
            new_img.save(path)
            return True
        except (FileNotFoundError, ValueError, OverflowError, MemoryError):
            return False

    def upload_image(self, filename, ratio):
        if self.resize_img(filename, ratio):
            path = os.getcwd() + f'/minio_upload/{filename}'
            if self.s3.Bucket('image').creation_date is None:
                self.s3.create_bucket(Bucket='image')
            try:
                self.s3.Bucket('image').upload_file(path, filename)
                return True
            except FileNotFoundError:
                return False
        return False

    def download_image(self, filename):
        path = os.getcwd() + f'/minio_download/{filename}'
        try:
            self.s3.Bucket('image').download_file(filename, path)
            return True
        except ClientError:
            return False


class ApiServicer(app_pb2_grpc.ApiServicer):

    def __init__(self):
        self.filehandler = FileHandler()
        self.filehandler.setup_db()
        self.filehandler.setup_s3()

    async def UploadImage(self, request, context):
        status = self.filehandler.upload_image(request.filename, request.ratio)
        if status:
            self.filehandler.add_filename_to_db(request.filename)
            response = f'{request.filename} uploaded succesfully'
        else:
            response = f'{request.filename} could not be uploaded'
        return app_pb2.ImageResponse(message=response)

    async def DownloadImage(self, request, context):
        print("Server downloading image")
        status = self.filehandler.download_image(request.filename)
        if status:
            response = f"{request.filename} downloaded successfully"
        else:
            response = f"{request.filename} not found"
        return app_pb2.ImageResponse(message=response)

    def PrintSavedFiles(self, request, context):
        filenames = self.filehandler.get_db_filenames()
        for filename in filenames:
            response = app_pb2.FilenameResponse(filename=filename['filename'])
            yield response


async def serve() -> None:
    server = grpc.aio.server()
    app_pb2_grpc.add_ApiServicer_to_server(ApiServicer(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()

    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
