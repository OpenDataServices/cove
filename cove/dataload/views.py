from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, ProcessRun
from django.http import Http404
from taglifter import TagLifter
from functools import partial
import os
##requests doesn't work with large files, see below
#import requests
#from requests.auth import HTTPDigestAuth
import subprocess
import urllib.parse
from collections import OrderedDict


def fetch(dataset):
    pass


def convert(dataset):
    tl = TagLifter(
        ontology=".ve/src/resource-projects-etl/ontology/resource-projects-ontology.rdf",
        source=dataset.supplied_data.original_file.file.name,
        base="http://resourceprojects.org/",
        source_meta={"author": "TODO", "Source_Type": "official", "Converted": "Today"}
    )
    tl.build_graph()
    tl.graph.serialize(
        format='turtle',
        destination=os.path.join(dataset.supplied_data.upload_dir(), 'output.ttl')
    )


def put_to_virtuoso(dataset, staging):
    ttl_filename = os.path.join(dataset.supplied_data.upload_dir(), 'output.ttl')
    prefix = 'staging.' if staging else ''
    graphuri = 'http://{}resourceprojects.org/{}'.format(prefix, dataset.supplied_data.pk)

    # Call curl in a subprocess, as requests doesn't work with large files.
    #
    # Security considerations:
    # Beware adding user input to this call. check_call has shell=False by
    # default, which means it's not possible to eascape the shell. However,
    # user input could pass extra arguments / sensitive files to curl, so we
    # should be careful:
    # * ttl_filename is not from user input, so should be safe
    # * graphuri is urlencoded, so should be safe
    subprocess.check_call([
        'curl',
        '-T',
        ttl_filename,
        'http://virtuoso:8890/sparql-graph-crud-auth?' + urllib.parse.urlencode({'graph': graphuri}),
        '--digest',
        '--user',
        'dba:{}'.format(os.environ['DBA_PASS'])
    ])

    # This requests code doesn't work for files larger than about 1MB
    #with open(os.path.join(data_dir, f), 'rb') as fp:
    #    r = requests.put('http://localhost:8890/sparql-graph-crud-auth',
    #    #'http://requestb.in/1mfng7t1',
    #        params = {'graph': graphuri},
    #        auth=HTTPDigestAuth('dba', os.environ['DBA_PASS']),
    #        data=fp
    #    )

    # We're using shell=True here (and running virutoso SQL directly!), so must
    # trust prefix, graphuri and DBA_PASS. The only outside input to this are
    # DBA_PASS the pk used to construct graphuri, which are not user editable.
    # We must ensure this continues to be the case.
    subprocess.check_call('''
        echo "DB.DBA.RDF_GRAPH_GROUP_INS('http://{}resourceprojects.org/data/', '{}');" | isql virtuoso dba {} \
        '''.format(prefix, graphuri, os.environ['DBA_PASS']), shell=True)


def delete_from_virtuoso(dataset, staging):
    prefix = 'staging.' if staging else ''
    graphuri = 'http://{}resourceprojects.org/{}'.format(prefix, dataset.supplied_data.pk)

    # Using curl here because we're already using it for putting.
    # If we want to switch to e.g. requests this part should work fine.
    subprocess.check_call([
        'curl',
        '-X',
        'DELETE',
        'http://virtuoso:8890/sparql-graph-crud-auth?' + urllib.parse.urlencode({'graph': graphuri}),
        '--digest',
        '--user',
        'dba:{}'.format(os.environ['DBA_PASS'])
    ])


PROCESSES = OrderedDict([
    ('fetch', {
        'name': 'Fetched',
        'action_name': 'Fetch',
        'depends': None,
        'function': fetch,
        'main': True,
    }),
    ('convert', {
        'name': 'Converted',
        'action_name': 'Convert',
        'more_info_name': 'Conversion messages',
        'depends': 'fetch',
        'function': convert,
        'main': True
    }),
    ('staging', {
        'name': 'Pushed to staging',
        'action_name': 'Push to staging',
        'more_info_name': 'View on staging',
        'depends': 'convert',
        'function': partial(put_to_virtuoso, staging=True),
        'reverse_id': 'rm_staging',
        'main': True
    }),
    ('live', {
        'name': 'Pushed to live',
        'action_name': 'Push to live',
        'depends': 'fetch',
        'more_info_name': 'View on live',
        'function': partial(put_to_virtuoso, staging=False),
        'reverse_id': 'rm_live',
        'main': True
    }),
    ('rm_staging', {
        'name': 'Removed from staging',
        'action_name': 'Remove from staging',
        'depends': 'staging',
        'function': partial(delete_from_virtuoso, staging=True),
        'main': False
    }),
    ('rm_live', {
        'name': 'Removed from live',
        'action_name': 'Remove from live',
        'depends': 'live',
        'function': partial(delete_from_virtuoso, staging=False),
        'main': False
    }),
])

# Add id and reverse fields to each process
PROCESSES = OrderedDict([
    (process_id, dict(
        id=process_id,
        reverse=PROCESSES[process['reverse_id']] if 'reverse_id' in process else None,
        **process))
    for process_id, process in PROCESSES.items()])


def statuses(dataset):
    for process_id, process in PROCESSES.items():
        if process['main']:
            last_run = dataset.processrun_set.filter(process=process_id).order_by('-datetime').first()
            depends_last_run = dataset.processrun_set.filter(process=process['depends']).order_by('-datetime').first()
            label_class = ''
            if last_run and depends_last_run:
                if last_run.datetime < depends_last_run.datetime:
                    label_class = 'label-warning'
                elif last_run.successful:
                    label_class = 'label-success'
                else:
                    label_class = 'label-danger'
            yield {
                'process': process,
                'label_class': label_class,
                'last_run': last_run,
            }


def dataload(request):
    return render(request, "dataload.html", {
        'datasets_statuses': ((dataset, statuses(dataset)) for dataset in Dataset.objects.all()),
        'main_process_names': [process['name'] for process in PROCESSES.values() if process['main']]
    })


def data(request, pk):
    supplied_data = SuppliedData.objects.get(pk=pk)
    try:
        dataset = supplied_data.dataset
    except Dataset.DoesNotExist:
        dataset = Dataset.objects.create(supplied_data=supplied_data)
    return redirect(reverse('cove:dataload_dataset', args=(dataset.pk,), current_app=request.current_app))


def dataset(request, pk):
    dataset = Dataset.objects.get(pk=pk)
    return render(request, "dataset.html", {
        'dataset': dataset,
        'statuses': statuses(dataset)
    })


def run_process(request, pk, process_id):
    if process_id in PROCESSES:
        dataset = Dataset.objects.get(pk=pk)
        PROCESSES[process_id]['function'](dataset)
        ProcessRun.objects.create(
            process=process_id,
            dataset=dataset
        )
        return redirect(reverse('cove:dataload_dataset', args=(pk,), current_app=request.current_app))
    else:
        raise Http404()
