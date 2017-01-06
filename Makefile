DOCKER_REG_NAME     ?= "docker.onedata.org"
DOCKER_REG_USER     ?= ""
DOCKER_REG_PASSWORD ?= ""

docker:
	git archive --format=tar --prefix=luma/ --output=example_docker/luma.tar HEAD
	./docker_build.py --repository $(DOCKER_REG_NAME) --user $(DOCKER_REG_USER) \
                    --password $(DOCKER_REG_PASSWORD)  --name luma --publish \
                    --remove example_docker
	rm example_docker/luma.tar
