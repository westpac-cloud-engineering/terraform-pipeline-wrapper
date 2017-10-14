from .modules import *


# Create Space
API_Calls = TerraformAPICalls(organization="westpac-v2")
#API_Calls.CreateWorkspace("core-odev", "Westpac/tf-azure-core")
API_Calls.LoadLocalAzureCredentials("core-odev")
API_Calls.LoadVariables("test.tfvars", "core-odev")
