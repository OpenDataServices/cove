import pytest
import cove.input.views as v


@pytest.mark.django_db
def test_input(rf):
    resp = v.input(rf.get('/'))
    assert resp.status_code == 200
