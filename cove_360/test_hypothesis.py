from cove_360.lib.threesixtygiving import get_grants_aggregates
from hypothesis import HealthCheck, given, assume, settings, strategies as st
import pytest


"""
## Suggested testing patterns (from CamPUG talk)
* simple fuzzing
* round trip
* invariants and idempotents
* test oracle
"""

general_json = st.recursive(st.floats() | st.integers() | st.booleans() | st.text() | st.none(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children))


@pytest.mark.xfail
@given(general_json)
def test_get_grants_aggregates(json_data):
    get_grants_aggregates(json_data)


@given(general_json)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_get_grants_aggregates_dict(json_data):
    assume(type(json_data) is dict)
    get_grants_aggregates(json_data)
