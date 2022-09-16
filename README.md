I've created a web app that allows you to upload an image to minio from the browser. 
The application consists of two grpc apps communicating with each other. 
One of them is controlling the Minio server and a MongoDB database while the other one hosts a Flask web app.

To run the application you first need to start a Minio server through the terminal, info here: https://docs.min.io/docs/minio-quickstart-guide.html 
You also need to start a mongoDB server by running the docker-compose file.

Then you start the server and client by running the server.py and client.py files.

I've put the required pip installations in the requirements.txt file. 

When in the browser you type in the name of the image you want to upload and a compression ratio between 0.5 - 1 if you want to compress the image.
The image you want to upload has to be located in the "minio_upload" folder. By default, there are two images there, dummy.jpg and user.png.

To download files you enter the name of the image you've uploaded, and they will be downloaded to the "minio_download" folder. 

If you press the "Show saved files" button it will show you the filenames of all files you've uploaded to minio.
