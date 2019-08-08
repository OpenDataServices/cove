import os
import glob
import json
import time
import signal
import subprocess
from urllib.parse import urlparse, urlunparse

import requests

"""
This is a test that uses old/unpublished data files that we don't want to make
public.
It checks that the JSON produced by 360 Cove is the same as previously.

Travis is set up with a password to download the files from a password
protected url, see .travis.yml

"""


#
# Generate 360 output
#

print("Running 360 ...")

server_proc = os.fork()
if not server_proc:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cove_360.settings'
    subprocess.call(['python', 'manage.py', 'runserver', '8008'])
    exit()

time.sleep(5)

for original_file in glob.glob('360/*'):
    output_dir = os.path.join('secret_data_test', '360', original_file.split('/')[-1].split('.')[0])
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, 'validation_errors.json')
    with open(output_filename, 'w+') as output_file:
        response = requests.post('http://localhost:8008/', files={'original_file': open(original_file, 'rb')}, data={'csrfmiddlewaretoken': 'foo'}, headers={'Cookie': 'csrftoken=' + 'foo'})

        parsed = urlparse(response.url)
        new_tuple = parsed.scheme, parsed.netloc, '/media/' + parsed.path.split('/')[-1] + '/validation_errors-3.json', '', '', ''
        new_url = urlunparse(new_tuple)
        output_file.write(requests.get(new_url).text)

os.kill(server_proc, signal.SIGTERM)


#
# Test 360 results
#

print("Testing 360 ...")

os.chdir(os.path.join('secret_data_test', '360'))

for dirname in os.listdir('.'):
    print(dirname)
    expected_path = os.path.join('..', '..', 'secret_data_test_archive', '360', dirname, 'validation_errors.json')
    actual_path = os.path.join(dirname, 'validation_errors.json')
    with open(actual_path) as fp, open(expected_path) as fp_archive:
        actual_data = json.load(fp)
        expected_data = json.load(fp_archive)
        assert actual_data == expected_data
