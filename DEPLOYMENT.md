
## How to create a deployment pull requset


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
{{Explanation of what has changed.}}

Standing tasks:
- [ ] Re-run translations if any text has changed
- [ ] Create a new branch `release-{{YYYYMM}}` if it doesn't exist.
- [ ] Deploy to a subdomain on the dev server http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/ - redo this for any additional commits
- [ ] Check that the correct commit has been deployed using the link in the footer http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/
- [ ] Run `CUSTOM_SERVER_URL=http://release-{{YYYYMM}}.dev.cove.opendataservices.coop/ py.test fts` - redo this for each redeploy to the subomdain

After merge:
- [ ] Run salt highstate on `cove-live`
- [ ] Check that the correct commit has been deployed using the link in the footer http://cove.opendataservices.coop/
- [ ] Run `CUSTOM_SERVER_URL=http://cove.opendataservices.coop/ py.test fts` on a local copy of the updated live branch
- [ ] Run salt highstate on `cove-live-ocds`
- [ ] Check that the correct commit has been deployed using the link in the footer http://release-201602.dev.cove.opendataservices.coop/
- [ ] Run `CUSTOM_SERVER_URL=http://standard.open-contracting.org PREFIX_OCDS=/validator/ py.test fts ` on a local copy of the updated live branch
```

Where `{{YYYYMM}}` should be replace with the actual year and month numbers - e.g. 201602

Add any extra tasks as appropriate. If they should be recurring update this template.
