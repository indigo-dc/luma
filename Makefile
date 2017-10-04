.PHONY: docker push

all: image push

TAG			?= v1.0.0
PREFIX		?= docker.onedata.org
REPO_NAME	?= luma

##
## Docker artifact
##

image:
	docker build . -t ${PREFIX}/${REPO_NAME}
	docker build . -t ${PREFIX}/${REPO_NAME}:${TAG}

push:
	docker push ${PREFIX}/${REPO_NAME}
	docker push ${PREFIX}/${REPO_NAME}:${TAG}
