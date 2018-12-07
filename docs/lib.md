Cove library structure
======================

Cove is now split into multiple software libraries.

The libraries
-------------

There are several libraries that are used.

[Lib-Cove-Web](https://github.com/OpenDataServices/lib-cove-web) is a library of common Django elements that are shared across standards.

[Lib-Cove](https://github.com/OpenDataServices/lib-cove) is a library of non-web tools that are shared across standards. The intention is that this should have no dependencies on web software, like Django.

A standard may have it's own Lib Cove - for example [Lib-Cove-BODS](https://github.com/openownership/lib-cove-bods) or [Lib-Cove-OCDS](https://github.com/open-contracting/lib-cove-ocds).
These contain the specific checks and tools for that standard. These depend on Lib-Cove. Again, The intention is that these should have no dependencies on web software, like Django.

This allows libraries like [Lib-Cove-BODS](https://github.com/openownership/lib-cove-bods) or [Lib-Cove-OCDS](https://github.com/open-contracting/lib-cove-ocds) to be used in other places, including non-web places. For instance, they can be called from the command line and [OCDS Kingfisher](https://github.com/open-contracting/kingfisher) uses Lib-Cove-OCDS to check the data it has.

Running a Cove instance in it's own repository
----------------------------------------------

This enables a Cove instance for a standard to be run in it's own repository.

Compared to the old way of running instances in this shared repository, the benefits of this are:

* Allows dependencies to be set and upgraded for one standard at a time, instead of all standards being required to take changes at the same time.
* Allows changes to be rolled out to one standard at a time, instead of all standards being required to take changes at the same time.
* It's clear what standard a commit impacts on (a commit in the shared repository may only effect one standard).
* It's clear when there are new versions for a standard (a commit in the shared repository may only effect one standard, so that doesn't mean the other standards need to be deployed).
* Allows each standard to set their own repository policies - access, protected branches, etc.
* Easier to use as no need to set a special DJANGO_SETTINGS_MODULE variable when running commands.

For example, see [Cove for BODS](https://github.com/openownership/cove-bods).


Running a Cove instance in this shared Cove repository
------------------------------------------------------

Some standards are still run in this shared repository, in packages like "cove_360" or "cove_iati".

These still use the Lib Cove Web and the Lib Cove libraries mentioned above.
