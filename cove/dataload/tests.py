from unittest import mock
import cove.dataload.models as m
import cove.input.models
import pytest
from collections import OrderedDict


orig_import = __import__
PROCESSES = OrderedDict([
    ('nodeps', {
        'name': '',
        'depends': None,
        'main': True,
        'reverse_id': 'nodeps_reverse',
    }),
    ('nodeps_reverse', {
        'name': '',
        'depends': '',
        'main': False,
    })
])
cove_resourceprojects_mock = mock.Mock(PROCESSES=PROCESSES)


def import_mock(name, *args):
    if name == 'cove_resourceprojects':
        return cove_resourceprojects_mock
    return orig_import(name, *args)


with mock.patch('builtins.__import__', side_effect=import_mock):
    import cove.dataload.views as v


@pytest.mark.django_db
class TestStatuses:
    def test_no_process_runs(self):
        list_statuses = list(v.statuses(m.Dataset()))
        assert len(list_statuses) == 1
        assert list_statuses[0]['label_class'] == ''
        assert list_statuses[0]['last_run'] is None

    @pytest.mark.parametrize('successful', [True, False])
    def test_last_run(self, successful):
        supplied_data = cove.input.models.SuppliedData.objects.create()
        dataset = m.Dataset.objects.create(supplied_data=supplied_data)
        # Create some process runs
        m.ProcessRun.objects.create(dataset=dataset, process='nodeps', successful=True)
        m.ProcessRun.objects.create(dataset=dataset, process='nodeps', successful=False)
        # Assign the last one to a variable, and check later that's what we get returned
        last_run = m.ProcessRun.objects.create(dataset=dataset, process='nodeps', successful=successful)
        list_statuses = list(v.statuses(dataset))
        assert len(list_statuses) == 1
        if successful:
            assert list_statuses[0]['label_class'] == 'label-success'
        else:
            assert list_statuses[0]['label_class'] == 'label-danger'
        assert list_statuses[0]['last_run'] == last_run
