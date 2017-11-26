import requests
import json
import os

# BASE API CALLS
class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organization, app_id, component_name, atlas_token=None):

        # Get Token from Environment Variable if not passed.
        if atlas_token == None:
            atlas_token = os.environ["ATLAS_TOKEN"]

        self.header = {
            'Authorization': "Bearer " + atlas_token,
            'Content-Type': 'application/vnd.api+json'
        }

        self.app_id = app_id
        self.component_name = component_name
        self.organization = organization

    def get_workspaces(self):
        workspaces_url = self.base_url + "/organizations/" + self.organization + "/workspaces"
        return requests.get(workspaces_url, headers=self.header)


    def get_workspace_id(self, workspace_name):
        linkable_repo_url = self.base_url + "/organizations/" + self.organization + "/workspaces"
        r = requests.get(url=linkable_repo_url, headers=self.header).text

        # Find the ID for the Repository that matches the repository name.
        for obj in json.loads(r)['data']:
            if obj["attributes"]["name"] == workspace_name:
                return obj["id"]

    def get_git_oauth_token(self):
        oauth_token_url = self.base_url + "/organizations/" + self.organization + "/o-auth-tokens"
        r = requests.get(url=oauth_token_url, headers=self.header).text
        return r


    def create_workspace(self, environment, repo_name, branch="master"):
        workspace_name = self.generate_workspace_name(environment)
        workspaces_url = self.base_url + "/compound-workspaces"

        # Build Request
        data = {
            "data": {
                "type": "compound-workspaces",
                 "attributes": {
                    "name": workspace_name,
                    "working_directory": "",
                    "linkable-repo-id": repo_name,
                    "o-auth-token-id": 233140,
                    "ingress-trigger-attributes": {
                        "default-branch": "true",
                        "branch": branch,
                        "vcs_root_path": "",
                        "ingress-submodules": "false",
                    }
                }
            }
        }

        # Make Request
        request = requests.post(url=workspaces_url, data=json.dumps(data), headers=self.header)

        print(request.status_code)
        return workspace_name

    def generate_workspace_name(self, environment):
        return (self.app_id + "-" + environment + "-" + self.component_name).replace(" ", "_")

