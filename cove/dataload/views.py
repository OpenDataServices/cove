from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, Process
from django.http import Http404
from taglifter import TagLifter
from functools import partial
import os
##requests doesn't work with large files, see below
#import requests
#from requests.auth import HTTPDigestAuth
import subprocess
import urllib.parse


def dataload(request):
    return render(request, "dataload.html", {
        'datasets': Dataset.objects.all()
    })


def data(request, pk):
    supplied_data = SuppliedData.objects.get(pk=pk)
    try:
        dataset = supplied_data.dataset
    except Dataset.DoesNotExist:
        dataset = Dataset.objects.create(supplied_data=supplied_data)
    return redirect(reverse('cove:dataload_dataset', args=(dataset.pk,), current_app=request.current_app))


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


def run_process(request, pk, process_type):
    processes = {
        'fetch': fetch,
        'convert': convert,
        'staging': partial(put_to_virtuoso, staging=True),
        'live': partial(put_to_virtuoso, staging=False),
    }
    if process_type in processes:
        dataset = Dataset.objects.get(pk=pk)
        processes[process_type](dataset)
        Process.objects.create(
            type=process_type,
            dataset=dataset
        )
        return redirect(reverse('cove:dataload_dataset', args=(pk,), current_app=request.current_app))
    else:
        raise Http404()


def dataset(request, pk):
    return render(request, "dataset.html", {
        'dataset': Dataset.objects.get(pk=pk),
    })
