# Deployment Notes

General Django deployment considerations apply to deploying Cove. We deploy using Apache and uwsgi using this  [Salt State file](https://github.com/OpenDataServices/opendataservices-deploy/blob/master/salt/cove.sls).

## How to do a live deploy of CoVE

### 360Giving

1. Do the actual deploy. From the [opendataservices-deploy directory](https://github.com/OpenDataServices/opendataservices-deploy):

```
salt-ssh --state-output=mixed -L 'cove-360-live' state.highstate
```
2. Check that the latest commit is shown in the footer of <https://dataquality.threesixtygiving.org/>

3. Test that the live site is working as expected. From the cove directory:

```
CUSTOM_SERVER_URL=https://dataquality.threesixtygiving.org/ DJANGO_SETTINGS_MODULE=cove_360.settings py.test cove_360/tests_functional.py -n 4
```

### IATI

1. Do the actual deploy. From the [opendataservices-deploy directory](https://github.com/OpenDataServices/opendataservices-deploy):

```
salt-ssh --state-output=mixed -L 'cove-live-iati' state.highstate
```
2. Check that the latest commit is shown in the footer of <http://iati.cove.opendataservices.coop/>

3. Test that the live site is working as expected. From the cove directory:

```
CUSTOM_SERVER_URL=http://iati.cove.opendataservices.coop/ DJANGO_SETTINGS_MODULE=cove_iati.settings py.test cove_iati/tests_functional.py -n 4
```
