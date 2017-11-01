import json
import os

import consul
import hcl
import requests
import time

class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organization, directory, app_id, atlas_token=None, base_api_url=None):

        # Get Token from Environment Variable if not passed.
        atlas_token = os.environ["ATLAS_TOKEN"]
        self.header = {
            'Authorization': "Bearer " + atlas_token,
            'Content-Type': 'application/vnd.api+json'
        }

        self.app_id = app_id
        self.organization = organization
        self.directory = directory

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

    def get_workspace_id(self, workspace_name):
        linkable_repo_url = self.base_url + "/organizations/" + self.organization + "/workspaces"
        r = requests.get(url=linkable_repo_url, headers=self.header).text

        # Find the ID for the Repository that matches the repository name.
        for obj in json.loads(r)['data']:
            if obj["attributes"]["name"] == workspace_name:
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
                        "branch": branch,  # NOT CONFIGURABLE IN BETA. TO BE REPLACED WITH DEFAULT BRANCH
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

    def generate_workspaces(self, app_id, app_name, cost_centre, git_repository):
        c = consul.Consul(host=os.environ["CONSUL_ADDRESS"])

        # Write MetaFile to Consul
        base_keypath = "apps/" + self.app_id + "/"

        # Write MetaFile to Consul
        c.kv.put(base_keypath + "app_id", app_id)
        c.kv.put(base_keypath + "app_name", app_name)
        c.kv.put(base_keypath + "cost_centre", cost_centre)
        c.kv.put(base_keypath + "git_repository", git_repository)

        # Generate Workspaces from Environment Section of Meta
        for environment in self.environments:
            workspace_name = self.generate_workspace_name(environment)

            self.create_workspace(workspace_name, self.git_repository,
                                  self.environments[environment])
            c.kv.put(base_keypath + "workspaces/" + workspace_name, workspace_name)

    def get_run_status(self, run_id="run-jDDckmxjRA1rTXVx"):
        request_uri = self.base_url + "/runs/" + run_id
        data = json.loads(requests.get(request_uri, headers=self.header).text)
        return data['data']['attributes']['status']

    def discard_untriggered_plans(self, workspace_id):
        request_uri = self.base_url + "/workspaces/" + workspace_id + "/runs"
        # Get Status of all pending plans

        print("Discarding Untriggered Jobs")

        nothing_to_discard = False
        while not (nothing_to_discard):
            data = json.loads(requests.get(request_uri, headers=self.header).text)

            nothing_to_discard = True
            for obj in data['data']:

                # Delete Item
                if obj["attributes"]["status"] == "planned":
                    print("Discarding: " + obj["id"])
                    self.discard_plan(obj["id"])

                # More items left to Delete
                elif obj["attributes"]["status"] == "pending" or obj["attributes"]["status"] == "planning":
                    nothing_to_discard = False

    def discard_plan(self, run_id):
        request_uri = self.base_url + "/runs/" + run_id + "/actions/discard"
        data = {"comment": "Dropped by Jenkins Build"}

        requests.post(request_uri, headers=self.header, data=json.dumps(data)).text

    def create_run(self, workspace_id, destroy=False):

        # Untriggered plans must be discarded before creating a new one is queued.
        self.discard_untriggered_plans(workspace_id)

        request_uri = self.base_url + "/runs"

        data = {
            "data": {
                "attributes": {
                    "is-destroy": destroy
                },
                "type": "runs",
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    }
                }
            }
        }

        return_data = requests.post(request_uri, headers=self.header, data=json.dumps(data))

        print("Creating new Terraform run against: " + workspace_id)

        # Check if run can be created Successfully
        if str(return_data.status_code).startswith("2"):
            print("New Run: " + json.loads(return_data.text)['data']['id'])

            # Keep Checking until planning phase has finished
            planning = True
            status = "planning"
            changes_detected = False
            while planning:
                planning = False
                print("Job Status: Planning")
                time.sleep(5)

                request = json.loads(requests.get(
                    self.base_url + "/runs/" + json.loads(return_data.text)['data']['id'],
                    headers=self.header
                ).text)

                status = request['data']['attributes']['status']
                changes_detected = request['data']['attributes']['has-changes']
                if status == "planning":
                    planning = True

            # If Plan Failed
            if status == "errored":
                print("Job Status: Failed")
                print("Job Output")
                exit(1)

            # If Plan Succeeded, Check for Changes
            elif status == "planned":
                if not changes_detected:
                    print("No Changes Detected")
                    exit(0)  # Exit if no changes

                print("Changes Detected")
                with open('data.txt', 'w') as f:
                    json.dump({"run_id": json.loads(return_data.text)['data']['id']}, f, ensure_ascii=False)
                exit(2)

            exit(0)

        else:  # Else Fail Run
            print("Plan Failed: " + json.loads(return_data.text)["data"]["attributes"]["message"])
            exit(1)

    def apply_run(self, workplace_id, run_id, destroy=False):
        request_uri = self.base_url + "/runs/" + run_id + "/actions/apply"

        data = {
            "data": {
                "attributes": {
                    "is-destroy": destroy
                },
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workplace_id
                        }
                    }
                },
                "type": "runs"
            }
        }

        print("Applying Job: " + run_id)
        return_data = requests.post(request_uri, headers=self.header, data=json.dumps(data))

        if str(return_data.status_code).startswith("2"):

            # Keep Checking until planning phase has finished
            status = "applying"
            while status == "applying" or status == "queued":
                print("Job Status: applying changes")
                time.sleep(5)

                request = json.loads(requests.get(self.base_url + "/runs/" + run_id, headers=self.header).text)

                status = request['data']['attributes']['status']

            # If Plan Failed
            if status == "errored":
                print("Job Status: Failed")
                print("Job Output TBA")
                exit(1)

            # If Plan Succeeded, Check for Changes
            elif status == "applied":
                print("Job Status: Applied Successfully!")
                exit(0)

        else:  # Else Fail Run
            print("Apply Failed")
            exit(1)

workplace = TerraformAPICalls(organization="westpac-v2", directory='C:\Repositories\Orchestration\Apps\A00001-Bamboo', app_id="XXX001")
workspace_id = workplace.get_workspace_id("XXX001-odev-My_Test_Application")
#run_id = workplace.create_run(workspace_id)
apply = workplace.apply_run(workspace_id, "run-Z3obZbjZW29xERCz")


# workplace.discard_untriggered_plans(workspace_id)

# API_Calls.LoadLocalAzureCredentials("core-odev")
# API_Calls.LoadVariables("test.tfvars", "core-odev")
