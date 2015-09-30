from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, ProcessRun
from django.http import Http404
from cove_resourceprojects import PROCESSES


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
