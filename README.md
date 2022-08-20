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

# Retrieving Files
  
For this you need nothing but a browser. There are two options to retriving a file <code>Stream</code> or <code>Download</code> retrival.
On streaming the file is returned in small bits and pieces called chunks. Streaming is suitable for video streaming apps where you want to start watching the video 
immediately and have an option to skip to a certain part, these features which are not present on Download. Download retrival returnes the file faster than Stream.
Now go ahead and stream the video we uploaded earlier using this link.

```
http://localhost:7111/api/v1/stream/Kalahari@video.mp4
```
  And to download the file simply change <code>stream</code> to <code>download</code> on the url
  
```
http://localhost:7111/api/v1/download/Kalahari@video.mp4
```
  
  # Access Control
  
  Now lets secure our files by putting access control measures. And there are two access control measures we can use <code>Presigned URLs</code> and <code>IPv4 Access</code>. In presigned-urls a unique url is generated for you, which in turn you can give to a client to use. These presigned urls are really long with the aim of making it hard to guess a url as there are 36^256 possibilities. As for IPv4 Access its as simple as giving access to some IP address. Lets upload another video of your choice but this time we will add another body parameter <code>mode</code> which is used to define wheather a file is public or private.
  
  ```yml
  - Request: POST
  - Headers:
    - SHARD-KEY: Key we defined ealier on as an enviroment variable 
  - Body (Multipart-form):
    - file: The file itself 
    - filename: The name to save the file as
    - mode: private
  ```
  
  Your request should look something like this
  ```
  curl --request POST \
    --url http://localhost:7111/api/v1/store \
    --header 'Content-Type: multipart/form-data' \
    --header 'SHARD-KEY: BasicPassword' \
    --form 'file=@C:\Users\rbryanben\Videos\another_video.mp4' \
    --form filename=another_video.mp4 \
    --form mode=private
  ```
  
  # Presigned URLs 
  
  A GET request to the path <code>/api/v1/presign/[your_query_string]</code> is used to generate presigned urls. Within the request the parameter <code>duration</code> and the header <code>SHARD-KEY</code> have to be present as defined below.
  
  ```yml
  - Request: GET
  - Headers:
    - SHARD-KEY: Key we defined ealier on as an enviroment variable 
  - Parameters:
    - duration: Time in seconds the presigned url should remain valid
  ```
  
  Using curl your request should look something like this. It is important to note that you cannot generate a presigned url for a public file. 
  
  ```shell
  curl --request GET \
    --url 'http://localhost:7111/api/v1/presign/Kalahari@another_video.mp4?duration=60' \
    --header 'SHARD-KEY:  BasicPassword'
  ```
  
  In return you should get a signed query string that looks like this
  
  ```shell
  Kalahari@another_video.mp4?signature=9cfb765b-58fd-419a-8990-4a9b18ef6ffb5bc47f08-48be-4704-a2a4-648c4a212c3fd662bdb1-1a54-4381-8b81-a451b26e7962181ef282-ea9a-4709-bcb8-63d300bf652e
  ```
  
  Send this string to the path <code>/api/v1/stream</code> to stream the video.
  ```
  http://localhost:7111/api/v1/stream/[your_signed_query_string]
  ```
  
  
  
  # IPv4 Access 
  
  A GET request to the path <code>/api/v1/ipv4access/[your_query_string] </code> is used to grant IPv4 access. Within the request the parameters <code>duration</code>,<code>ipv4</code> and the header <code>SHARD-KEY</code> have to be present as defined by the template below.
  
  ```yml
  - Request: GET
  - Headers:
    - SHARD-KEY: Key we defined ealier on as an enviroment variable 
  - Parameters:
    - duration: Time in seconds the presigned url should remain valid
    - ipv4: IP address to give access to 
  ```
  
  Your curl request should look something like this
  
  ```
  curl --request GET \
    --url 'http://localhost:7111/api/v1/ipv4access/Kalahari@another_video.mp4?duration=60&ipv4=172.17.0.1' \
    --header 'SHARD-KEY:  BasicPassword'
  ```
  
  You should get the IP address you specified as an indication of success.
  
  ```
  172.17.0.1
  ```
  
  It is important to note that we did not use the IP address 127.0.0.1 and used instead the docker network gateway 172.17.0.1 to grant access. This is because requests to containers come from the network gateway unless you have macvlan setup with the container network. To learn more about how you can use your actual IP read the feature docs on Access Control. Now go ahead and stream the file.

# Sharding

Now comes the key feature which is to distribute the instances to increase availability and storage capacity. And let us start off by understanding what a gossip instance is.

# Gossip Instance

The gossip instance is sort of the leader among a group of instances. It keeps the records of all instances that are linked together and provides other instances with infomation about other instances, such that they can retrieve information from them. An instance becomes a gossip instance when another instance registers to it, meaning initially a gossip instance is a regular instance. 

