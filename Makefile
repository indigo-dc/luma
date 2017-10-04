.PHONY: docker

all: docker

##
## Docker artifact
##

docker:
	docker build . -t docker.onedata.org/luma:v1
