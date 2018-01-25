import tfe2_pipeline_wrapper.lib.ServiceNowCalls as SNOW
import click
import json


@click.command()
@click.option('--configuration_file', required=False)
@click.option('--log_file', required=False)
def main(configuration_file, log_file):
    with open(configuration_file) as config_file:
        config = json.load(config_file)

    with open(log_file, "r", encoding="utf-8") as log_file:
        log = log_file.read()

    SNOW.raise_servicenow_change(config, log)


if __name__ == "__main__":
    main()