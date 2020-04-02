# MVP testing

All testing to be done as a stage in the ci pipeline for the MVP is contained within this directory. This includes general types of tests, functional tests, acceptance tests etc.

For tests specifically to do with acceptig a feature/story or requirement refer to the [acceptance_tests folder](/tests/acceptance_tests/README.md) for more information.

Note, this directory is uploaded to the container when 'make test' is executed. Files
in this directory will be found inside /build once uploaded to the container.

