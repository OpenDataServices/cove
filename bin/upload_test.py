import requests
import argparse
from urllib.parse import urlparse, urlunparse
import csv

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload set of files to cove')
    parser.add_argument('cove_url', help='URL endpoint or upload page')
    parser.add_argument('files', help='files to import', nargs='+')
    args = parser.parse_args()

    with open('validation_errors.csv', 'w+') as validation_errors:
        validation_writer = csv.writer(validation_errors)
        validation_writer.writerow(["file", "message", "count", "first_error"])
        for file in args.files:
            print(file)
            response = requests.post(args.cove_url, files={'original_file': open(file, 'rb')}, data={'csrfmiddlewaretoken': 'foo'}, headers={'Cookie': 'csrftoken=' + 'foo'})

            parsed = urlparse(response.url)
            new_tuple = parsed.scheme, parsed.netloc, '/media/' + parsed.path.split('/')[-1] + '/validation_errors-2.json', '', '', ''
            new_url = urlunparse(new_tuple)
            validation_errors = requests.get(new_url).json()
            for key, value in validation_errors.items():
                validation_writer.writerow([file, key, len(value), value[0]])
