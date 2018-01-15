import te2_sdk.te2 as te2
from tfe2_pipeline_wrapper import ApplicationInformation as ai
import click

@click.command()
@click.option('--configuration_file', required=True)
def main(configuration_file):

    info = ai.ApplicationInformation(configuration_file)
    info.raise_servicenow_change()
    '''
    tf_info = info.get_terraform_tenant_information()

    tf_client = te2.TE2Client(
        organisation=tf_info['organisation'],
        atlas_token=info.atlas_secret,
        base_url="https://atlas.hashicorp.com/api/v2"
    )

    info.generate_and_upload_configuration(tf_client)

    tf_ws_runs = te2.TE2WorkspaceRuns(
        client=tf_client,
        workspace_name=info.tf_info['workspace']
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