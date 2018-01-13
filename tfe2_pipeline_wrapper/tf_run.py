from te2_sdk import te2
from tfe2_pipeline_wrapper import ApplicationInformation as ai
import click
import json
import hcl
import requests

def load_app_variables(TE2Vars, repository, branch, environment, component_name, azure_client_secret):
    TE2Vars.delete_all_variables()
    url = "https://raw.githubusercontent.com/" + repository + "/" + branch + "/env/" + environment +".tfvars"

    print("Getting Environment Variables from: " + url)
    variable_list = hcl.loads(requests.get(url).text)

    TE2Vars.create_or_update_workspace_variable(
        key="component_name",
        value=component_name,
        hcl=True
    )

    ## TO BE REPLACED WITH VAULT CREDENTIAL IN PRIVATE. JUST USING AZURE FOR TEMPORARY
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

@click.command()
@click.option('--request_type', required=True)
@click.option('--app_id', required=True)
@click.option('--component_name', required=True)
@click.option('--environment', required=True)
@click.option('--atlas_token', required=True)
@click.option('--azure_client_secret', required=True)
@click.option('--destroy', required=True)
@click.option('--run_id', required=True)
def main(request_type, app_id, component_name, environment, run_id, atlas_token, azure_client_secret, destroy=False):

    info = ai.ApplicationInformation(
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
        component_name=component_name,
        azure_client_secret=azure_client_secret
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
    main()