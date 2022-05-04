docker rm -f desert-gobi
docker rmi gobi
docker build --tag gobi:latest .
docker run -it -d -e SHARD_KEY=2022RBRYANBEN -e INSTANCE_NAME=GOBI  --name desert-gobi -p 7123:80 gobi