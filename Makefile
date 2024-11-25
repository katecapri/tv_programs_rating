
.PHONY: run
run:
	- docker network create tv_network
	- docker-compose up -d --build