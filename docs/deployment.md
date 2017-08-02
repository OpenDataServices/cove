# Deployment Notes

General Django deployment considerations apply to deploying Cove. We deploy using Apache and uwsgi using this  [Salt State file](https://github.com/OpenDataServices/opendataservices-deploy/blob/master/salt/cove.sls).

## How to create a deployment pull request


Post a pull request with a title following the appropriate template.:

For the monthly rollout of new features:
```
End of {{Month}} {{Year}} live deployment 
```

For bug fixes:
``
Post {{Month}} {{Year}} bug fixes ({{Num}}) - {{optionally, brief description of changes}} - live deployment 
``

In both cases, add a description following this template:
```
URL for testing: http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/

Planned deployment date: 

#### Summary of changes for this deployment

#### Tasks in deploy process

Before merge:
- [ ] Re-run translations if any text has changed
- [ ] Create a new branch `release-{{YYYYMM}}` if it doesn't exist.
- [ ] Deploy to a subdomain on `cove-dev` for OCDS http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/
- [ ] Check that the correct commit has been deployed using the link in the footer http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/
- [ ] Run `BROWSER=PhantomJS CUSTOM_SERVER_URL=http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/ DJANGO_SETTINGS_MODULE=cove_ocds.settings py.test cove_ocds/tests_functional.py` - redo this for each redeploy to the subomdain
- [ ] Deploy to a subdomain on the 360 dev server http://release-{{YYYYMM}}.cove-360-dev.default.threesixtygiving.uk0.bigv.io/
- [ ] Check that the correct commit has been deployed using the link in the footer http://release-{{YYYYMM}}.cove-360-dev.default.threesixtygiving.uk0.bigv.io/ 
- [ ] Run `BROWSER=PhantomJS CUSTOM_SERVER_URL=http://release-{{YYYYMM}}.cove-360-dev.default.threesixtygiving.uk0.bigv.io/  DJANGO_SETTINGS_MODULE=cove_360.settings py.test cove_360/tests_functional.py` - redo this for each redeploy to the subomdain

Steps above need redoing for additional commits.

After merge:
- [ ] Run salt highstate on `cove-360-live`
- [ ] Check that the correct commit has been deployed using the link in the footer http://dataquality.threesixtygiving.org/
- [ ] Run `BROWSER=PhantomJS CUSTOM_SERVER_URL=https://dataquality.threesixtygiving.org/ DJANGO_SETTINGS_MODULE=cove_360.settings py.test cove_360/tests_functional.py` on a local copy of the updated live branch
- [ ] Run salt highstate on `cove-live-ocds`
- [ ] Check that the correct commit has been deployed using the link in the footer http://standard.open-contracting.org/validator/
- [ ] Run `BROWSER=PhantomJS CUSTOM_SERVER_URL=http://dev.cove.opendataservices.coop/ DJANGO_SETTINGS_MODULE=cove_ocds.settings py.test cove_ocds/tests_functional.py` on a local copy of the updated live branch
- [ ] Check that changes on live are merged back into master too
```

Where `{{YYYYMM}}` should be replace with the actual year and month numbers - e.g. 201602

Add any extra tasks as appropriate. If they should be recurring update this template.
