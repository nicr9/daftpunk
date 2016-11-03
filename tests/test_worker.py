# -*- coding: utf-8 -*-
import docker
import pytest
import requests

from mock_results import MockResults


class TestWorker(object):
    repo = "redis"
    tag  = "latest"
    container_name = "tests_dp2_{}".format(repo)

    def get_image_name(self):
        return "{}:{}".format(self.repo, self.tag)

    def setup_class(cls):
        # Monkey patch requests so we can access tests data
        MockResults.set_earliest_date()
        requests.get = MockResults.get

        # Use a local install of docker for testing
        cls.docker = docker.Client(base_url="unix://var/run/docker.sock")

        # Check if there is Redis image on this system
        pulled = False
        try:
            cls.docker.inspect_image(cls.repo)
            pulled = True
        except docker.errors.NotFound:
            assert False

        if not pulled:
            print "Pulling '{}:{}' image".format(cls.repo, cls.tag)
            cls.docker.pull(cls.repo, tag=cls.tag)

        # Clean up docker containers
        cls.docker.remove_container(cls.container_name, force=True)

    def setup_method(self):
        # Create an redis container
        self.container = self.docker.create_container(
            self.get_image_name(),
            name=self.container_name,
            detach=True
        )

        self.docker.start(container=self.container.get("Id"))
        # Redis container should be ready to interact with

    def teardown_method(self):
        self.docker.remove_container(self.container.get("Id"), force=True)

    def test_something(self):
        pass

    def test_something_else(self):
        pass
