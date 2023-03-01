Cove library structure
======================

Cove consists of several software libraries.

The libraries
-------------

[Lib-Cove](https://github.com/OpenDataServices/lib-cove) is the core library of non-web tools that are shared across standards. For example, validation helpers which are useful for more than one standard. The intention is that this should have no dependencies on web software like Django, and can be useful as a commandline interface or software library, without a frontend.

[Lib-Cove-Web](https://github.com/OpenDataServices/lib-cove-web) is a library of common Django elements that are shared across standards, to provide a web frontend for the tool.

A standard may have it's own extension of Lib-Cove - for example [Lib-Cove-BODS](https://github.com/openownership/lib-cove-bods) or [Lib-Cove-OCDS](https://github.com/open-contracting/lib-cove-ocds). 
These contain the specific checks and tools for that standard, and depend on Lib-Cove. Again, the intention is that these should have no dependencies on web software, like Django.

This allows libraries like [Lib-Cove-BODS](https://github.com/openownership/lib-cove-bods) or [Lib-Cove-OCDS](https://github.com/open-contracting/lib-cove-ocds) to be used in other places, including non-web places. For instance, they can be called from the commandline or included as dependencies in other software (eg. [OCDS Kingfisher](https://github.com/open-contracting/kingfisher) uses Lib-Cove-OCDS to check the data it has).

Running a Cove instance in it's own repository
----------------------------------------------

A Cove instance for a particular standard can be run in it's own repository.

Compared to the old way of running instances in this shared repository, the benefits of this are:

* Allows dependencies to be set and upgraded for one standard at a time, instead of all standards being required to take changes at the same time.
* Allows changes to be rolled out to one standard at a time, instead of all standards being required to take changes at the same time.
* It's clear what standard a commit impacts on (a commit in the shared repository may only affect one standard).
* It's clear when there are new versions for a standard (a commit in the shared repository may only affect one standard, so that doesn't mean the other standards need to be re-deployed).
* Allows each standard to set their own repository policies - access, protected branches, etc.
* Easier to use as there is no need to set a special `DJANGO_SETTINGS_MODULE` variable when running commands.

For example, see [Cove for BODS](https://github.com/openownership/cove-bods) or [Cove for OCDS](https://github.com/open-contracting/cove-ocds).


Running a Cove instance in this shared Cove repository
------------------------------------------------------

The IATI standard is still run in this repository, in the package `cove_iati`.

It uses the Lib-Cove-Web and the Lib-Cove libraries mentioned above.

No new COVE's should be created in this repository - they should have their own repository.
