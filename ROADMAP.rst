Roadmap
=======

August - December 2016
----------------------

See also the flatten-tool roadmap https://github.com/OpenDataServices/flatten-tool/blob/master/ROADMAP.rst 

- Spend some time on improving analytics 
    - In particular it would be useful to know how many validations end with error. 
- Use IODC as an opportunity to do some user testing 
- Spend some time on Cove deployment 
    - Configure our dev/staging/live servers more similarly, particularly wrt. OCDS/360 split, to avoid issues only being noticed when doing the live deploy. 
    - Redeploy some of our Cove instances so that they can be billed directly to clients. 
    - Review the specs of the servers used for cove 
- Dedicate some time to misc bug fixes 
- Validation of extensions is important for OCDS 1.1 live 
- Ensure we support new style OCDS codelists 
- Improve display of flatten-tool conversion errors 
- A Large files policy - we need to decide how we handle them, and tell people how we handle them - need to say we have a time out now.  

We’d like to (but are unlikely to have time for in the next 5 months):

- Start on the process of separating the code for the 360Giving and OCDS versions of the tool 
- A 360 specific deploy on 360Giving domain 
- Sentry user feedback from errors 
- Provide a merge releases feature for OCDS data 
- Spend some time talking with OCDS/360Giving data analysts to better understand their needs 
    - When to use CoVE and when to use other analysis tools, and how these fit together: ipython notebooks, sql output 
    - Programmatic access 
- Finish work on programmatic access to Cove, this may include: 
    - "API" on conversion / validation / warnings / aggregate data 
    - Button to download a CSV/JSON of validation results/warnings/aggregate data 
    - Be available for offline use - i.e offering CoVE as a python library 
- Completeness - a tree with percentages like some of the OCDS evaluation reports 
    - Also useful to flag whether it’s a required field 
    - Some questions around how this works with work with one of many files 
    - For 360 flag maybe what appears in the main sheet of the default spreadsheet template 
- More OCDS summary statistics 
- Extra warnings for fields that do not follow documentation guidelines. 
- Improve the information we provide about OCDS record packages 

We won’t:

- Do OCDS completeness based on the current basic/intermediate/advanced framework in the docs as that needs improvement first 

Nice to haves:

- Show some graphs and maps 
- Use Whoosh - python text search? - This should be a big help with exploring your data 
- Work with IATI data. 
- Custom quick and easy deployment. 

April - July 2016, what we did
------------------------------

PRs for deploying new features to live:

- June https://github.com/OpenDataServices/cove/pull/436
- July https://github.com/OpenDataServices/cove/pull/466

We did (from the roadmap):

- A specific sprint  in May around the 360Giving version of CoVE 
    - Improved the words in the application and changed the layout - explain to users more about what's going on 
    - Use new source map in flatten-tool to provide validation information about the original spreadsheet users 
- In a later month, applied some of the changes from that sprint to the OCDS version also. 
- Some more work on errors 
- Start some work on programmatic access to Cove as a Python library 
- Testing loading lots of data from various published sources to check for regressions/changes, although not properly merged yet… 
- Some work around Logging/reporting more information about how the application is being used 
- Make it more clear about others can contribute to this project 
- Cove can now be deployed with dev schema 
- Cove now checks content-type and content-disposition to determine filetype 
- Lots of work on flatten-tool, and now have a roadmap for that: https://github.com/OpenDataServices/flatten-tool/blob/master/ROADMAP.rst

Additionally we did:

- Warnings from flatten-tool are now displayed in Cove 
- Better format checking (uris) 

Stalled:

- A Large files policy - we need to decide how we handle them, and tell people how we handle them - need to say we have a time out now. 

We deliberately didn’t:

- Validate other formats directly (e.g csvs as csvs, excel as excel), taking a source map approach instead 

We said we would, but didn’t get to:

- Start on the process of separating the 360Giving and OCDS versions of the tool 
- Comprehensiveness 
    - Fields not being used/'coverage' for 360Giving based on spreadsheet on the website. 
    - Completeness of OCDS 
