from te2_sdk import te2
from tfe2_pipeline_wrapper import ApplicationInformation as ai
import click
import json
import hcl
import requests


@click.command()
@click.option('--configuration_file', required=True)
def main(configuration_file):

    info = ai.ApplicationInformation(configuration_file)
    info.clone_repository_and_compress()

    '''
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

    '''

if __name__ == "__main__":
    main()