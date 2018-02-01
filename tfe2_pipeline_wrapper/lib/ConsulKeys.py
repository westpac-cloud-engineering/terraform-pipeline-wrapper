import consul


class ConsulApplicationDeploymentKeys:
    def __init__(self, consul_client, application_id, component_name, environment, branch_or_tag, destroy):
        """
        This class returns application information, based on the deployments ApplicationID, DeploymentID and Component_Name
        :param consul_client: ConsulClient object instantiation
        :param application_id: Application ID in Consul
        :param component_name: The Component name in Consul
        :param environment:  The environment this deployment is referring to (e.g. dev/test/prod)
        """
        self.id = application_id
        self.component_name = component_name
        self.environment = environment
        self.branch_or_tag = branch_or_tag
        self.destroy = destroy

        self.consul_client = consul_client
        self.base_app_key = "apps/" + application_id + "/"
        self.base_component_key = self.base_app_key + "deployments/" + component_name + "/"
        self.base_environment_key = self.base_component_key + environment + "/"

        self.name = self.consul_client.get_consul_key(self.base_app_key + "app_name")
        self.bcrm_id = self.consul_client.get_consul_key(self.base_app_key + "bcrm")
        self.git_repository = self.consul_client.get_consul_key(self.base_component_key + "git_repository")

        self.data_classification = "TBA"

        self.azure_provider = self.get_azure_provider()
        self.aws_provider = self.get_aws_provider()
        self.terraform_tenant = self.get_terraform_tenant()

    def get_azure_provider(self):
        """
        Checks to see if Application Deployment is related to an Azure Tenancy, and if so, returns the corresponding
        information
        :return: A map containing a client_id, resource_group_name, subscription_id & tenant_id
        """
        try:
            subscription_key = self.consul_client.get_consul_key(self.base_environment_key + "azure/subscription_key")
        except KeyError:
            return None
        return {
            'client_id': self.consul_client.get_consul_key(self.base_environment_key + "azure/client_id"),
            'resource_group_name': self.consul_client.get_consul_key(self.base_environment_key + "azure/resource_group_name"),
            'subscription_id': self.consul_client.get_consul_key(subscription_key + "subscription_id"),
            'tenant_id': self.consul_client.get_consul_key(subscription_key + "tenant_id"),
        }

    def get_terraform_tenant(self):
        """

        :return:
        """
        tenant = 'poc'  # TODO: Remove hard-coding of Tenant ID
        try:
            workspace = self.consul_client.get_consul_key(self.base_environment_key + "terraform/tf_workspace")
        except KeyError:
            return None
        return {
            'workspace': workspace,
            'tenant': tenant,
            'organisation': self.consul_client.get_consul_key("shared_services/terraform/" + tenant + "/organisation")
        }

    @staticmethod
    def get_aws_provider():
        """
        Checks to see if Application Deployment is related to an Azure Tenancy, and if so, returns the corresponding
        information. This function has not been implemented and only returns None
        :return: None
        """
        return None


class ConsulClient:
    def __init__(self, address, port, token, dc):
        """
        Wrapper for the Consul Client, simplifying configuration.
        :param address:
        :param port:
        :param token:
        :param dc:
        """
        # Consul Application Key Paths
        self.consul_client = consul.Consul(host=address, port=port)
        self.consul_token = token
        self.consul_dc = dc

    def get_consul_key(self, key):
        """
        Returns value of key from Consul Server defined by Client Class
        :param key:
        :return:
        """
        try:
            val = self.consul_client.kv.get(
                str(key),
                token=self.consul_token,
                dc=self.consul_dc
            )[1]['Value'].decode('utf-8')
        except TypeError:
            return "KEY_NOT_FOUND"
        return val


