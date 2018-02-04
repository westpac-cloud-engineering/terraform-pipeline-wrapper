import requests
import json
import datetime

HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

def raise_servicenow_change(configuration_data, plan_log):

    # Change Details
    description = "Terraform Deployment - App:  " + configuration_data['deployment']['id'] + \
        " | Component: " + configuration_data['deployment']['component_name'] + \
        " | Environment: " + configuration_data['deployment']['environment']
    justification = "This is an automated change raised by Terraform. It has been pre-approved by the Service " \
                    "Engineering team"

    data = {
        'title': "Terraform Automated Change",
        'short_description': description,
        'type': 'Unplanned',
        'category': 'Software',
        'description': description,
        "justification": justification,
        "implementation_plan": plan_log,
        "risk_impact_analysis": "Low as Non-Production Environment. Not Customer Facing. Plan Succeeded",
        "test_plan": "Tests are automated as part of the declarative run model.",
        "backout_plan": "Re-run this workflow with an earlier working version of the application.",
        "start_date": (datetime.datetime.today() + datetime.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": (datetime.datetime.today() + datetime.timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M:%S"),
        "assignment_group": configuration_data['deployment']['id'],
        "state": -1
    }

    # Do the HTTP request
    response = requests.post(
        url=configuration_data['service_now']['url'],
        auth=(configuration_data['service_now']['username'], configuration_data['service_now']['password']),
        headers=HEADERS,
        data=json.dumps(data)
    )

    if str(response.status_code).startswith("2"):
        print("Change '" + response.json()['result']['number'] + "' successfully raised")
        print("URL = https://wbchpaaspoc.service-now.com/nav_to.do?uri=change_request.do?sys_id=" +
              response.json()['result']['sys_id'] + "&sysparm_view=itsm_process")

        return response.json()
    else:
        raise SyntaxError


def close_servicenow_change(configuration_data, sys_id, apply_results):
    data = {
        "close_code": "successful",
        "close_notes": apply_results,
        "state": 3  # Closed Status
    }

    response = requests.patch(
        url=configuration_data['service_now']['url'] + "/" + sys_id,
        auth=(configuration_data['service_now']['username'], configuration_data['service_now']['password']),
        headers=HEADERS,
        data=json.dumps(data)
    )


    if str(response.status_code).startswith("2"):
        print("Change '" + response.json()['result']['number'] + "' successfully closed")
        print("URL = https://wbchpaaspoc.service-now.com/nav_to.do?uri=change_request.do?sys_id=" +
              response.json()['result']['sys_id'] + "&sysparm_view=itsm_process")

        return response.json()
    else:
        raise SyntaxError