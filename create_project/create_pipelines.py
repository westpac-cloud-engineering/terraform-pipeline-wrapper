import create_project.application_requests as app
import json
import os

# Load Application into Consul
with open('data.json', 'r') as f:
    data = json.load(f)
    app = app.ApplicationArchetype(
        app_id=data['app_id'],
        app_name=data['app_name'],
        consul_address=os.environ['CONSUL_ADDRESS']
    )

    # Create Application Keys
    app.create_consul_application_keys(
        cost_centre=data['cost_centre'],
        bcrm=data['bcrm']
    )

    app.create_application_pipelines(
        components=data['components']
    )
