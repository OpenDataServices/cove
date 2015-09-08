from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from cove.input.models import SuppliedData
from cove.dataload.models import Dataset, Process


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


def run_process(request, pk, process_name):
    Process.objects.create(
        type=process_name,
        dataset=Dataset.objects.get(pk=pk)
    )
    return redirect(reverse('cove:dataload_dataset', args=(pk,), current_app=request.current_app))


def dataset(request, pk):
    return render(request, "dataset.html", {
        'dataset': Dataset.objects.get(pk=pk),
    })
