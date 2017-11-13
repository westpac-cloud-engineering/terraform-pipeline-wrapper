import json
import hcl
import requests
import time
import build_info


class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organisation, app_id, component_name, workspace_name, environment, repository, secrets, base_api_url=None):
        self.header = {
            'Authorization': "Bearer " + secrets["atlas_token"],
            'Content-Type': 'application/vnd.api+json'
        }

        self.app_id = app_id
        self.environment = environment
        self.component_name = component_name
        self.organisation = organisation
        self.secrets = secrets
        self.workspace_name = workspace_name
        self.repository = repository
        self.workspace_id = self.get_workspace_id()

    def add_workspace_variable(self, key, value, category="terraform", sensitive=False,
                               hcl=False, variable_id=None):
        variable_url = self.base_url + "/vars"
        data = {
            "data": {
                "type": "vars",
                "attributes": {
                    "key": key,
                    "value": value,
                    "category": category,
                    "sensitive": sensitive
                }
            }
        }

        if hcl==True:
            data['data']['attributes']['hcl'] = True

        # If new variable, filter to the correct workspace
        if not variable_id:
            data["filter"] = {
                "organization": {
                    "username": self.organisation
                },
                "workspace": {
                    "name": self.workspace_name
                }
            }

            return (requests.post(url=variable_url, data=json.dumps(data), headers=self.header).status_code)

        # Else find the existing one using the variable ID
        else:
            data["data"]["id"] = variable_id
            return requests.patch(url=variable_url + "/" + variable_id, data=json.dumps(data), headers=self.header)

    def get_workspace_id(self):
        linkable_repo_url = self.base_url + "/organizations/" + self.organisation + "/workspaces"
        r = requests.get(url=linkable_repo_url, headers=self.header).text

        # Find the ID for the Repository that matches the repository name.
        for obj in json.loads(r)['data']:
            if obj["attributes"]["name"] == self.workspace_name:
                return obj["id"]

    def delete_variables(self):
        request_uri = self.base_url + "/vars?filter[organization][username]=" + self.organisation + "&filter[workspace][name]=" + self.workspace_name

        data = requests.get(request_uri, headers=self.header).text

        # Delete Variables
        for tfvar in json.loads(data)["data"]:
            self.delete_variable(tfvar["id"])

    def load_secrets(self):
        if "environment_variables" in self.secrets:
            for obj in self.secrets["environment_variables"]:
                self.add_workspace_variable(obj, self.secrets["environment_variables"][obj], category="env", hcl=False, sensitive=True)

        if "workspace_variables" in self.secrets:
            for obj in self.secrets["workspace_variables"]:
                self.add_workspace_variable(obj, self.secrets["workspace_variables"][obj], category="env", hcl=False, sensitive=True)

    def load_app_variables(self, directory):
        url = "https://raw.githubusercontent.com/" + self.repository + "/env/" + self.environment + "/env/" + self.environment +".tfvars"

        print("Getting Environment Variables from: " + url)
        variable_list = hcl.loads(requests.get(url).text)
        for obj in variable_list:
            self.add_workspace_variable(obj, hcl.dumps(variable_list[obj]), hcl=True)

        self.add_workspace_variable("app_id", self.app_id, hcl=False)

    # Environment Variables from file
    def load_environment_variables(self, directory):
        with open(directory + "environment_variables.json", 'r') as fp:
            variable_list = json.load(fp)
            for obj in variable_list:
                self.add_workspace_variable(obj, variable_list[obj], category="env",
                                            sensitive=True)

    def delete_variable(self, variable_id):
        request_uri = self.base_url + "/vars/" + variable_id
        return requests.delete(request_uri, headers=self.header)

    def get_run_status(self, run_id="run-jDDckmxjRA1rTXVx"):
        request_uri = self.base_url + "/runs/" + run_id
        data = json.loads(requests.get(request_uri, headers=self.header).text)
        return data['data']['attributes']['status']

    def discard_untriggered_plans(self):
        request_uri = self.base_url + "/workspaces/" + self.workspace_id + "/runs"
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

        return requests.post(request_uri, headers=self.header, data=json.dumps(data)).text

    def create_run(self, destroy=False):

        # Untriggered plans must be discarded before creating a new one is queued.
        self.discard_untriggered_plans()
        self.delete_variables()
        self.load_secrets()
        self.load_app_variables("")


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
                            "id": self.workspace_id
                        }
                    }
                }
            }
        }

        return_data = requests.post(request_uri, headers=self.header, data=json.dumps(data))

        print("Creating new Terraform run against: " + self.workspace_id)

        self.delete_variables()

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
                if changes_detected:
                    print("Changes Detected")
                    with open('data.json', 'w') as f:
                        json.dump({'status': "changed", 'run_id': json.loads(return_data.text)['data']['id']}, f,
                                  ensure_ascii=False)

                else:
                    print("No Changes Detected")
                    with open('data.json', 'w') as f:
                        json.dump({"status": "unchanged", "run_id": json.loads(return_data.text)['data']['id']}, f,
                                  ensure_ascii=False)

            exit(0)

        else:  # Else Fail Run
            print("Plan Failed: " + json.loads(return_data.text)["data"]["attributes"]["message"])

            with open('data.json', 'w') as f:
                json.dump({"status": "failed", "run_id": json.loads(return_data.text)['data']['id']}, f,
                          ensure_ascii=False)

    def apply_run(self, run_id, destroy=False):

        # Reload secrets into Terraform.
        self.delete_variables()
        self.load_secrets()
        self.load_app_variables("")

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
                            "id": self.workspace_id
                        }
                    }
                },
                "type": "runs"
            }
        }

        print("Applying Job: " + run_id)
        return_data = requests.post(request_uri, headers=self.header, data=json.dumps(data))

        # Url endpoint not available
        # log_read_url = json.loads(return_data.text)['data']['attributes']['log-read-url']

        if str(return_data.status_code).startswith("2"):

            # Keep Checking until planning phase has finished
            status = "applying"
            while status == "applying" or status == "queued":
                print("Job Status: Applying changes")
                time.sleep(5)

                request = json.loads(requests.get(self.base_url + "/runs/" + run_id, headers=self.header).text)

                status = request['data']['attributes']['status']

            # Get Log File
            # print("Log File Directory:" + log_read_url)
            # print(requests.get(log_read_url, headers=self.header).text)

            self.delete_variables()

            # If Plan Failed
            if status == "errored":
                with open('data.json', 'w') as f:
                    json.dump({"status": "failed"}, f,
                              ensure_ascii=False)

            # If Plan Succeeded, Check for Changes
            elif status == "applied":
                with open('data.json', 'w') as f:
                    json.dump({"status": "applied"}, f,
                              ensure_ascii=False)

        else:  # Else Fail Run
            print("Apply Failed")
            with open('data.json', 'w') as f:
                json.dump({"status": "errored"}, f,
                          ensure_ascii=False)

