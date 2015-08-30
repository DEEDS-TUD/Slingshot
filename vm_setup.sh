#!/bin/bash
function parse_options() {
  while getopts ":utfd" optchar;
  do
    case "${optchar}" in
      u)
        log "We are going to upgrade all packages!!"
        upgrade=1
        ;;
      d)
        log "DELETE DATABASE!"
        delete=1
        ;;
      *)
        log "No options!"
        ;;
    esac
  done
}

function log() {
  printf '%s\n' "$(tput setaf 3)vm_setup:$(tput sgr0) $1"
}

function install_pythonbrew() {
    log "Install pythonbrew"
    TEMP_TARBALL="pythonbrew-1.3.4.tar.gz"
    if [ -r ${TEMP_TARBALL} ] ; then
	ROOT="$HOME/.pythonbrew"
	PATH_DISTS="$ROOT/dists"
	TEMP_FILE="pythonbrew-1.3.4"
	PYTHON=$(command -v python)
	mkdir -p "$PATH_DISTS"
	rm -rf "$PATH_DISTS/$TEMP_TARBALL"
	rm -rf "$PATH_DISTS/$TEMP_FILE"
	mv $TEMP_TARBALL $PATH_DISTS
	log "Extracting $PATH_DISTS/$TEMP_TARBALL"
	cd $PATH_DISTS ; tar zxf $TEMP_TARBALL
	$PYTHON $PATH_DISTS/$TEMP_FILE/pythonbrew_install.py
	if [[ $? == 1 ]] ; then
	    log "Failed to install pythonbrew."
	    exit
	fi
	cd -
    else
	curl -kL http://xrl.us/pythonbrewinstall | bash
    fi
    [ -s $HOME/.pythonbrew/etc/bashrc ] && echo "source $HOME/.pythonbrew/etc/bashrc" >> $HOME/.bashrc
    source $HOME/.pythonbrew/etc/bashrc
}

function setup_slingshot_environment() {
  log "Installing python 2.7.2"
  pythonbrew install 2.7.2
  log "Switch python version to 2.7.2"
  pythonbrew switch 2.7.2
  log "Initialise virtual-environment"
  pythonbrew venv init
  log "Create virtual-environment 'slingshot_venv'"
  pythonbrew venv create slingshot_venv
}

function pythonbrew_not_installed() {
  [ ! -d $HOME/.pythonbrew ];
}

function use_slingshot_environment() {
  pythonbrew venv use slingshot_venv
}

function setup_python_build_system() {
  if pythonbrew_not_installed; then
    install_pythonbrew
    setup_slingshot_environment
  fi
  use_slingshot_environment
}

function install_slingshot() {
    log "Install slingshot into virtual-environment"
    SLINGSHOT_ARCHIVE="slingshot-0.2.tar.gz"
    if [ -r ${SLINGSHOT_ARCHIVE} ] ; then # no package available... we assume we're where the sources are
	SLINGSHOT_BUILD_DIR="dist"
	pythonbrew venv use slingshot_env
	python setup.py sdist
	deactivate
	mv -v ${SLINGSHOT_BUILD_DIR}/${SLINGSHOT_ARCHIVE} .
    fi
    if [ $upgrade ]; then
	log "Install with dependencies"
	pip install --upgrade ./${SLINGSHOT_ARCHIVE}
    else
	log "Install without dependencies"
	pip install --upgrade --no-deps ./${SLINGSHOT_ARCHIVE}
    fi
}

function reset_database() {
  log "Create database 'slingshot' to use for db user 'slingshot'"
  mysql -u root --password=slingshot -e "DROP DATABASE slingshot" #&> /dev/null
  mysql -u root --password=slingshot -e "CREATE DATABASE slingshot CHARACTER SET utf8; GRANT ALL ON slingshot.* TO 'slingshot'@'%' IDENTIFIED BY 'slingshot' WITH GRANT OPTION; GRANT ALL ON slingshot.* TO 'slingshot'@'localhost' IDENTIFIED BY 'slingshot' WITH GRANT OPTION;" #&> /dev/null
  log "Initialise database with schema"
  mysql -u slingshot --password=slingshot slingshot < $HOME/.pythonbrew/venvs/Python-2.7.2/slingshot_venv/lib/python2.7/site-packages/slingshot/db/init_db_mysql.sql
  log "Deleted database!"
}

function main() {
  parse_options "$@"
  setup_python_build_system
  install_slingshot
  if [ $delete ]; then
    reset_database
  fi
}

main "$@"

