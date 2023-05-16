Containerisation and Orchestration - exercise 02
================================================

[[_TOC_]]

Creating OCI Images
-------------------

This directory contains an example of creating a basic `echoserver` application in an OCI Image using Docker.  All of the snippets below can be incrementally added to a `Dockerfile` and then built with the following from the `./ex02` directory:
```console
docker build --tag ex02-echoserver:0.0.1 --file Dockerfile .
```
This participation is strongly encouraged to gain an understanding of the general pattern for building up OCI Images, that are easy to maintain and are efficient to deploy.

Beginning
---------

The `Dockerfile` should be - where ever possible - self documenting.  To do this, liberal use of comments should be adopted, along with a consistent structure.

The starting point is always addressing the base image.  It is useful to use `ARG`s in conjunction with the `FROM` so that different images can be used without changing the code.
```dockerfile
ARG base_image="python:3.9.5-alpine"
FROM $base_image AS builder
```

Labels
------

Labels help establish the provenance of an image.  Add them after the `ARG`s and `FROM`:
```dockerfile
ARG base_image="python:3.9.5-alpine"
FROM $base_image AS builder

LABEL \
      author="Piers Harding <Piers.Harding@skao.int>" \
      description="This image illustrates build dependencies" \
      license="Apache2.0" \
      int.skao.team="Systems Team" \
      int.skao.repository="https://gitlab.com/ska-telescope/sdi/ska-ser-containerisation-and-orchestration"
```

Environment
-----------

Where possible, group `ENV` vars near the top of the `Dockerfile`:
``` dockerfile
# set path
ENV PYTHONPATH=${PYTHONPATH}:../:/
```

The main event: COPY, RUN
-------------------------

The bulk of the workload of customising an OCI Image is performed using the `COPY` and `RUN` directives.  These should be ordered from least frequent change to most frequent change so that the Docker build process can make use of Image Layer caching in order to speed up the rebuild times as you iterate over development.  It is also good practice to place package names in alphabetical order and separate them line by line to increase readability:

```dockerfile
# Add Alpine basic build dependencies
RUN apk add --no-cache \
    alpine-sdk \
    build-base \
    --virtual build-dependencies \
    linux-headers \
    make

# Copy poetry.lock* in case it doesn't exist in the repo
COPY requirements.txt ./

# Install python runtime dependencies
RUN pip3 install -r /requirements.txt --prefix /app
```

Multi-stage Build
-----------------

Once we have executed all the above steps, we have resolved all of the necessary Python package dependencies for our `echoserver`, but if we just used this as the basis for our final image it would be bloated with the build tools and the downloaded source and workspace requirements of the Python packages themselves.  However, what we can do is start the Image definition again, and then copy forward the built packages from the previous stage without taking the tools, cache, and source code with them - add the following to the `Dockerfile` so far:
```dockerfile

ARG base_image="python:3.9.5-alpine"
FROM $base_image
LABEL \
      author="Piers Harding <Piers.Harding@skao.int>" \
      description="This image illustrates build dependencies" \
      license="Apache2.0" \
      int.skao.team="Systems Team" \
      int.skao.website="https://gitlab.com/ska-telescope/sdi/ska-ser-containerisation-and-orchestration"

# point to built libraries - to be copied below
ENV PYTHONPATH=/app/lib/python3.9/site-packages

# do not buffer stdout - so we get the logs
ENV PYTHONUNBUFFERED=1

# copy the built library dependencies from the builder stage
COPY --from=builder /app /app
```

Setting the User Environment
----------------------------

We are now on the way to wrapping up our containerised `echoserver`.  The following creates a specific runtime user account, sets the default working directory for the container runtime, and then switches the default runtime user to this account.  This will stop the application running as root, increasing the diffculty of an attacker being able to escalate priviledges and/or breaking out of the container:
```dockerfile
# Create the user for running the app
RUN adduser -h /app -D app
WORKDIR /app
USER app
```

We now add the simple Python Bottle echo application:
```dockerfile
# copy over application
COPY ./echo.py /app/echo.py
```

Ports and Volumes
-----------------

Ports and volumes are not strictly required to be defined in an Image, but it is good practice to do so as it provides documentary evidence of the intent of use of them:
```dockerfile
# expose ports
EXPOSE 8080
```

