import tfe2_pipeline_wrapper.lib.ServiceNowCalls as SNOW
import click
import json


@click.command()
@click.option('--action_type', required=True)
@click.option('--configuration_file', required=True)
@click.option('--log_file', required=True)
@click.option('--sys_id', required=False)
def main(action_type, configuration_file, log_file, sys_id=None):
    # Open Files
    with open(configuration_file) as config_file:
        config = json.load(config_file)
    with open(log_file, "r", encoding="utf-8") as log_file:
        log = log_file.read()

    # Open or Close a change
    results = {}
    if action_type == "plan":
        results = SNOW.raise_servicenow_change(configuration_data=config, plan_log=log)
    elif action_type == "apply":
        results = SNOW.close_servicenow_change(configuration_data=config, sys_id=sys_id, apply_results=log)
    else:
        print("Invalid Action Type")

    # Write run results to file
    with open('change_results.json', "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(results))



if __name__ == "__main__":
    main()
