import requests
import jinja2 as j2

class JenkinsCalls:

    def __init__(self, base_url, username, password):
        self.base_url = "https://" + username + ":" + password + "@" + \
              base_url

    def get_crumb(self):
        url = self.base_url + '/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'

        return dict(s.split(':') for s in [requests.get(url=url).text])

    def create_jenkins_pipeline_job(self, app_id, component_pipelines_name, environment, sub_key=""):

        # Generate request variables
        pipeline_full_name = app_id + "/" + component_pipelines_name + "/" + environment
        url = self.base_url + sub_key + "/createItem?name=" + component_pipelines_name + "-" + environment

        print("Creating Job: " + pipeline_full_name)

        # Generate Template
        template = j2.Environment(loader=j2.PackageLoader('create_project', 'jenkins_jobs')).get_template('terraform_default.xml')
        pipeline_info = {
            "displayName": "Deployment: " + environment,
            "app_id": app_id
        }

        # Create Jobs
        headers = {"Content-Type": "application/xml", **self.get_crumb()}
        request = requests.post(url=url, headers=headers, data=template.render(pipeline_info=pipeline_info))

        return pipeline_full_name

    # Create Folder in Jenkins
    def create_jenkins_folder(self, name, display_name, sub_key=""):
        print("Creating Folder: " + display_name)

        # Generate Template
        headers = {"Content-Type": "application/xml", **self.get_crumb()}
        template = j2.Environment(loader=j2.PackageLoader('create_project', 'jenkins_jobs')).get_template('jenkins_folder.xml')
        folder_info = {
            "displayName": display_name,
        }

        url = self.base_url + sub_key + "/createItem?name=" + name

        return requests.post(url=url, headers=headers, data=template.render(folder_info=folder_info)).status_code
