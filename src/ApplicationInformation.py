import io, os, tarfile
import consul

class ApplicationInformation:
    def __init__(self, app_id, component_name, environment, consul_address, consul_token="", consul_dc=""):

        # Application Information
        self.component_name = component_name
        self.environment = environment
        self.app_id = app_id
        self.consul_address = consul_address
        self.consul_token = consul_token
        self.consul_dc = consul_dc

        self.get_application_information_from_consul()

    def get_application_information_from_consul(self):
        # Consul Application Key Paths
        self.base_app_key = "apps/" + self.app_id + "/"
        self.base_component_key = self.base_app_key + "components/" + self.component_name + "/"
        self.base_environment_key = self.base_component_key + self.environment + "/"

        # Get Deployment information from Consul
        self.tf_repository = self._get_consul_key(self.base_component_key + "git_repository")
        self.tf_workspace = self._get_consul_key(self.base_environment_key + "terraform/workspace")
        self.tf_tenant = self._get_consul_key(self.base_environment_key + "terraform/tenant")

        self.tf_organisation = self._get_consul_key(
            "shared_services/terraform/" +
             self.tf_tenant +
            "/organisation"
        )

    def _get_consul_key(self, key):
        c = consul.Consul(host=self.consul_address)
        return c.kv.get(str(key), token=self.consul_token, dc=self.consul_dc)[1]['Value'].decode('utf-8')

    # TODO: This Function to compress files in memory
    @staticmethod
    def _compress_files_in_memory(source_directory="/"):
        """ Returns a tar file, in memory as an IOStream

        This object is held in memory to reduce the likelihood of secrets being written to disk.

        :param source_directory: Source Directory which needs to be tarred
        :return: IOStream
        """

        tar_output = io.StringIO()

        with tarfile.open("configuration_files.tar.gz", "w:gz") as tar:
            tar.add(source_directory, arcname=os.path.basename(source_directory))
        return str(source_directory + "configuration_files.tar.gz")

    def _validate_application_archetype_format(self):
        return False


class GenerateApplicationArchetype:
    def __init__(self, directory, application_name):
        self.directory = directory
        self.application_name = application_name

    def clone_application_archetype(self):
        return True # TODO: Get Folder from Git Repository

    def _generate_jenkinsfile(self):
        return False # TODO: Generate JenkinsFile

    def _generate_readme_contents(self):
        return False # TODO: Generate README Contents