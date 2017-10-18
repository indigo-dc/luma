.PHONY: docker push

all: image push

COMMIT      := $(shell git rev-parse HEAD)
HASH        := $(shell git rev-parse --short=10 HEAD)
BRANCH      := $(shell git rev-parse --abbrev-ref HEAD)
TICKET      := $(shell git rev-parse --abbrev-ref HEAD | sed -nr 's/.*VFS-([0-9]+).*/\1/p')
RELEASE     := $(shell git rev-parse --abbrev-ref HEAD | sed -nr 's/release\/(.+)/\1/p')
TAG			?= $(shell git describe --tags --always)
VERSION     ?= $(shell echo ${TAG} | tr - .)
PREFIX		?= docker.onedata.org
REPO_NAME	?= luma


##
## Docker artifact
##

image:
	docker build . -t ${PREFIX}/${REPO_NAME}:ID-${HASH}

push:
	@echo "docker push ${PREFIX}/${REPO_NAME}:ID-${HASH}"
	$(shell echo "Build report for luma" > luma-docker-build-report.txt)
	$(shell echo "" >> luma-docker-build-report.txt)
	$(shell echo "Artifacts:" >> luma-docker-build-report.txt)
	$(shell echo "" >> luma-docker-build-report.txt)
	$(shell echo "Artifact docker.onedata.org/luma:ID-${HASH}" >> luma-docker-build-report.txt)
	$(shell echo "	To get image run:" >> luma-docker-build-report.txt)
	$(shell echo "		docker pull docker.onedata.org/luma:ID-${HASH}" >> luma-docker-build-report.txt)
ifneq ($(TICKET),)
	@echo "docker tag ${PREFIX}/${REPO_NAME}:ID-${HASH} ${PREFIX}/${REPO_NAME}:VFS-${TICKET}"
	@echo "docker push ${PREFIX}/${REPO_NAME}:VFS-${TICKET}"
	$(shell echo "		docker pull docker.onedata.org/luma:VFS-${TICKET}" >> luma-docker-build-report.txt)
endif
ifneq ($(RELEASE),)
	@echo "docker tag ${PREFIX}/${REPO_NAME}:ID-${HASH} ${PREFIX}/${REPO_NAME}:${RELEASE}"
	@echo "docker push ${PREFIX}/${REPO_NAME}:${RELEASE}"
	$(shell echo "		docker pull docker.onedata.org/luma:${RELEASE}" >> luma-docker-build-report.txt)
endif


test:
	docker run -t --rm ${PREFIX}/${REPO_NAME}:ID-${HASH} \
		python3 -m unittest tests/test_luma.py
