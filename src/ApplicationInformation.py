import consul
import io, os, tarfile
class ApplicationInformation:
    def __init__(self, app_id, component_name, environment, consul_address, consul_token="", consul_dc=""):

        # Consul Information
        self.consul_address = consul_address
        self.consul_token = consul_token

        self.component_name = component_name
        self.environment = environment
        self.app_id = app_id

        self.base_app_key = "apps/" + app_id + "/"
        self.base_component_key = self.base_app_key + "components/" + component_name + "/"
        self.base_environment_key = self.base_component_key + environment + "/"

        # Get info from consul
        print (self.base_environment_key + "terraform/workspace")
        self.tf_workspace = self.get_consul_key(self.base_environment_key + "terraform/workspace")
        self.tf_organisation = self.get_consul_key(
            "shared_services/terraform/" +
            self.get_consul_key(self.base_environment_key + "terraform/tenant") +
            "/organisation"
        )
        self.tf_repository = self.get_consul_key(self.base_component_key + "git_repository")

    def get_consul_key(self, key):
        c = consul.Consul(host=self.consul_address)
        return c.kv.get(str(key), token=self.consul_token, dc=self.consul_dc)[1]['Value'].decode('utf-8')


    # TODO: This function
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
