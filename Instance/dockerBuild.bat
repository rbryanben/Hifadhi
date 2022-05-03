docker rm -f gobi_test
docker rmi gobi
docker build --tag gobi:latest .
docker run -it -d -e SHARD_KEY=2022RBRYANBEN -e INSTANCE_NAME=GOBI --name gobi_test -p 7123:80 gobi