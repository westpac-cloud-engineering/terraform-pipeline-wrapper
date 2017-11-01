import requests
import json
import os
import hcl
from requests.auth import HTTPBasicAuth


class BambooCreateProject:
    def __init__(self, base_url):
        self.auth = HTTPBasicAuth(os.environ['bamboo_user'], os.environ['bamboo_password'])
        self.base_url = base_url + "/rest/api/latest"

        self.create_project()

        self.create_deployment_project()

    def create_project(self):
        print()

    def create_deployment_project(self):
        data = {
          "name": "Test deployment",
          "planKey": {
             "key": "TEST-TEST"
          },
          "description": "Project description"
       }

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        print (self.base_url + "/deploy/project")
        print (json.loads(requests.get(url=self.base_url + "/deploy/project/all", auth=self.auth, headers=headers).text))
        # print (requests.put(url=self.base_url + "/deploy/project",auth=self.auth, data=json.dumps(data), headers=headers).text)

createproject = BambooCreateProject(base_url="http://10.100.16.6:8085")
