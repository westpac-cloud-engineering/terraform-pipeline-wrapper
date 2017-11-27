import argparse
from te2_sdk import te2
import json
import consul
import hcl
import requests

p = argparse.ArgumentParser()
p.add_argument('request_type')
p.add_argument('app_id')
p.add_argument('component_name')
p.add_argument('environment')
p.add_argument('atlas_token')
p.add_argument('destroy')
p.add_argument('run_id')


class BuildInformation:
    def __init__(self, app_id, component_name, environment, consul_address, consul_token="", consul_dc=""):

        # Consul Information
        self.consul_address = consul_address
        self.consul_token = consul_token
        self.consul_dc = consul_dc

        self.component_name = component_name
        self.environment = environment
        self.app_id = app_id

        self.base_app_key = "apps/" + app_id + "/"
        self.base_component_key = self.base_app_key + "/pipelines/" + component_name + "/"
        self.base_environment_key = self.base_component_key + environment + "/"

        # Get info from consul
        self.tf_workspace = self.get_consul_key(self.base_environment_key + "tf_workspace")
        self.tf_organisation = self.get_consul_key(
            "shared_services/terraform/" +
            self.get_consul_key(self.base_environment_key + "tf_tenant") +
            "/organisation"
        )
        self.tf_repository = self.get_consul_key(self.base_component_key + "git_repository")

    def get_consul_key(self, key):
        c = consul.Consul(host=self.consul_address)
        return c.kv.get(str(key), token=self.consul_token, dc=self.consul_dc)[1]['Value'].decode('utf-8')

def load_app_variables(TE2Vars, repository, branch, environment, app_id):
    TE2Vars.delete_all_variables()
    url = "https://raw.githubusercontent.com/" + repository + "/" + branch + "/env/" + environment +".tfvars"

    print("Getting Environment Variables from: " + url)
    variable_list = hcl.loads(requests.get(url).text)
    TE2Vars.create_or_update_workspace_variable(
        key="app_id",
        value=app_id,
        hcl=False
    )

    for obj in variable_list:
        TE2Vars.create_or_update_workspace_variable(
            key=obj,
            value=hcl.dumps(variable_list[obj]),
            hcl=True
        )


def main(request_type, app_id, component_name, environment, run_id, atlas_token, destroy=False):

    info = BuildInformation(
        app_id=app_id,
        component_name=component_name,
        environment=environment,
        consul_address="consul.australiaeast.cloudapp.azure.com"
    )

    tf_client = te2.TE2Client(
        organisation=info.tf_organisation,
        atlas_token=atlas_token,
        base_url="https://atlas.hashicorp.com/api/v2"
    )

    tf_ws_vars = te2.TE2WorkspaceVariables(
        client=tf_client,
        workspace_name=info.tf_workspace
    )

    tf_ws_runs = te2.TE2WorkspaceRuns(
        client=tf_client,
        workspace_name=info.tf_workspace
    )

    load_app_variables(
        TE2Vars=tf_ws_vars,
        repository=info.tf_repository,
        branch="env/" + environment,
        environment=environment,
        app_id=app_id,
    )

    run = tf_ws_runs.request_run(request_type=request_type, destroy=destroy)
    log_url = tf_ws_runs.get_plan_log(run_id=run["id"], request_type=request_type)

    with open( 'data.json', 'w') as the_file:
        the_file.write(json.dumps(run))

    # Files to be archived with Jenkins Job
    with open( run['id'] + '-' + request_type + '.json', 'w') as the_file:
        the_file.write(json.dumps(run))

    with open( run['id'] + "-" + request_type + '.log', 'w') as the_file:
        the_file.write(requests.get(log_url).text)



if __name__ == "__main__":
    args = p.parse_args()
    main(
        args.request_type,
        args.app_id,
        args.component_name,
        args.environment,
        args.run_id,
        args.atlas_token,
        args.destroy
    )