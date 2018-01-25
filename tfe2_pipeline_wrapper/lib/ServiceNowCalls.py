import requests
import json
import datetime


def raise_servicenow_change(configuration_data, plan_log):

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Change Details
    description = "Terraform Deployment - App:  " + configuration_data['deployment']['id'] + \
        " | Component: " + configuration_data['deployment']['component_name'] + \
        " | Environment: " + configuration_data['deployment']['environment']
    justification = "This is an automated change raised by Terraform. It has been pre-approved by the Service " \
                    "Engineering team"
    implementation_plan = plan_log
    risk_and_impact_plan = "Low as Non-Production Environment. Not Customer Facing. Plan Succeeded"
    backout_plan = "Re-run this workflow with an earlier working version of the application."
    test_plan = "Tests are automated as part of the declarative run model."

    scheduled_start = (datetime.datetime.today() + datetime.timedelta(minutes=2)).strftime("YYYYMMDD HH:mm:ss (%Y-%m-%d %H:%M:%S)")
    scheduled_finish = (datetime.datetime.today() + datetime.timedelta(minutes=22)).strftime("YYYYMMDD HH:mm:ss (%Y-%m-%d %H:%M:%S)")

    data = {
        'title': "Terraform Automated Change",
        'short_description': description,
        'type': 'Unplanned',
        'category': 'Software',
        'description': description,
        "justification": justification,
        "implementation_plan": implementation_plan,
        "risk_impact_analysis": risk_and_impact_plan,
        "test_plan": test_plan,
        "backout_plan": backout_plan,
        "start_date": scheduled_start,
        "end_date": scheduled_finish
    }

    # Do the HTTP request
    response = requests.post(
        url=configuration_data['service_now']['url'],
        auth=(configuration_data['service_now']['username'], configuration_data['service_now']['password']),
        headers=headers,
        data=json.dumps(data)
    )

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
        exit()

    print(response.json())