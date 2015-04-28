import pytest
import datainput.views as v

@pytest.mark.django_db
def test_input(rf):
    resp = v.input(rf.get('/'))
