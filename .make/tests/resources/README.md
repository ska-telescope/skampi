SKA Python Skeleton Project
===========================

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-templates-ska-python-skeleton/badge/?version=latest)](https://developer.skatelescope.org/projects/ska-python-skeleton/en/latest/?badge=latest)

Briefly describe your project here

Requirements
------------

The system used for development needs to have Python 3 and `pip` installed.

Install 
-------

**Always** use a virtual environment. [Pipenv](https://pipenv.readthedocs.io/en/latest/) is now Python's officially
recommended method, but we are not using it for installing requirements when building on the CI Pipeline. You are encouraged to use your preferred environment isolation (i.e. `pip`, `conda` or `pipenv` while developing locally.

For working with `Pipenv`, follow these steps at the project root:

First, ensure that `~/.local/bin` is in your `PATH` with:
```bash
> echo $PATH
```

In case `~/.local/bin` is not part of your `PATH` variable, under Linux add it with:
```bash
> export PATH=~/.local/bin:$PATH
```
or the equivalent in your particular OS.

Then proceed to install pipenv and the required environment packages:

```bash
> pip install pipenv # if you don't have pipenv already installed on your system
> pipenv install
> pipenv shell
```

You will now be inside a pipenv shell with your virtual environment ready.

Use `exit` to exit the pipenv environment.


Testing
-------

* Put tests into the `tests` folder
* Use [PyTest](https://pytest.org) as the testing framework
  - Reference: [PyTest introduction](http://pythontesting.net/framework/pytest/pytest-introduction/)
* Run tests with `python setup.py test`
  - Configure PyTest in `setup.py` and `setup.cfg`
* Running the test creates the `htmlcov` folder
    - Inside this folder a rundown of the issues found will be accessible using the `index.html` file
* All the tests should pass before merging the code 
 
 Code analysis
 -------------
 * Use [Pylint](https://www.pylint.org) as the code analysis framework
 * By default it uses the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/)
 * Use the provided `code-analysis.sh` script in order to run the code analysis in the `module` and `tests`
 * Code analysis should be run by calling `pylint ska_python_skeleton`. All pertaining options reside under the `.pylintrc` file.
 * Code analysis should only raise document related warnings (i.e. `#FIXME` comments) before merging the code
 
Writing documentation
 --------------------
 * The documentation generator for this project is derived from SKA's [SKA Developer Portal repository](https://github.com/ska-telescope/developer.skatelescope.org)
 * The documentation can be edited under `./docs/src`
 * If you want to include only your README.md file, create a symbolic link inside the `./docs/src` directory if the existing one does not work:
 ```bash
$ cd docs/src
$ ln -s ../../README.md README.md
```
 * In order to build the documentation for this specific project, execute the following under `./docs`:
 ```bash
$ make html
```
* The documentation can then be consulted by opening the file `./docs/build/html/index.html`

Development
-----------

### PyCharm

As this project uses a `src` [folder structure](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure),
under _Preferences > Project Structure_, the `src` folder needs to be marked as "Sources".  That will
allow the interpreter to be aware of the package from folders like `tests` that are outside of `src`.
When adding Run/Debug configurations, make sure "Add content roots to PYTHONPATH" and
"Add source roots to PYTHONPATH" are checked.
