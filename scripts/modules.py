import requests
import json
import os
import hcl
import consul


class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organization, directory, atlas_token=None, base_api_url=None):

        # Get Token from Environment Variable if not passed.
        atlas_token = os.environ["ATLAS_TOKEN"]
        self.header = {
            'Authorization': "Bearer " + atlas_token,
            'Content-Type': 'application/vnd.api+json'
        }

        self.organization = organization
        self.directory = directory

        # Read Metafile
        with open(self.directory + "/meta.tfvars", 'r') as fp:
            variable_list = hcl.load(fp)

            self.app_id = variable_list["app_id"]
            self.app_name = variable_list["app_name"]
            self.cost_centre = variable_list["cost_centre"]
            self.git_repository = variable_list["git_repository"]
            self.environments = variable_list["environments"]

    def get_workspaces(self):
        workspaces_url = self.base_url + "/organizations/" + self.organization + "/workspaces"
        return requests.get(workspaces_url, headers=self.header)

    def get_linkable_repo_id(self, repo_name):
        linkable_repo_url = self.base_url + "/linkable-repos?filter[organization][username]=" + self.organization
        r = requests.get(url=linkable_repo_url, headers=self.header).text

        # Find the ID for the Repository that matches the repository name.
        for obj in json.loads(r)['data']:
            if obj["attributes"]["name"] == repo_name:
                return obj["id"]

    def create_workspace(self, workspace_title, repo_name, branch="master"):
        repo_id = self.get_linkable_repo_id(repo_name)
        workspaces_url = self.base_url + "/compound-workspaces"

        # Build Request
        data = {
            "data": {
                "type": "compound-workspaces",
                "attributes": {
                    "name": workspace_title,
                    "working_directory": "",
                    "linkable-repo-id": repo_id,
                    "ingress-trigger-attributes": {
                        "default-branch": "true",  # NOT CONFIGURABLE IN BETA. TO BE REPLACED WITH DEFAULT BRANCH
                        "branch": branch,          # NOT CONFIGURABLE IN BETA. TO BE REPLACED WITH DEFAULT BRANCH
                        "vcs_root_path": "",
                        "ingress-submodules": "false",
                    }
                }
            }
        }

        # Make Request
        return requests.post(url=workspaces_url, data=json.dumps(data), headers=self.header)

    def add_workspace_variable(self, workspace, key, value, category="terraform", sensitive="false",
                               hcl="false", variable_id=None):
        variable_url = self.base_url + "/vars"

        data = {
            "data": {
                "type": "vars",
                "attributes": {
                    "key": key,
                    "value": value,
                    "category": category,
                    "hcl": hcl,
                    "sensitive": sensitive
                }
            }
        }

        # If new variable, filter to the correct workspace
        if not variable_id:
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

    def load_variables(self, environment):
        workspace_name = self.generate_workspace_name(environment)
        request_uri = self.base_url + "/vars?filter[organization][username]=" + self.organization + "&filter[workspace][name]=" + workspace_name

        data = requests.get(request_uri, headers=self.header).text

        # Delete all the existing (Non-Environment) variables
        for tfvar in json.loads(data)["data"]:
            if tfvar["attributes"]["category"] == "terraform":
                self.delete_variable(tfvar["id"])

        with open(self.directory + "/env/" + environment + ".tfvars", 'r') as fp:
            variable_list = hcl.load(fp)
            for obj in variable_list:
                self.add_workspace_variable(workspace_name, obj, hcl.dumps(variable_list[obj]), hcl="true")

        self.add_workspace_variable(workspace_name, "app_id", self.app_id, hcl="false")

    def load_local_azure_credentials(self, environment):
        workspace = self.generate_workspace_name(environment)

        self.add_workspace_variable(workspace, "ARM_CLIENT_ID", os.environ["ARM_CLIENT_ID"], category="env",
                                    sensitive="true")
        self.add_workspace_variable(workspace, "ARM_CLIENT_SECRET", os.environ["ARM_CLIENT_SECRET"], category="env",
                                    sensitive="true")
        self.add_workspace_variable(workspace, "ARM_SUBSCRIPTION_ID", os.environ["ARM_SUBSCRIPTION_ID"], category="env",
                                    sensitive="true")
        self.add_workspace_variable(workspace, "ARM_TENANT_ID", os.environ["ARM_TENANT_ID"], category="env",
                                    sensitive="true")

    def delete_variable(self, variable_id):
        request_uri = self.base_url + "/vars/" + variable_id
        return requests.delete(request_uri, headers=self.header)

    def generate_workspace_name(self, environment):
        return (self.app_id + "-" + environment + "-" + self.app_name).replace(" ", "_")

    def generate_workspaces(self):
        c = consul.Consul(host=os.environ["CONSUL_ADDRESS"])

        # Write MetaFile to Consul
        base_keypath = "apps/" + self.app_id + "/"

        # Write MetaFile to Consul
        c.kv.put(base_keypath + "app_id", self.app_id)
        c.kv.put(base_keypath + "app_name", self.app_name)
        c.kv.put(base_keypath + "cost_centre", self.cost_centre)
        c.kv.put(base_keypath + "git_repository", self.git_repository)

        # Generate Workspaces from Environment Section of Meta
        for environment in self.environments:
            workspace_name = self.generate_workspace_name(environment)

            self.create_workspace(workspace_name, self.git_repository,
                                  self.environments[environment])
            c.kv.put(base_keypath + "workspaces/" + workspace_name, workspace_name)

workplace = TerraformAPICalls(organization="westpac-v2", directory='C:/repositories/Orchestration/XXX001-TestApp01')
workplace.generate_workspaces()
workplace.load_local_azure_credentials("odev")
workplace.load_variables("odev")


# API_Calls.LoadLocalAzureCredentials("core-odev")
# API_Calls.LoadVariables("test.tfvars", "core-odev")
