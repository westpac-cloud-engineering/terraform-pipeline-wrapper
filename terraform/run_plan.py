workplace = TerraformAPICalls(organization="westpac-v2", directory='C:\Repositories\Orchestration\Apps\A00001-Bamboo')
workplace.generate_workspaces()
workplace.load_local_azure_credentials("odev")
workplace.load_variables("odev")