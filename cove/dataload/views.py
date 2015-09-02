from django.shortcuts import render

MOCK_DATASETS = [
    {
        'name': 'Dataset 1',
        'fetched': {'success': True, 'when': 6},
        'converted': {'success': True, 'when': 5},
        'on_staging': {'success': True, 'when': 4},
        'on_live': {'success': True, 'when': 3},
    },
    {
        'name': 'Dataset 2',
        'fetched': {'success': False, 'when': 10},
    },
    {
        'name': 'Dataset 3',
        'fetched': {'success': True, 'when': 8},
        'converted': {'success': False, 'when': 7},
    },
    {
        'name': 'Dataset 4',
        'fetched': {'success': True, 'when': 1},
        'converted': {'success': True, 'when': 20},
        'on_staging': {'success': True, 'when': 19},
        'on_live': {'success': True, 'when': 18},
    },
    {
        'name': 'Dataset 5',
        'fetched': {'success': True, 'when': 6},
        'converted': {'success': False, 'when': 5},
    },
    {
        'name': 'Dataset 6',
        'fetched': {'success': True, 'when': 1},
        'converted': {'success': False, 'when': 2},
    },
    {
        'name': 'Dataset 7',
        'fetched': {'success': True, 'when': 3},
        'converted': {'success': True, 'when': 2},
        'on_staging': {'success': True, 'when': 19},
        'on_live': {'success': True, 'when': 18},
    },
    {
        'name': 'Dataset 8',
        'fetched': {'success': True, 'when': 3},
        'converted': {'success': True, 'when': 2},
        'on_staging': {'success': True, 'when': 1},
        'on_live': {'success': True, 'when': 18},
    },
]


def dataload(request):
    return render(request, "dataload.html", {'mode': int(request.GET.get('mode', 0)), 'datasets': MOCK_DATASETS})
