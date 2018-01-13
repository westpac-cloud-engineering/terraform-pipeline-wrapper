import jinja2
import time

class TerraformProviderGenerator:
    def __init__(self, provider_list):
        self.provider_list = provider_list
        self.generate_documentation()

    def generate_documentation(self):
        job = {
            'generated_date': time.strftime("%x %X", time.gmtime()),
            'workspace_name': "My Workspace Name"
        }

        app = {
            'name': 'My Test Application',
            'component_name': 'Infrastructure',
            'id': 'A00001',
            'environment': 'NProd',
            'data_classification': 'Protected',
            'bcrm_id': 'Originations',
        }

        env = jinja2.Environment(
            loader=jinja2.PackageLoader('tfe2_pipeline_wrapper', 'templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        template = env.get_template('terraform_configuration/deployment_meta.tf.template')

        print(template.render(app=app, job=job, provider_list=self.provider_list))


TF = TerraformProviderGenerator({})
