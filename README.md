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
