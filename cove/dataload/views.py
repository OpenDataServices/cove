from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, ProcessRun
from django.http import Http404
from cove_resourceprojects import PROCESSES
from collections import OrderedDict


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
            # Get the last run for this process
            last_run = dataset.processrun_set.filter(process=process_id).order_by('-datetime').first()
            depends_last_run = None

            # And for the process it depends on
            if process['depends']:
                depends_last_run = dataset.processrun_set.filter(process=process['depends']).order_by('-datetime').first()
            # If the reverse of the process has been run more recently, undo it
            if last_run and 'reverse_id' in process:
                reverse_last_run = dataset.processrun_set.filter(process=process['reverse_id'], successful=True).order_by('-datetime').first()
                if reverse_last_run and last_run.datetime < reverse_last_run.datetime:
                    last_run = None

            label_class = ''
            if last_run:
                if depends_last_run and last_run.datetime < depends_last_run.datetime:
                    label_class = 'label-warning'
                elif last_run.successful:
                    label_class = 'label-success'
                else:
                    # Note this currently will never happen for the NRGI code
                    label_class = 'label-danger'
            yield {
                'process': process,
                'label_class': label_class,
                'last_run': last_run,
                'more_info_link': process['more_info_link'](dataset) if 'more_info_link' in process else '',
            }


def dataload(request):
    return render(request, "dataload.html", {
        'datasets_statuses': ((dataset, statuses(dataset)) for dataset in Dataset.objects.filter(deleted=False)),
        'main_process_names': [process['name'] for process in PROCESSES.values() if process['main']]
    })


def data(request, pk):
    supplied_data = SuppliedData.objects.get(pk=pk)
    try:
        dataset = supplied_data.dataset
    except Dataset.DoesNotExist:
        if 'name' in request.POST:
            dataset = Dataset.objects.create(
                supplied_data=supplied_data,
                name=request.POST['name']
            )
        else:
            return render(request, 'dataset_name.html')
    # Input module has already fetched the data for us, so fake a fetch
    return run_process(request, dataset.id, 'fetch', fake=True)


def dataset(request, pk):
    dataset = Dataset.objects.get(pk=pk)
    if dataset.deleted:
        return redirect(reverse('cove:dataload', current_app=request.current_app))
    return render(request, "dataset.html", {
        'dataset': dataset,
        'statuses': statuses(dataset)
    })


def run_process(request, pk, process_id, fake=False):
    if process_id in PROCESSES:
        dataset = Dataset.objects.get(pk=pk)
        if not fake:
            PROCESSES[process_id]['function'](dataset)
        ProcessRun.objects.create(
            process=process_id,
            dataset=dataset
        )
        return redirect(reverse('cove:dataload_dataset', args=(pk,), current_app=request.current_app))
    else:
        raise Http404()
