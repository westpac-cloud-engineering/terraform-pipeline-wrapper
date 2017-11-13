import os
import consul
import create_project.jenkins_requests as jenkins
import create_project.terraform_requests as terraform

# Defines the overarching application wrapper for Jenkins/Consul/Terraform/Github
class ApplicationArchetype:
    def __init__(self, app_id, app_name, consul_address, consul_token="", consul_dc=""):
        self.app_id = app_id
        self.consul_address = consul_address
        self.consul_token = consul_token
        self.consul_dc = consul_dc
        self.app_base_key = "apps/" + self.app_id
        self.app_name = app_name

    # Take a map of key/values and create in consul.
    def create_consul_keys(self, kvs):
        c = consul.Consul(host=self.consul_address)

        for key in kvs:
            c.kv.put(key, kvs[key], token=self.consul_token, dc=self.consul_dc)

    def get_consul_key(self, key):
        c = consul.Consul(host=self.consul_address)
        print("key: " + key)
        return c.kv.get(str(key), token=self.consul_token, dc=self.consul_dc)[1]['Value'].decode('utf-8')

    # Create Base Application Keys in Consul
    def create_consul_application_keys(self, cost_centre, bcrm):

        print("Creating Consul Application Keys")

        kvs = {
            self.app_base_key + "/cost_centre": cost_centre,
            self.app_base_key + "/bcrm": bcrm,
            self.app_base_key + "/app_name": self.app_name,
        }

        self.create_consul_keys(kvs)

    def create_application_pipelines(self, components):

        for component in components:

            # Create Keys
            jenkins_component_key = "/job/" + self.app_id + "/job/" + component["name"]
            pipelines_key = self.app_base_key + "/pipelines/" + component["name"] + "/"

            # Create Jenkins Class
            jenkins_calls = jenkins.JenkinsCalls(base_url="jenkins.wbc-cloud-poc.com", username=os.environ['JENKINS_USERNAME'],
                                         password=os.environ['JENKINS_PASS'])

            # Create Folders
            print("Creating Jenkins Folders")
            jenkins_calls.create_jenkins_folder(name=self.app_id, display_name=self.app_id + " - " + self.app_name)
            jenkins_calls.create_jenkins_folder(name=component["name"], display_name=component["name"],
                                                sub_key="/job/" + self.app_id)

            # Create Consul Application Component Key
            print("Creating Consul Application: Component Keys")
            self.create_consul_keys({pipelines_key + "/git_repository": component['pipeline_repository']})

            # Create Pipelines
            for env in component['deployment_environments']:
                branch_name = "env/" + env['name']

                # Create Jenkins Pipeline
                if component['pipeline_type'] == "jenkins" :
                    jenkins_job_name = jenkins_calls.create_jenkins_pipeline_job(
                        app_id=self.app_id,
                        component_pipelines_name=component["name"],
                        environment=env['name'],
                        jf_branch="",
                        jf_path="",
                        jf_url="",
                        sub_key=jenkins_component_key
                    )

                # Create Terraform Pipeline
                terraform_calls = terraform.TerraformAPICalls(
                    organization=self.get_consul_key("shared_services/terraform/" + env['terraform']['tf_tenant'] + "/organisation"),
                    app_id=self.app_id,
                    component_name=component["name"],
                    atlas_token=None,
                )

                print(terraform_calls.get_git_oauth_token())
                terraform_job_name = terraform_calls.create_workspace(
                    environment=env['name'],
                    repo_name=component['pipeline_repository'],
                    branch=branch_name
                )

                # Create Keys
                kvs = {
                    pipelines_key + env['name'] + "/git_branch": branch_name,
                    pipelines_key + env['name'] + "/jenkins_job_url": jenkins_job_name,
                    pipelines_key + env['name'] + "/tf_tenant": env['terraform']['tf_tenant'],
                    pipelines_key + env['name'] + "/tf_workspace": terraform_job_name,
                    pipelines_key + env['name'] + "/production_flag": str(env['production_environment'])
                }

                self.create_consul_keys(kvs)

