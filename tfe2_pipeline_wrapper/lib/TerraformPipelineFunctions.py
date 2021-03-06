import jinja2
import tempfile
import json
import hcl
import te2_sdk.te2 as te2
import os
import tarfile
import time
import tfe2_pipeline_wrapper.lib.ConsulKeys as ConsulKeys
import zipfile
import requests
import io


class TFE2Actions:
    def __init__(self, configuration_map):
        self.tf_info = TFDeploymentInfoGenerator(configuration_map)
        self.azure_secret = configuration_map['azure_secret']  # TODO: REMOVE WHEN LINKED TO VAULT
        self.atlas_secret = configuration_map['atlas_secret']  # TODO: REMOVE WHEN LINKED TO VAULT

        self.TE2Client = te2.TE2Client(
            organisation=self.tf_info.deployment_information.terraform_tenant['organisation'],
            atlas_token=self.atlas_secret,
        )

    def generate_run(self, request_type, run_id=None):
        tf_ws_runs = te2.TE2WorkspaceRuns(
            client=self.TE2Client,
            workspace_name=self.tf_info.deployment_information.terraform_tenant['workspace']
        )

        run = tf_ws_runs.request_run(request_type=request_type, run_id=run_id, destroy=self.tf_info.deployment_information.destroy)

        if request_type == "plan":
            log_url = tf_ws_runs.get_plan_log(run_id=run["id"], request_type=request_type)
        elif request_type == "apply":
            log_url = tf_ws_runs.get_plan_log(run_id=run_id, request_type=request_type)
        else:
            raise SyntaxError("Invalid Request Type")

        with open('deployment_meta.json', 'w') as the_file:
            the_file.write(json.dumps(run))

        with open('deployment_' + request_type + '.log', 'w') as the_file:
            log = requests.get(log_url).text
            print("Log Output: ", log)

            the_file.write(log)

    def _load_app_variables(self, directory, tf_client):
        tfe2_vars = te2.TE2WorkspaceVariables(
            client=tf_client,
            workspace_name=self.tf_info.deployment_information.terraform_tenant['workspace']
        )

        tfe2_vars.delete_all_variables()

        variables_file_path = os.path.join(
            directory,
            "Terraform_Variables",
            str(self.tf_info.deployment_information.environment) + ".tfvars"
        )

        with open(variables_file_path, 'r') as var_file:
            variable_list = hcl.load(var_file)

            print("Uploading Secret - azurerm_client_secret: ##REDACTED##")
            tfe2_vars.create_or_update_workspace_variable(
                key="azurerm_client_secret",
                value=self.azure_secret,  # TODO: Replace with Vault Secrets Call
                hcl=False,
                sensitive=True
            )

            print("Uploading Application Variables from: " + str(self.tf_info.deployment_information.environment) + ".tfvars")
            for obj in variable_list:
                print(" - " + obj + ": " + str(variable_list[obj]))
                tfe2_vars.create_or_update_workspace_variable(
                    key=obj,
                    value=hcl.dumps(variable_list[obj]),
                    hcl=True
                )

    @staticmethod
    def _tar_configuration_contents(temp_directory):
        """
        Takes a TemporaryDirectory() class object, and returns a Tarred TemporaryFile()
        :param temp_directory:
        :return: Tar gzipped TemporaryFile()
        """
        configuration_files_tar = tempfile.TemporaryFile()

        with tarfile.open(fileobj=configuration_files_tar, mode='w:gz') as tar:
            tar.add(os.path.join(temp_directory, "Terraform_Configuration"), arcname='.')
        return configuration_files_tar

    def _download_config_and_unzip_from_github(self, repo, branch):
        uri = "https://github.com/" + repo + "/archive/" + branch + ".zip"
        print('Downloading Repository from: ' + uri)

        try:
            zip_ref = zipfile.ZipFile(io.BytesIO(requests.get(uri).content))
        except zipfile.BadZipFile:
            raise FileNotFoundError("Cannot find Repository URL. Most likely bad branch or tag.")
        temp_directory = tempfile.TemporaryDirectory()
        zip_ref.extractall(temp_directory.name)
        return temp_directory

    def generate_and_upload_configuration(self):
        repo = self.tf_info.deployment_information.git_repository

        te2_ws_config = te2.TE2WorkspaceConfigurations(
            client=self.TE2Client,
            workspace_name=self.tf_info.deployment_information.terraform_tenant['workspace']
        )

        temp_directory = self._download_config_and_unzip_from_github(
            repo=repo,
            branch=self.tf_info.deployment_information.branch_or_tag
        )
        repo_folder_name = os.listdir(temp_directory.name)[0] # Get Repository Folder Name

        temp_path = os.path.join(temp_directory.name, repo_folder_name)

        self._load_app_variables(temp_path, self.TE2Client)  # Uploads the configuration from Repository
        self.tf_info.generate_meta_file(os.path.join(temp_path, "Terraform_Configuration"))
        te2_ws_config.upload_configuration(
            self._tar_configuration_contents(temp_path)
        )

    # def trigger_plan_against_terraform_enterprise(self, TE2Client):


class TFOpenSourceActions:
    def __init__(self):
        print("This is a stub")


class TFDeploymentInfoGenerator:
    def __init__(self, configuration_map):
        self.consul_client = ConsulKeys.ConsulClient(
            address=configuration_map['consul']['address'],
            token=configuration_map['consul']['token'],
            dc=configuration_map['consul']['dc'],
            port=configuration_map['consul']['port']
        )
        self.deployment_information = ConsulKeys.ConsulApplicationDeploymentKeys(
            consul_client=self.consul_client,
            application_id=configuration_map['deployment']['id'],
            component_name=configuration_map['deployment']['component_name'],
            environment=configuration_map['deployment']['environment'],
            branch_or_tag=configuration_map['deployment']['branch_or_tag'],
            destroy=configuration_map['deployment']['destroy']
        )

    def _application_information_for_template(self):
        """ This function returns a set list of information from consul around an Application Deployment, based on its
        environment, application ID and component name
        :return: Map of Application attributes, including Name, Component_name, id, environment, data_classification & bcrm_id
        """
        return {
            'name': self.deployment_information.name,
            'component_name': self.deployment_information.name,
            'id': self.deployment_information.id,
            'environment': self.deployment_information.environment,
            'data_classification': "TBA",  # TODO : Handle missing keys
            'bcrm_id': self.deployment_information.bcrm_id,
        }

    def generate_meta_file(self, destination):
        job = {
            'generated_date': time.strftime("%x %X", time.gmtime()),
            'workspace_name': self.deployment_information.terraform_tenant['workspace']
        }

        provider_list = {
            'azure': self.deployment_information.get_azure_provider(),
            'aws': self.deployment_information.get_aws_provider()
        }

        env = jinja2.Environment(loader=jinja2.PackageLoader('tfe2_pipeline_wrapper', 'templates'))

        with open(os.path.join(destination, "meta.tf"), "wb") as fh:
            print("Generating Meta File:")
            meta_file = env.get_template("deployment_meta.tf.template").render(
                job=job,
                app=self._application_information_for_template(),
                provider_list=provider_list
            )
            print(meta_file)

            fh.write(meta_file.encode())

