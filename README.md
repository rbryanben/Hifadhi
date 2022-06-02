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
