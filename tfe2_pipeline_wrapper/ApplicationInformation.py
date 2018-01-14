import json
import os
import tarfile
import time
import consul
import jinja2
import git
import tempfile


class ApplicationInformation:
    def __init__(self, configuration_file):
        with open(configuration_file) as config:
            data = json.load(config)
            self.consul_information = data["consul"]
            self.deployment_information = data["deployment"]

        # Consul Application Key Paths
        self.base_app_key = "apps/" + self.deployment_information['id'] + "/"
        self.base_component_key = self.base_app_key + "deployments/" + self.deployment_information['component_name'] + "/"
        self.base_environment_key = self.base_component_key + self.deployment_information['environment'] + "/"

    def get_application_information_from_consul(self):
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

    @staticmethod
    def load_app_variables(TE2Vars, azure_client_secret):
        TE2Vars.delete_all_variables()
        url = "https://raw.githubusercontent.com/" + repository + "/" + branch + "/env/" + environment + ".tfvars"

        print("Getting Environment Variables from: " + url)
        variable_list = hcl.loads(requests.get(url).text)

        ## TODO: Replace with Vault Secrets Call
        TE2Vars.create_or_update_workspace_variable(
            key="azure_client_secret",
            value=azure_client_secret,
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

    def clone_repository_and_compress(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            git.Repo.clone_from('https://github.com/westpac-cloud-deployments/001_DemoApp_ComponentName.git', temp_directory)
            self.generate_meta_file(os.path.join(temp_directory, "Terraform_Configuration"))

            self.tar_configuration_contents(temp_directory) # Tar the Configuration Files


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