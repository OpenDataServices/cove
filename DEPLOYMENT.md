
## How to create a deployment pull requset

Post a pull request with a title following the template:
``
Post {{Month}} {{Year}} bug fixes ({{Num}}) - typo - live deployment 
``

And a description following this template:
```
{{summary of the change}}

Standing tasks:
- [ ] Re-run translations if any text has changed
- [ ] Create a new branch `release-201602` if it doesn't exist.
- [ ] Deploy to a subdomain on the dev server http://release-201602.dev.cove.opendataservices.coop/ - redo this for any additional commits
- [ ] Check that the correct commit has been deployed using the link in the footer
- [ ] Run `CUSTOM_SERVER_URL=http://release-201602.dev.cove.opendataservices.coop/ py.test fts` - redo this for each redeploy to the subomdain

After merge:
- [ ] Run salt highstate on `cove-live`
- [ ] Check that the correct commit has been deployed using the link in the footer
- [ ] Run `CUSTOM_SERVER_URL=http://cove.opendataservices.coop/ py.test fts` on a local copy of the updated live branch
- [ ] Run salt highstate on `cove-live-ocds`
- [ ] Check that the correct commit has been deployed using the link in the footer
- [ ] Run `CUSTOM_SERVER_URL=http://standard.open-contracting.org PREFIX_OCDS=/validator/ py.test fts ` on a local copy of the updated live branch
```

Add any extra tasks as appropriate. If they should be recurring update this template.
