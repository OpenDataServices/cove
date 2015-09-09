from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, Process
from django.http import Http404
from taglifter import TagLifter
import os


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
        ontology=".ve/src/taglifter/ontology/resource-projects-ontology.rdf",
        source=dataset.supplied_data.original_file.file.name,
        base="http://resourceprojects.org/",
        source_meta={"author": "TODO", "Source_Type": "official", "Converted": "Today"}
    )

    tl.build_graph()
    tl.graph.serialize(
        format='turtle',
        destination=os.path.join(dataset.supplied_data.upload_dir(), 'output.ttl')
    )
    pass


def staging(dataset):
    pass


def live(dataset):
    pass


def run_process(request, pk, process_type):
    processes = {
        'fetch': fetch,
        'convert': convert,
        'staging': staging,
        'live': live
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