The End
-------

Finally, we add default `ENTRYPOINT` and `CMD` which describe the default application to launch and the default arguments to pass to that application:
```dockerfile
# default launcher for app
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/echo.py"]
```

The complete OCI Image definition can be found in [Dockerfile.alpine](./Dockerfile.alpine).

The entire build and run process can be executed as follows from the `ex02` directory:
```console
$ docker build --pull --build-arg base_image="python:3.9.5-alpine" -f Dockerfile.alpine --tag "ex02-echoserver:0.0.1" .
Sending build context to Docker daemon  41.47kB
Step 1/19 : ARG base_image="python:3.9.5-alpine"
Step 2/19 : FROM $base_image AS builder
3.9.5-alpine: Pulling from library/python
Digest: sha256:27c650557ac417c20c4257e669ccd08c1df51966e36e2aab48b83076ea2c2122
Status: Image is up to date for python:3.9.5-alpine
 ---> 2d64a2341b7c
Step 3/19 : ENV PYTHONPATH=${PYTHONPATH}:../:/
 ---> Using cache
 ---> 9d31202cb7e3
Step 4/19 : RUN apk add --no-cache     alpine-sdk     build-base     --virtual build-dependencies     linux-headers     make
 ---> Using cache
 ---> 42089b16bb30
Step 5/19 : COPY requirements.txt ./
 ---> Using cache
 ---> 7b93c253e332
Step 6/19 : RUN pip3 install -r /requirements.txt --prefix /app
 ---> Using cache
 ---> 424fcd2b9265
Step 7/19 : ARG base_image="python:3.9.5-alpine"
 ---> Using cache
 ---> a93e47d92f04
Step 8/19 : FROM $base_image
3.9.5-alpine: Pulling from library/python
Digest: sha256:27c650557ac417c20c4257e669ccd08c1df51966e36e2aab48b83076ea2c2122
Status: Image is up to date for python:3.9.5-alpine
 ---> 2d64a2341b7c
Step 9/19 : LABEL       author="Piers Harding <Piers.Harding@skao.int>"       description="This image illustrates build dependencies"       license="Apache2.0"       int.skao.team="Systems Team"       int.skao.website="https://gitlab.com/ska-telescope/sdi/ska-ser-containerisation-and-orchestration"
 ---> Using cache
 ---> b07560d495e7
Step 10/19 : ENV PYTHONPATH=/app/lib/python3.9/site-packages
 ---> Using cache
 ---> ec5763f6a253
Step 11/19 : ENV PYTHONUNBUFFERED=1
 ---> Using cache
 ---> e77ba0d37613
Step 12/19 : COPY --from=builder /app /app
 ---> Using cache
 ---> 82c7337bea15
Step 13/19 : RUN adduser -h /app -D app
 ---> Using cache
 ---> 4af34fd7c897
Step 14/19 : WORKDIR /app
 ---> Using cache
 ---> 1cc64787c10a
Step 15/19 : USER app
 ---> Using cache
 ---> 02d2697258e3
Step 16/19 : COPY ./echo.py /app/echo.py
 ---> Using cache
 ---> f61d2e6e2e87
Step 17/19 : EXPOSE 8080
 ---> Using cache
 ---> d1fb4e9ed556
Step 18/19 : ENTRYPOINT ["/usr/local/bin/python3"]
 ---> Using cache
 ---> da63c7178cbb
Step 19/19 : CMD ["/app/echo.py"]
 ---> Using cache
 ---> 30eac577846f
Successfully built 30eac577846f
Successfully tagged ex02-echoserver:0.0.1
$ docker run  --name ex02-echo --publish 8082:8080 -d ex02-echoserver:0.0.1
18ea4e6d96f98307ad96de44105b4bd5fec7e80d4a1251d51ef46cbce3893bf6

# Now, point your browser or curl at: http://0.0.0.0:8082/blah/blah

$ curl http://0.0.0.0:8082/blah/blah
# <b>Got: blah/blah</b>!
```

Clean up:
```console
$ docker rm -f ex02-echo
ex02-echo
```

[Home &#x3e;&#x3e;](../README.md)
