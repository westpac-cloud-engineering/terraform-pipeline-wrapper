import os
import tempfile
import tarfile

temp_directory = "C:\\Users\\roryc\\Desktop\\test files"

configuration_files_tar = tempfile.TemporaryFile()
with tarfile.open('C:\\Users\\roryc\\Desktop\\test.tar.gz', mode='w:gz') as tar:
    tar.add(os.path.join(temp_directory), arcname='')
