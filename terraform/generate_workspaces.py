import terraform.terraform_class as tf

workplace = tf.TerraformAPICalls(organization="westpac-v2", directory='C:\Repositories\Orchestration\Apps\A00001-Bamboo')
workspace_id = workplace.get_workspace_id("XXX001-odev-My_Test_Application")
run_id = workplace.create_run(workspace_id)