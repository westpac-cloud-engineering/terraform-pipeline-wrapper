import click

@click.command()
@click.option('--request_type', required=True)
@click.option('--app_id', required=True)
@click.option('--component_name', required=True)
@click.option('--environment', required=True)
@click.option('--atlas_token', required=True)
@click.option('--azure_client_secret', required=True)
@click.option('--destroy', required=True)
@click.option('--run_id', required=True)
def main(request_type, app_id, component_name, environment, run_id, atlas_token, azure_client_secret, destroy=False):
    print("Success!")

if __name__ == "__main__":
    main()