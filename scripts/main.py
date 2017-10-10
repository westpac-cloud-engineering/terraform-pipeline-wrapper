import requests
import json
import os
import hcl

class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organization, atlas_token=None, base_api_url=None, ):

        # Get Token from Environment Variable if not passed.
        atlas_token = os.environ["ATLAS_TOKEN"]
        self.header = {
            'Authorization': "Bearer " + atlas_token,
            'Content-Type': 'application/vnd.api+json'
        }

        self.organization = organization

    def get_workspaces(self):
        workspaces_url = self.base_url + "/organizations/" + self.organization + "/workspaces"
        return requests.get(workspaces_url,headers=self.header)

    def get_linkable_repo_id(self, repo_name):
        linkable_repo_url = self.base_url + "/linkable-repos?filter[organization][username]=" + self.organization
        r = requests.get(url=linkable_repo_url, headers=self.header).text

        # Find the ID for the Repository that matches the repository name.
        for obj in json.loads(r)['data']:
            if obj["attributes"]["name"] == repo_name:
                return obj["id"]

    def CreateWorkspace(self, workspace_title, repo_name, path="", branch="master"):
        repo_id = self.get_linkable_repo_id(repo_name)
        workspaces_url = self.base_url + "/compound-workspaces"

        # Build Request
        data = {
            "data" : {
                "type": "compound-workspaces",
                "attributes": {
                    "name": workspace_title,
                    "working_directory":"",
                    "linkable-repo-id": repo_id,
                    "ingress-trigger-attributes": {
                        "default-branch": "true",   # NOT CONFIGURABLE IN BETA. TO BE REPLACED WITH DEFAULT BRANCH
                        "branch": branch,           # NOT CONFIGURABLE IN BETA. TO BE REPLACED WITH DEFAULT BRANCH
                        "vcs_root_path": "",
                        "ingress-submodules": "false",
                    }
                }
            }
        }

        # Make Request
        return requests.post(url=workspaces_url, data=json.dumps(data), headers=self.header)

    def AddWorkspaceVariable(self, workspace, key, value, category="terraform", sensitive="false",
                                  hcl="false",variable_id=None):
        variable_url = self.base_url + "/vars"

        data = {
            "data": {
                "type": "vars",
                "attributes": {
                    "key": key,
                    "value": value,
                    "category": category,
                    "hcl": sensitive,
                    "sensitive": sensitive
                }
            }
        }

        # If new variable, filter to the correct workspace
        if variable_id == None:
            data["filter"] = {
                "organization": {
                    "username": self.organization
                },
                "workspace": {
                    "name": workspace
                }
            }
            return requests.post(url=variable_url, data=json.dumps(data), headers=self.header)

        # Else find the existing one using the variable ID
        else:
            data["data"]["id"] = variable_id
            print(data)
            return requests.patch(url=variable_url + "/" + variable_id, data=json.dumps(data), headers=self.header)

    def LoadVariables(self, tfvars_location, workspace):
        request_uri = self.base_url + "/vars?filter[organization][username]=" + self.organization + "&filter[workspace][name]=" + workspace

        data = requests.get(request_uri, headers=self.header).text

        # Delete all the existing (Non-Environment) variables
        for tfvar in json.loads(data)["data"]:
            if tfvar["attributes"]["category"] == "terraform":
                self.DeleteVariable(tfvar["id"])

        with open(tfvars_location, 'r') as fp:
            variable_list = hcl.load(fp)
            for obj in variable_list:
                self.AddWorkspaceVariable(workspace, obj, hcl.dumps(variable_list[obj]))

    def LoadLocalAzureCredentials(self, workspace):
        self.AddWorkspaceVariable(workspace, "ARM_CLIENT_ID", os.environ["ARM_CLIENT_ID"],category="env",
                                  sensitive="true")
        self.AddWorkspaceVariable(workspace, "ARM_CLIENT_SECRET", os.environ["ARM_CLIENT_SECRET"], category="env",
                                  sensitive="true")
        self.AddWorkspaceVariable(workspace, "ARM_SUBSCRIPTION_ID", os.environ["ARM_SUBSCRIPTION_ID"], category="env",
                                  sensitive="true")
        self.AddWorkspaceVariable(workspace, "ARM_TENANT_ID", os.environ["ARM_TENANT_ID"], category="env",
                                  sensitive="true")


    def DeleteVariable(self, variable_id):
        request_uri = self.base_url + "/vars/" + variable_id
        return requests.delete(request_uri, headers=self.header)

API_Calls = TerraformAPICalls(organization="westpac-v2")
API_Calls.CreateWorkspace("dev2", "Westpac/tf-azure-core")
API_Calls.LoadLocalAzureCredentials("dev2")
API_Calls.LoadVariables("test.tfvars", "dev2")

