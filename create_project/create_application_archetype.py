import json
import os
import consul
import requests
from jinja2 import Environment, PackageLoader


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

    # Create Base Application Keys in Consul
    def create_consul_application_keys(self, cost_centre, bcrm):

        print("Creating Consul Application Keys")

        kvs = {
            self.app_base_key + "/cost_centre": cost_centre,
            self.app_base_key + "/bcrm": bcrm,
            self.app_base_key + "/app_name": self.app_name,
        }

        self.create_consul_keys(kvs)

    def create_jenkins_application_deployment(self, git_repository, component_pipelines_name, environments):

        # Create Keys
        jenkins_component_key = "/job/" + self.app_id + "/job/" + component_pipelines_name
        pipelines_key = self.app_base_key + "/pipelines/" + component_pipelines_name

        # Create Jenkins Application Folder
        jenkins_calls = JenkinsCalls(base_url="jenkins.wbc-cloud-poc.com", username=os.environ['JENKINS_USERNAME'],
                                     password=os.environ['JENKINS_PASS'])

        # Create Folders
        print("Creating Jenkins Folders")
        jenkins_calls.create_jenkins_folder(name=self.app_id, display_name=self.app_id + " - " + self.app_name)
        jenkins_calls.create_jenkins_folder(name=component_pipelines_name, display_name=component_pipelines_name,
                                            sub_key="/job/" + self.app_id)

        # Create Consul Application Component Key
        print("Creating Consul Application: Component Keys")
        self.create_consul_keys({pipelines_key + "/git_repository": git_repository})

        # Create Pipelines
        for env in environments:
            # Create Jenkins Pipeline
            jenkins_job_name = jenkins_calls.create_jenkins_pipeline_job(self.app_id,
                                                                         component_pipelines_name,
                                                                         env,
                                                                         sub_key=jenkins_component_key)

            # Create Terraform Pipeline
            terraform_job_name = "stub"

            # Create Keys
            kvs = {
                pipelines_key + env['env'] + "/git_branch": "env/" + env,
                pipelines_key + env['env'] + "/jenkins_job_url": jenkins_job_name,
                pipelines_key + env['env'] + "/tf_tenant": env['tf_tenant'],
                pipelines_key + env['env'] + "/tf_workspace": terraform_job_name,
                pipelines_key + env['env'] + "/production_flag": env['production_flag']
            }
            self.create_consul_keys(kvs)


class JenkinsCalls:

    def __init__(self, base_url, username, password):
        self.base_url = "https://" + username + ":" + password + "@" + \
              base_url

    def get_crumb(self):
        url = self.base_url + '/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'

        return dict(s.split(':') for s in [requests.get(url=url).text])

    def create_jenkins_pipeline_job(self, app_id, component_pipelines_name, environment, sub_key=""):

        # Generate request variables
        pipeline_full_name = app_id + "/" + component_pipelines_name + "/" + environment
        url = self.base_url + sub_key + "/createItem?name=" + component_pipelines_name + "-" + environment

        print("Creating Job: " + pipeline_full_name)

        # Generate Template
        template = Environment(loader=PackageLoader('create_project', 'jenkins_jobs')).get_template('terraform_default.xml')
        pipeline_info = {
            "displayName": app_id + ": " + component_pipelines_name + " - " + environment,
            "app_id": app_id
        }

        # Create Jobs
        headers = {"Content-Type": "application/xml", **self.get_crumb()}
        request = requests.post(url=url, headers=headers, data=template.render(pipeline_info=pipeline_info))

        return pipeline_full_name

    # Create Folder in Jenkins
    def create_jenkins_folder(self, name, display_name, sub_key=""):
        print("Creating Folder: " + display_name)

        # Generate Template
        headers = {"Content-Type": "application/xml", **self.get_crumb()}
        template = Environment(loader=PackageLoader('create_project', 'jenkins_jobs')).get_template('jenkins_folder.xml')
        folder_info = {
            "displayName": display_name,
        }

        url = self.base_url + sub_key + "/createItem?name=" + name

        return requests.post(url=url, headers=headers, data=template.render(folder_info=folder_info)).status_code