# Registering to a Gossip Instance

To register to an instance simply set the enviroment variable GOSSIP_INSTANCE for your container with the address of the instance you want to register to. NB: Do not define https:// or http:// for in your address otherwise on connection the instance will interpret the address as http://http://<your_address> which will not work. The instance will try to connect over HTTP and if that fails it will try over HTTPS.

Let us start off by creating an instance named Kalahari that will act as our gossip instance, assuming you do not have one from the previous turtorials.

```
 docker run --name instance-kalahari -d -e INSTANCE_NAME=Kalahari -e SHARD_KEY=BasicPassword -p 7110:80  rbryanben/hifadhi:test
```

Now let us obtain the instance IP using this command 

```
docker inspect -f "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}" instance-kalahari
```

Once the instance is running and you have the ip, lets create another instance that runs on port 7510 with the same SHARD-KEY and GOSSIP_INSTANCE set to the IP address of the instance Kalahari. If the shard key does not match, the instance will not be registered

```
docker run --name instance-sahara -d -e INSTANCE_NAME=Sahara -e SHARD_KEY=BasicPassword -e GOSSIP_INSTANCE=<Kalahari_ip> -p 7510:80  rbryanben/hifadhi:test
```

That being done, let us check if the instance was registered on the gossip instance buy executing this curl command

```
curl --request GET \
  --url http://localhost:7110/api/v1/registered_instances \
  --header 'Content-Type: multipart/form-data' \
  --header 'SHARD-KEY: BasicPassword'
```

You should get a list of all registered instances if everything executed correctly.

```JSON
{
	"Sahara": {
		"ipv4": "172.17.0.3",
		"total_memory": 244,
		"used_memory": 90,
		"stored_files_size": 0,
		"cached_files_size": 0,
		"instance_name": "Sahara",
		"stored_files_count": 0,
		"cached_files_count": 0,
		"uptime": 0,
		"healthy": true
	},
	"Kalahari": {
		"ipv4": "localhost:7110",
		"total_memory": 244.47995376586914,
		"used_memory": 90.63045501708984,
		"stored_files_size": 0,
		"cached_files_size": 0,
		"instance_name": "Kalahari",
		"stored_files_count": 0,
		"cached_files_count": 0,
		"uptime": 798.4496290683746
	}
}
```
Congratulations if you received the above response. You have setup your very first distributed file server. Now go ahead an upload a file to any one of the instances and then try to stream the file from both instances.

# Using Compose

Lets now try to setup a 3 distributed instances using Docker Compose this time so that we can easily manage instances instead of doing everything randomly. Paste the following yml into your docker-compose.yml file and then run it.
	
```yml
version: "3.3"
services:
  kalahari:
    image: "rbryanben/hifadhi:test"
    ports:
      - 8000:80
    environment:
      - SHARD_KEY=BasicPassword
      - INSTANCE_NAME=kalahari
  namib:
    image: "rbryanben/hifadhi:test"
    ports:
      - 8001:80
    environment:
      - SHARD_KEY=BasicPassword
      - INSTANCE_NAME=namib
      - GOSSIP_INSTANCE=kalahari
    depends_on:
      - kalahari
  sahara:
    image: "rbryanben/hifadhi:test"
    ports:
      - 8002:80
    environment:
      - SHARD_KEY=BasicPassword
      - INSTANCE_NAME=sahara
      - GOSSIP_INSTANCE=kalahari
    depends_on:
      - kalahari
      
```
	
In my case I used the command below to build the compose file 

```
docker-compose up -d --build
```
Go ahead and navigate to localhost ports 8000 8001 and 8002 to verify that the instances are running. 

# Congratulations 
	
Congrats if you have reached this point, which is basically all there is to it. The last thing to do is to run a production version of Hifadhi instead of the test version we were using that uses a development server.

# Production

For production you should use the latest tag instead of the test tag. Go ahead and pull the latest version of Hifadhi from Docker Hub

```
docker pull rbryanben/hifadhi:latest
```

# Workers and Threads

The production version of Hifadhi uses Gunicorn as its HTTP Server. Gunicorn needs defined, the number of worker procceesses it will have, and the number of threads. If running one instance only it is recommened to set the number of workers between 4-12, as stated by their <a href="https://docs.gunicorn.org/en/stable/design.html#:~:text=DO%20NOT%20scale%20the%20number,load%20balancing%20when%20handling%20requests.">documentation</a>. And then set the threads to four. 

# Running Latest

To run a production instance, you need WORKERS and THREADS set as enviroment variables. 
```
docker run --name instance-production -d -e INSTANCE_NAME=ProductionDemo -e SHARD_KEY=BasicPassword -e WORKERS=4 -e THREADS=4 -p 9000:80  rbryanben/hifadhi:latest
```
Go ahead and navigate to port 9000
  
  

  
