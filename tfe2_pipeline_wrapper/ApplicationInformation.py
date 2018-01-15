import json
import os
import tarfile
import time
import consul
import jinja2
import git
import tempfile
import hcl
import te2_sdk.te2 as te2
import requests


class ApplicationInformation:
    def __init__(self, configuration_file):
        with open(configuration_file) as config:
            data = json.load(config)
            self.consul_information = data["consul"]
            self.deployment_information = data["deployment"]
            self.atlas_secret = data['atlas_secret']
            self.azure_secret = data['azure_secret']

        # Consul Application Key Paths
        self.base_app_key = "apps/" + self.deployment_information['id'] + "/"
        self.base_component_key = self.base_app_key + "deployments/" + self.deployment_information['component_name'] + "/"
        self.base_environment_key = self.base_component_key + self.deployment_information['environment'] + "/"

    def get_application_information_from_consul(self):
        """This function returns a set list of information from consul around an Application Deployment, based on its
        environment, application ID and component name
        :return: Map of Application attributes, including Name, Component_name, id, environment, data_classification & bcrm_id
        """

        return {
            'name': self._get_consul_key(self.base_app_key + "app_name"),
            'component_name': self.deployment_information['component_name'],
            'id': self.deployment_information['id'],
            'environment': self.deployment_information['environment'],
            'data_classification': "TBA",
            'bcrm_id': self._get_consul_key(self.base_app_key + "bcrm"),
        }

    def get_terraform_tenant_information(self):
        tenant = "poc" # TODO: Remove Hardcoding of Tenant ID
        return {
            'workspace': self._get_consul_key(self.base_environment_key + "terraform/tf_workspace"),
            'tenant': tenant,
            'organisation': self._get_consul_key("shared_services/terraform/" + tenant + "/organisation")
        }

    def get_azure_provider(self):
        try:
            subscription_key = self._get_consul_key(self.base_environment_key + "azure/subscription_key")
        except:
            return None
        return {
            'client_id': self._get_consul_key(self.base_environment_key + "azure/client_id"),
            'resource_group_name': self._get_consul_key(self.base_environment_key + "azure/resource_group_name"),
            'subscription_id': self._get_consul_key(subscription_key + "subscription_id"),
            'tenant_id': self._get_consul_key(subscription_key + "tenant_id"),
        }

    def load_app_variables(self, directory, tf_client):
        TE2Vars = te2.TE2WorkspaceVariables(
            client=tf_client,
            workspace_name=self.get_terraform_tenant_information()['workspace']
        )

        TE2Vars.delete_all_variables()
        variables_file_path = os.path.join(directory, "Terraform_Variables", self.deployment_information['environment'] + ".tfvars")
        with open(variables_file_path, 'r') as var_file:
            variable_list = hcl.load(var_file)

            # TODO: Replace with Vault Secrets Call
            TE2Vars.create_or_update_workspace_variable(
                key="azurerm_client_secret",
                value=self.azure_secret,
                hcl=False,
                sensitive=True
            )

            for obj in variable_list:
                TE2Vars.create_or_update_workspace_variable(
                    key=obj,
                    value=hcl.dumps(variable_list[obj]),
                    hcl=True
                )

    def get_aws_provider(self):
        return None # TODO: Module to get aws provider information

    def _get_consul_key(self, key):
        c = consul.Consul(host=self.consul_information['address'], port=self.consul_information['port'])
        return c.kv.get(
            str(key),
            token=self.consul_information['token'],
            dc=self.consul_information['dc']
        )[1]['Value'].decode('utf-8')

    @staticmethod
    def tar_configuration_contents(temp_directory):
        # Compress Files into Temporary Tar file
        configuration_files_tar = tempfile.TemporaryFile()
        with tarfile.open(fileobj=configuration_files_tar, mode='w:') as tar:
            tar.add(os.path.join(temp_directory, "Terraform_Configuration"), arcname=os.path.sep)

        return configuration_files_tar

    def generate_and_upload_configuration(self, TE2Client):
        TE2WSConfigs = te2.TE2WorkspaceConfigurations(
            client=TE2Client,
            workspace_name=self.get_terraform_tenant_information()['workspace']
        )

        with tempfile.TemporaryDirectory() as temp_directory:
            git.Repo.clone_from('https://github.com/westpac-cloud-deployments/001_DemoApp_ComponentName.git', temp_directory)

            self.load_app_variables(temp_directory, TE2Client)  # Uploads the configuration from Repository
            self.generate_meta_file(os.path.join(temp_directory, "Terraform_Configuration"))
            TE2WSConfigs.upload_configuration(
                self.tar_configuration_contents(temp_directory)
            )

    def generate_meta_file(self, destination):
        job = {
            'generated_date': time.strftime("%x %X", time.gmtime()),
            'workspace_name': self._get_consul_key(self.base_environment_key + "terraform/tf_workspace")
        }

        provider_list = {
            'azure': self.get_azure_provider(),
            'aws': self.get_aws_provider()
        }

        env = jinja2.Environment(loader=jinja2.PackageLoader('tfe2_pipeline_wrapper', 'templates'))

        with open(os.path.join(destination, "meta.tf"), "wb") as fh:
            print("Generating Meta File")
            fh.write(env.get_template("deployment_meta.tf.template").render(
                job=job,
                app=self.get_application_information_from_consul(),
                provider_list=provider_list
            ).encode())

    def raise_servicenow_change(self):
        # Set the request parameters
        url = 'https://wbchpaaspoc.service-now.com/api/now/table/change_request'

        # Eg. User name="admin", Password="admin" for this code sample.
        user = 'rory.chatterton'
        pwd = ''

        # Set proper headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        data = {
            'short_description': 'Test Change',
            'category': 'Terraform_Automated_Change',
            'description': "Automated change generated by Jenkins.",
            'configuration_item': 'A00031E-Prod-ServiceHubApp'
        }

        # Do the HTTP request
        response = requests.post(url, auth=(user, pwd), headers=headers, data=json.dumps(data))

        # Check for HTTP codes other than 200
        if response.status_code != 200:
            print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
            exit()

        # Decode the JSON response into a dictionary and use the data
        print(response.json())
