import tfe2_pipeline_wrapper.lib
import click


@click.command()
@click.option('--change_template', required=True)
@click.option('--logs_directory', required=True)
def main(configuration_file):
    print("TBA")

if __name__ == "__main__":
    main()