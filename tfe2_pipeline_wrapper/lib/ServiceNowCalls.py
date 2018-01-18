import requests
import json


def raise_servicenow_change(url, username, password):

    # Set proper headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {
        'short_description': 'Test Change',
        'category': 'Software',
        'description': "TBA.",
        'configuration_item': 'TBA'
    }

    # Do the HTTP request
    response = requests.post(url, auth=(username, password), headers=headers, data=json.dumps(data))

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
        exit()

    print(response.json())
