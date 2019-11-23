.PHONY: test build-image

CONTAINER_ENGINE ?= docker
IMAGE_NAME := operator-curator
IMAGE_TAG := $(shell git rev-parse --short=7 HEAD)

test:
	python3 -m unittest test/*.py

build-image:
	$(CONTAINER_ENGINE) build -t "$(IMAGE_NAME):$(IMAGE_TAG)" .

