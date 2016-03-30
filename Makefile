PKG_REVISION    ?= $(shell git describe --tags --always)

docker:
	rm -rf example_docker/luma
	git archive --format=tar --prefix=luma/ $(PKG_REVISION) | (cd example_docker && tar -xf -)
	./dockerbuild.py --user $(DOCKER_REG_USER) --password $(DOCKER_REG_PASSWORD) \
                         --email $(DOCKER_REG_EMAIL) --name luma \
                         --publish --remove example_docker
	rm -rf example_docker/luma