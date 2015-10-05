import re
import requests
import json
import os
from django.core.files.base import ContentFile


def get_google_doc(supplied_data):
    dir_path = os.path.join(supplied_data.upload_dir(), 'googledoc')
    os.makedirs(dir_path, exist_ok=True)
    result = re.search("([-\w]{25,})", supplied_data.source_url)
    key = result.group(0)

    api_url = 'https://spreadsheets.google.com/feeds/worksheets/' + key + '/public/full?alt=json'
    sheetlist = requests.get(api_url)
    supplied_data.original_file.save(
        key,
        ContentFile(sheetlist.text))
    sheetjson = json.loads(sheetlist.text)

    for entry in sheetjson['feed']['entry']:
        for link in entry['link']:
            if link['type'] == "text/csv":
                r = requests.get(link['href'])
                with open(os.path.join(dir_path, entry['title']['$t']), 'wb') as fp:
                    fp.write(r.content)
