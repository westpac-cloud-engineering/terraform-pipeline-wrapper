from unittest import TestCase, mock
import tfe2_pipeline_wrapper.lib.ConsulKeys as ai

TEST_CONSUL_CONFIGURATION = {
    "address": "consul.test",
    "port": "8500",
    "dc": "dc1",
    "token": "FakeToken"
}

TEST_DEPLOYMENT_INFORMATION = {
    "id": "001",
    "component_name": "Infrastructure",
    "environment": "dev"
}


class TestConsulCalls(TestCase):
    def setUp(self):
        self.cc = ai.ConsulCalls(TEST_CONSUL_CONFIGURATION, TEST_DEPLOYMENT_INFORMATION)

