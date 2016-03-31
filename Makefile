docker:
	git archive --format=tar --prefix=luma/ --output=example_docker/luma.tar HEAD
	./dockerbuild.py --user $(DOCKER_REG_USER) --password $(DOCKER_REG_PASSWORD) \
                         --email $(DOCKER_REG_EMAIL) --name luma \
                         --publish --remove example_docker
	rm example_docker/luma.tar