- Finish work on programmatic access to Cove, this may include: 
    - "API" on conversion / validation / warnings / aggregate data 
    - Button to download a CSV/JSON of validation results/warnings/aggregate data 
    - Be available for offline use - i.e offering CoVE as a python library 
- When to use CoVE and when to use other analysis tools, and how these fit together: ipython notebooks, sql output

April - July 2016
-----------------
We are planing a specific sprint in May around the 360Giving version of CoVE

We will continue with:

* Our current piece work on flatten-tool - and have a roadmap for the future
* A Large files policy - we need to decide how we handle them, and tell people how we handle them - need to say we have a time out now.
* Improving the words in the application - explain to users more about what's going on

We will:

* Start on the process of separating the 360Giving and OCDS versions of the tool
* Deal differently with JSON users and spreadsheet users (likely to be part of a 360 specific sprint)
* Validate other formats directly (e.g csvs as csvs, excel as excel)
* Comprehensiveness
* Fields not being used/'coverage' for 360 Giving based on spreadsheet on the website.
* Completeness of OCDS
* More work on errors
* Start some work on programmatic access to Cove, this may include:
* "API" on conversion / validation / warnings / aggregate data
* Button to download a CSV/JSON of validation results/warnings/aggregate data
* Be available for offline use - i.e offering CoVE as a python library
* When to use and when not - ipython notebooks, sql output
* Testing loading lots of data from various published sources to check for regressions/changes.
* Logging/reporting more information about how the application is being used
* Make it clear about others can contribute to this project

We want to do, but maybe not in the next 3 months:

* More OCDS summary statistics
* Provides a merge releases feature for OCDS data
* A 360 specific deploy on 360Giving domain
* Extra warnings for fields that do not follow documentation guidelines.

Nice to haves:

* Show some graphs and maps
* Use Whoosh - python text search? - This should be a big help with exploring your data
* Work with IATI data.
* Custom quick and easy deployment.

We have discussed but will not be doing the following in the foreseeable future:

* Comparison - see the difference between files
* Multiple files - upload many files at once and deal with them either collectively or individually
* Do we want a queue?
* We don't think it should become a datastore...
* Widget to let people embed links to converted data in their own websites (e.g. user publishers as CSV, but tags the link so that JSON and Excel links also provided);


Jan - March 2016
----------------

We did:

* Be live for OCDS validator (end of Jan 2016)
* Have improved error messages
* Some work towards a lovely 360page... ...and a lovely OCDS page
* Have Transifex integration for translations
* Have a key facts panel for 360giving - schema used, date you did it etc
* (Maybe) How does it do a single function...Validate only - split validate/flatten (as a config option?) - we have a button to flatten now, by default we don’t

NB - We also did loads of other stuff that was not reflected in the original roadmap (in particular lots of flatten-tool work)

We’re part way towards:

* Have a roadmap for Flatten Tool - a core component
* Have a Large files policy - we need to decide how we handle them, and tell people how we handle them - need to say we have a time out now.

We didn’t:

* Start on the process of separating the 360Giving and OCDS versions of the tool
* Deal differently with JSON users and spreadsheet users
* Validate other formats directly (e.g csvs as csvs, excel as excel)
* Show - Fields not being used/'coverage' for 360 Giving based on spreadsheet on the website.
* Use Whoosh - python text search? - This should be a big help with exploring your data
* Show some graphs and maps
* Be available for offline use - i.e offering CoVE as a python library
* Maybe (not done):
* Work with IATI data.
* Custom quick and easy deployment.
* A 360 specific deploy on 360Giving domain
* Things we discussed and decided not to do, so didn’t do:
* Comparison - see the difference between files
* Multiple files - upload many files at once and deal with them either collectively or individually
* Provides a merge releases feature for OCDS data
* Do we want a queue?
* "API" on validation / warnings / aggregate data
* Button to download a CSV/JSON of results
* When to use and when not - ipython notebooks, sql output, (part of this is moving cove into a library)
* We don't think it should become a datastore...
* Widget to let people embed links to converted data in their own websites (e.g. user publishers as CSV, but tags the link so that JSON and Excel links also provided);
