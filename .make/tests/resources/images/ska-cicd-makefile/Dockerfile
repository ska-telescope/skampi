ARG base_image="python"
ARG base_image_version="3.9.5-alpine"
FROM $base_image:$base_image_version AS builder

# set path
ENV PYTHONPATH=${PYTHONPATH}:../:/

# Add Alpine basic build dependencies
RUN apk add --no-cache \
    alpine-sdk=1.0-r1 \
    build-base=0.5-r3 \
    --virtual build-dependencies \
    linux-headers=5.10.41-r0 \
    make=4.3-r0

# Copy poetry.lock* in case it doesn't exist in the repo
COPY requirements.txt /

# Install Python runtime dependencies
RUN pip3 install --no-cache-dir -r /requirements.txt --prefix /app

FROM $base_image:$base_image_version
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

# Create the user for running the app
RUN adduser -h /app -D app
WORKDIR /app
USER app

# copy over application
COPY ./echo.py /app/echo.py

# expose ports
EXPOSE 8080

# default launcher for app
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/app/echo.py"]
