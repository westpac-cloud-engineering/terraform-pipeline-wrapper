import os
import sys
import jinja2

class JenkinsTemplate:
    def __init__(self, template_path):
        self.template_path = os.path.join(template_path, "jenkins")
        self.valid = self.validate_jenkins_structure()

    def validate_jenkins_structure(self):
        if os.path.isfile(os.path.join(self.template_path, "Jenkinsfile")):
            return True
        return False


class TerraformTemplate:
    def __init__(self, template_path):
        self.template_path = os.path.join(template_path, "terraform")
        self.valid = self.validate_terraform_structure()

    def validate_terraform_structure(self):
        # Check that the three valid files, environment.tfvars, main.tf and variables.tf exists
        if not os.path.isfile(os.path.join(self.template_path, "environment.tfvars")):
            return False
        if not os.path.isfile(os.path.join(self.template_path, "main.tf")):
            return False
        if not os.path.isfile(os.path.join(self.template_path, "variables.tf")):
            return False
        return True

    def generate_terraform_configuration(self, destination_path):
        return False


class RepositoryTemplate:
    def __init__(self, templates_path, template_name):
        self.template_name = template_name
        self.template_path = os.path.join(templates_path, template_name)

        if self.validate_configuration_template():
            self.valid = True
        else:
            self.valid = False

        self.jenkins_template = JenkinsTemplate(self.template_path)
        self.terraform_template = TerraformTemplate(self.template_path)

    def validate_configuration_template(self):
        # TODO: More Robust Validation of Configuration Template
        if os.path.isfile(os.path.join(self.template_path, "definition.json")):
            return True
        else:
            return False

    def generate_repository_from_template(self):
        return False

    def _generate_readme_contents(self):
        return False  # TODO: Generate README Contents

    def _generate_git_repository_and_upload(self):
        return False

    def generate_repository(self, target_directory):
        # Create Base folder
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        self._generate_readme_contents()

        # Generate Terraform Template
        if self.terraform_template.valid:
            self.terraform_template.generate_terraform_configuration(target_directory)

        # Generate Jenkins Template
        if self.terraform_template.valid:
            self.terraform_template.generate_terraform_configuration(target_directory)

        # Turn into a git repository and upload
        self._generate_git_repository_and_upload()

class GetAvailableRepositoryTemplates:
    def __init__(self):
        print("The available repository templates include:")

        templates_dir = os.path.join(sys.path[0], 'templates')
        for template_name in os.listdir(os.path.join(sys.path[0], 'templates')):
            template = RepositoryTemplate(templates_dir, template_name)

            if template.valid:
                print("- ", template.template_name)

        # self.generate_template_print('TEMPLATE_NAME_HERE')

    @staticmethod
    def generate_template_print(template):
        print("\nTo generate a template from this configuration, please run:")
        print("GenerateTemplate --template \"", template, "\" `")
        print("                 --directory \"DIRECTORY_TO_CREATE_REPOSITORY\" `")
        print("                 --app_name \"APPLICATION_NAME\" `")
        print("                 --component_name \"COMPONENT_NAME\" `")
        print("                 --environments Dev1 Test1 Test2 Etc")


class BoilerplateRepositoryGenerator():
    def __init__(self, template, directory, application_name, component_name, environments):
        self.directory = directory
        self.application_name = application_name

    def generate


GetAvailableRepositoryTemplates()
#BoilerplateRepositoryGenerator("default", "My_Application", "my_application", "component_name", ['dev', 'test'])