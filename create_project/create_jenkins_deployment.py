import create_project.create_application_archetype as app
import json
import os

# Load Application into Consul
with open('data.json', 'r') as f:
    data = json.load(f)
    jenkins_calls = app.ApplicationArchetype(
        app_id=data['app_id'],
        app_name=data['app_name'],
        consul_address=os.environ['CONSUL_ADDRESS']
    )

    # Create Application Keys
    jenkins_calls.create_consul_application_keys(
        cost_centre=data['cost_centre'],
        bcrm=data['bcrm']
    )

    jenkins_calls.create_jenkins_application_deployment(
        git_repository=data['pipeline_repository'],
        component_pipelines_name=data['pipeline_component'],
        environments=data['pipeline_environments']
    )
