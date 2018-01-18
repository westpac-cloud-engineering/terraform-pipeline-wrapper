import json
import click

import tfe2_pipeline_wrapper.lib.TerraformPipelineFunctions as tpf


@click.command()
@click.option('--request_type', required=True)
@click.option('--configuration_file', required=True)
def main(request_type, configuration_file):

    with open(configuration_file) as config:
        data = json.load(config)
        TFE2Actions = tpf.TFE2Actions(
            configuration_map=data
        )

    TFE2Actions.generate_run(request_type)


if __name__ == "__main__":
    main()

