# -*- coding: utf-8 -*-

import docker
import pytest
import requests

from mock_results import MockResults


class TestWorker(object):

    repo = "redis"
    tag  = "latest"

    def get_image_name(self):
        return "{}:{}".format(self.repo, self.tag)

    def get_container_name(self):
        return "tests_dp2_{}".format(self.repo)

    def is_redis_image_pulled(self):

        try:
            
            self.docker.inspect_image(self.re)
            return True

        except docker.errors.NotFound:
            return False

    def setup(self):
        
        # Monkey patch requests so we can access tests data 

        MockResults.set_earliest_date()
        requests.get = MockResults.get  

        # Use a local install of docker for testing

        self.docker = docker.Client(
            base_url="unix://var/run/docker.sock")

        # Check if there is Redis image on this system
        
        if not self.is_redis_image_pulled():
            
            print "Pulling '{}:{}' image".format(
                self.redis_reg, self.redis_tag)

            self.docker.pull(
                self.redis_reg, tag=self.redis_tag)

        # Create an redis container

        self.container = self.docker.create_container(
            self.get_image_name(), 
            name=self.get_container_name(),
            detach=True
        )

        self.docker.start(container=container.get("Id"))

        # Redis container should be ready to interact with

    def test_something(self):
        pass

    def test_something_else(self):
        pass

    def teardown(self):
        self.docker.remove_container(
            self.container.get("Id"))
