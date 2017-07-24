# CoVE

## Run interactive (start web server)

   docker run -ti -p 8000:8000 openagdata/cove

## Run non-interactive

This docker image builds off the base python 3 image and runs CoVE in the native python.  It takes a file in on the standard in and returns a parsed document on the standard out and validation errors on the standard error.

    cat sample-data/activity-standard-example-annotated.xml | docker run -i -e PROCESS_DATA=true openagdata/cove

Dockerhub [here](https://hub.docker.com/r/openagdata/cove/).

## Building the docker

    docker build --build-arg SECRET_KEY=asdfghjkl --no-cache --rm .
    docker push openagdata/cove
