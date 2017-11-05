class TerraformAPICalls():
    base_url = "https://atlas.hashicorp.com/api/v2"

    def __init__(self, organization, app_id, atlas_token=None, base_api_url=None):

        # Get Token from Environment Variable if not passed.
        atlas_token = os.environ["ATLAS_TOKEN"]
        self.header = {
            'Authorization': "Bearer " + atlas_token,
            'Content-Type': 'application/vnd.api+json'
        }

        self.app_id = app_id
        self.organization = organization

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
