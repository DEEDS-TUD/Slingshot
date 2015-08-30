# Slingshot
__Robustness Testing of LSB core library functions using fault injection.__

## Project background

Slingshot is a Python re-implementation of the [Ballista&copy;](http://www.cs.cmu.edu/afs/cs/project/edrc-ballista/www/) test tool for the Linux Standard Base (LSB). Unlike Ballista, Slingshot is not concerned with portability to a large variety of diverse POSIX implementations. This allows Slingshot to adopt wide spread and easily extensible data representations and programming languages and, thereby, facilitates its co-evolution with Linux and the LSB.

## Project status

We have used Slingshot to test the LSB implementation of Ubuntu Linux distributions. We are currently refactoring the tool to achieve better performance for the massive amounts of tests that need to be created, compiled, and run. Documentation and tests are also under development and the documentation on this page is outdated. The version published here is not stable and probably does not run out of the box on most systems. If you are considering to use this version of Slingshot, please get in contact with us for more information: <slingshot@deeds.informatik.tu-darmstadt.de>.

## Requirements
Slingshot is intended to work on most Linux systems, however it was so far only used to test
versions of Ubuntu. The installation scripts assume the package manager
`apt-get` and it's repository configuration file `/etc/apt/sources.list`.
Slingshot uses Python 2.7.2.

## Installation

Slingshot should be packaged as a python package as a tarball and installed with pip.
The recommended way to package and install python is with the supplied scripts.
Instructions are given below.

### Create and deploy tarball
In order to create a packaged version of slingshot and to deploy it use
`deploy_scripts/deploy.sh`. The available options are:

        -l    Deploy to local path
        -u    User (defaults to slingshot)
        -m    Host to use
        -p    Path on host to which should be deploied (defaults to ~/)

I.e. to deploy locally to the directory `~/somedir/testing`

        $ ./deploy_scripts/deploy.sh -l ~/somedir/testing

Or to deploy for user `zaphod` at host `betelgeuse` into the directory
`~/testing`

        $ ./deploy_scripts/deploy.sh -u zaphot -m betelgeuse -p testing

This creates the tar-ball `slingshot-bootstrap.tar.gz` in the specified location.

### Install slingshot from tar-ball
Extract the tar-ball

        $ tar -xzf slingshot-bootstrap.tar.gz

Run the installation script as root. ATTENTION after the script completes a
reboot is performed!

        $ sudo ./setup_root.sh

The installation script updates all pre installed packages and installs all
further required packages with the package manager `apt-get`. MYSQL is installed
and configured for user `slingshot` at database `slingshot` with password
`slingshot`. The python version manager pythonbrew is installed to
`~/.pythonbrew` and python version `2.7.2` is installed. Slingshot is installed
with pip into the virtual environment `slingshot_venv`.

(If the machine runs a Ubuntu version which is no longer supported the script
first patches `/etc/sources.list` to fetch packages from
old-releases.ubuntu.com.)

## Executing tests with slingshot
Slingshot can be used from within the virtual environment `slingshot_venv`
which was created in the installation process. To activate the environment:

        $ pythonbrew venv use slingshot_venv

### Initialize database
In order to run tests for a specific testcase list `(a_testcase_list.tcs)` the database has to
be initialized and filled with the appropriate data first.

        $ init_db -t a_testcase_list.tcs

This setup may require some time, so be patient.

#### Advanced options
        -u    database user (default: slingshot)
        -p    database password (default: slingshot)
        -s    server hosting database (default: localhost)
        -d    database (default: slingshot)
        -c    call table (default: bin/call_table)
        -m    type mapping (default: bin/type_mapping)
        -f    path to data type definitions (default: bin/dataTypes)
        -t    testcase list (mandatory)

### Run slingshot
Slingshot is then executed by simply running

        $ slingshot

#### Advanced options
        -u    database user (default: slingshot)
        -p    database password (default: slingshot)
        -s    server hosting database (default: localhost)
        -d    database (default: slingshot)
        -w    directory which should be used for the creation of testfiles (default: tmp)
        -t    Timeout after which a test is forcefully stopped (default: ?) !NOT USED!
        -o    Comma seperated list of self defined functions to test (only used for testing)
        -c    Flag if the working directory should be cleaned up periodicaly when executing tests. Cleanup is performed when the flag is ommitted.

## The slingshot repository
The slingshot repository contains the following files and folders:

        slingshot
        - deploy_scripts/
          |- deploy.sh
        - MANIFEST.in
        - pythonbrew-1.3.4.tar.gz
        - README.md
        - setup.py
        - slingshot/
          |- bin/
            |- ...
          |- core/
            |- ...
          |- db/
            |- ...
        - tests/
            |- ...
        - setup_root.sh
        - setup.sh

## Source code
Slingshots source code is located in the repository in the folder `slingshot`.
The source code is organised in the modules `bin`, `core` and `db`.

### bin
The bin module contains the default data type definitions, a default call
table, a default type mapping, the logger configuration as well as template
files.

### core
The core module contains the main implementation of slingshot.

### db
The db module contains the default database layout for the creation of the
database, the initialisation script to fill the database and an database gateway
which encapsulates all database interactions of slingshot.


## Runtime files
Which functions slingshot is going to test and which data type definitions
should be used for injection is configured with so called runtime files. These
runtime files are located in the `slingshot/bin` module. Here a brief
description of these files is given.

### call table
The call table provides additional information about functions which should be
tested. It is given in XML, against the schema `bin/ct.xsd`

### testcase list
List of testcases which should be executed. Each line correspond to a single
test case.

### data type specifications
A data type specification defines the different payloads which can be used
when injecting into a parameter with a matching type. Data type specifications
are given in XML, against the schema `bin/data_types.xsd`.

### type mapping
Maps the name of each data type specification to the appropriate C type.


## The database
TODO

### Layout
TODO

### Interpreting results
TODO

#### Helpful SQL queries
TODO
