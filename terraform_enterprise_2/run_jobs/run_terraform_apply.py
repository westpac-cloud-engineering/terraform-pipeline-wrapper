import terraform_class as tf
import argparse

p = argparse.ArgumentParser()
p.add_argument('organisation')
p.add_argument('app_id')
p.add_argument('workspace_name')
p.add_argument('run_id')
p.add_argument('destroy')
p.add_argument('atlas_token')

def main(organisation, app_id, workspace_name, run_id, atlas_token, destroy=False):
    api = tf.TerraformAPICalls(organization=organisation,  app_id=app_id, atlas_token=atlas_token)
    workspace_id = api.get_workspace_id(workspace_name)
    return api.apply_run(workspace_id, run_id=run_id, destroy=destroy)

if __name__ == "__main__":
    args = p.parse_args()
    main(args.organisation, args.app_id, args.workspace_name, args.run_id, args.atlas_token, args.destroy)
