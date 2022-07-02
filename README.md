# About Hifadhi
Hifadhi is a distributed file server made with python that makes use of containers. In English it is just AWS S3 that you can run on your computer or computers and serve files with access control.

# Capabilites
In this context a container running Hifadhi is refered to as an instance, and an instance has the following capabilities
- Store files.
- Serve stored files as a download.
- Stream files (Meaning you can build Netflix using Hifadhi).
- Generate presigned urls as an access control measure.
- Grant access to a file to a certin ipv4 (Another access control measure).
- Join a shard to increase the storage capacity.
- Cache files from other instances thereby increasing the file's availability.
- Ask other instances to cache a certain file given it is receiving too much load.

# Sharding

In this mechanism we want to increase the capacity of data we can store by storing data on multiple instances. Instances can obtain data from other instances and serve that data themselves as visulized below.

<img src="/Docs/Images/multi_instance.png" height="400px"/>

# Availability

In this mechanism a file is cached on other instances to increase its availability, as the file does not have to be fetched from the instances storing that file when a request is made. Caching is done every time an instance receives a request for a file that is on another instance, that file is downloaded from the other instance and cached locally. Or be done from the adapter as below.

<img src="/Docs/Images/shard_caching.png" height="500px"/>

# Getting Started

It is assumed you have Docker installed on your machine. If not follow the <a href="https://docs.docker.com/engine/install/">installation<a> guide on the Docker website. Once you have Docker setup, go ahead and pull the Hifadhi image from docker hub.

```
docker pull rbryanben/hifadhi:test
```

Once that is done go ahead and run your first instance on port 7111 using the command

```
docker run --name instance-kalahari -d -e INSTANCE_NAME=Kalahari -e SHARD_KEY=BasicPassword -p 7110:80  rbryanben/hifadhi:test
```
And just like that we have our first instance running, and now lets check that our instance is healthy by using curl to get the instance health. If you do not have curl installed on your machine you can simply click this <a href="http://localhost:7111/api/v1/health">link to check using your browser<a/>, and dont forget to come back.

```shell
curl http://localhost:7111/api/v1/health
```

You should get something like this, that shows the status of the instance.

<code>
{"status": "healthy", "uptime": 110.42238450050354, "instance": "Kalahari", "known_instances": null}
</code>

# Uploading Files 

It is assumed you have a program like <a href="https://www.postman.com/downloads/">postman</a> for api requests installed on your machine. What we want to do is upload a file to the instance so that we can later on
retrive it, and to do this we need to send a POST request to the instance address <code>http://localhost:7111/api/v1/store</code> with the following headers and body.

```yml
- Request: POST
- Headers:
  - SHARD-KEY: Key we defined ealier on as an enviroment variable 
- Body (Multipart-form):
  - file: The file itself 
  - filename: The name to save the file as 
```

Using this template upload <strong>any video of your choice</strong>  with the filename <strong>video.mp4</strong> and the shard-key set to <strong>BasicPassword</strong> like we defined on creating our container. As a curl request it should look like this

```shell
curl --request POST \
  --url http://localhost:7111/api/v1/store \
  --header 'Content-Type: multipart/form-data' \
  --header 'SHARD-KEY: BasicPassword' \
  --form 'file=@C:\Users\rbryanben\Videos\video.mp4' \
  --form filename=video.mp4 \
  --form =
```

Which we should receive a 200 response with a query string that looks like this
```
Kalahari@video.mp4
```

If you did not receive a 200 response with a query string here of the other reponse codes and what they mean.
```yaml
- Response:
  - 400 (Missing Parameters): One or more of the body parameters file and filename is missing. 
  - 401 (Denied): The SHARD-KEY defined on creating the instance container did not match the one supplied in the headers.
  - 500 (Internal Server Error): You should not get this
  - 200 (Success): File was uploaded successfully
```
