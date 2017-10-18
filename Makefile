.PHONY: docker push

all: image push

TAG			?= $(shell git describe --tags --always)
VERSION     ?= $(shell echo ${TAG} | tr - .)
PREFIX		?= docker.onedata.org
REPO_NAME	?= luma

##
## Docker artifact
##

image:
	docker build . -t ${PREFIX}/${REPO_NAME}:${VERSION}

push:
	docker push ${PREFIX}/${REPO_NAME}:${VERSION}

test:
	docker run -it --rm ${PREFIX}/${REPO_NAME}:${VERSION} \
		python3 -m unittest tests/test_luma.py
