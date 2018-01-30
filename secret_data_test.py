import os
import json
import glob
import subprocess

os.makedirs('secret_data_test', exist_ok=True)
os.chdir('secret_data_test')

for fname in glob.glob('../ocds/*'):
    subprocess.call(['../ocds-cli', fname])

for dirname in os.listdir('.'):
    print(dirname)
    with open(os.path.join(dirname, 'results.json')) as fp, open(os.path.join('..', 'secret_data_test_archive', dirname, 'results.json')) as fp_archive:
        assert json.load(fp) == json.load(fp_archive)
