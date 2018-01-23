import json
import click

import tfe2_pipeline_wrapper.lib.TerraformPipelineFunctions as tpf


@click.command()
@click.option('--request_type', required=True)
@click.option('--configuration_file', required=True)
@click.option('--run_id', required=False)
def main(request_type, configuration_file, run_id=None):

    with open(configuration_file) as config:
        data = json.load(config)
        TFE2Actions = tpf.TFE2Actions(
            configuration_map=data
        )

    if request_type == "plan":
        TFE2Actions.generate_and_upload_configuration()
        TFE2Actions.generate_run('plan')
    elif request_type == "apply":
        TFE2Actions.generate_run('apply', run_id)

if __name__ == "__main__":
    main()

