docker rm -f desert-gobi
docker rmi -f gobi
docker build --tag rbryanben/hifadhi
docker run -it -d -e SHARD_KEY=2022RBRYANBEN -e INSTANCE_NAME=GOBI  -e GOSSIP_INSTANCE=172.17.0.1:8000 --name desert-gobi -p 7123:80 rbryanben/hifadhi:test