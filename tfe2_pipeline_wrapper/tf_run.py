import json
import click

import tfe2_pipeline_wrapper.lib.TerraformPipelineFunctions as tpf


@click.command()
@click.option('--configuration_file', required=True)
def main(configuration_file):

    with open(configuration_file) as config:
        data = json.load(config)
        TFE2Actions = tpf.TFE2Actions(
            configuration_map=data
        )

    '''
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