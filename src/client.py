import asyncio
import logging

import grpc
import app_pb2, app_pb2_grpc
from flask import Flask, render_template, request
from server import ApiServicer
import os

app = Flask(__name__)


@app.route("/filenames/", methods=['GET', 'POST'])
async def get_filenames():
    async with grpc.aio.insecure_channel('[::]:50051') as channel:
        stub = app_pb2_grpc.ApiStub(channel)
        filenames = []
        async for name in stub.PrintSavedFiles(app_pb2.FilenameRequest(message="bla")):
            filenames.append(name)
    return render_template(
        "filenames.html",
        filenames=filenames
    )


@app.route("/", methods=['GET', 'POST'])
@app.route("/image/", methods=['GET', 'POST'])
async def handle_image():
    upload_file = request.args.get('upload_file')
    download_file = request.args.get('download_file')
    comp_ratio = request.args.get('comp_ratio')
    if comp_ratio != "" and comp_ratio is not None:
        try:
            comp_ratio = float(comp_ratio)
        except ValueError:
            return render_template(
                "image.html",
                response="Compression ratio has to be numeric"
            )
        if comp_ratio < 0.5 or comp_ratio > 1:
            return render_template(
                "image.html",
                response="Compression ratio has to be between 0.5-1"
            )
    else:
        comp_ratio = 1

    if upload_file is not None and upload_file != "":
        async with grpc.aio.insecure_channel('[::]:50051') as channel:
            stub = app_pb2_grpc.ApiStub(channel)
            response = await stub.UploadImage(app_pb2.UploadRequest(filename=upload_file, ratio=comp_ratio))
        return render_template(
            "image.html",
            response=response.message
        )

    elif download_file is not None and download_file != "":
        async with grpc.aio.insecure_channel('[::]:50051') as channel:
            stub = app_pb2_grpc.ApiStub(channel)
            response = await stub.DownloadImage(app_pb2.UploadRequest(filename=download_file))
        return render_template(
            "image.html",
            response=response.message
        )
    else:
        return render_template(
            "image.html",
            response=""
        )

app.config["api"] = ApiServicer()


if __name__ == '__main__':
    logging.basicConfig()
    port = int(os.environ.get('PORT', 8000))
    asyncio.run(app.run(host='0.0.0.0', port=port))
