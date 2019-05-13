#!/bin/bash
wget http://travis:$TRAVIS_SECRET_FILES_PASSWORD@travis-secret-files.live3.default.opendataservices.uk0.bigv.io/ocdstestdata.zip
unzip ocdstestdata.zip
wget http://travis:$TRAVIS_SECRET_FILES_PASSWORD@travis-secret-files.live3.default.opendataservices.uk0.bigv.io/360testdata.zip
unzip 360testdata.zip
wget http://travis:$TRAVIS_SECRET_FILES_PASSWORD@travis-secret-files.live3.default.opendataservices.uk0.bigv.io/secret_data_test_archive_10.zip
unzip secret_data_test_archive_10.zip
