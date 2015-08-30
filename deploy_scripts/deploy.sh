#!/bin/bash

# We can deploy directly to a vm. The URL has to be usable by scp!

# Argument = -u user -m vm -p deploypath

usage()
{
cat << EOF
usage: $0 options

This script creates a tar ball of slingshot and when specified depolys the
tarball to a given vm.

OPTIONS:
-h    Show this message
-u    User (defaults to slingshot)
-m    Virtual Machine to use
-p    Path on vm to which should be deploied (defaults to ~/)
EOF
}

USER=
VM=
DEPLOY_PATH=

while getopts "hlu:m:p:" OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    u)
      USER=$OPTARG
      ;;
    m)
      VM=$OPTARG
      ;;
    l)
      LOCAL=1
      ;;
    p)
      DEPLOY_PATH=$OPTARG
      ;;
    ?)
      usage
      exit
      ;;
  esac
done

python setup.py sdist
cp vm_jaunty_setup_root.sh dist/
cp vm_jaunty_setup.sh dist/
cp cleanup_scripts/cleanup.sh dist/
cd dist/
tar -czf slingshot-bootstrap.tar.gz slingshot-0.1.tar.gz vm_jaunty_setup_root.sh  vm_jaunty_setup.sh cleanup.sh
rm vm_jaunty_setup.*
rm cleanup.sh

if [ $LOCAL ]; then
    echo "Deploy locally to $DEPLOY_PATH"
    cp slingshot-0.1.tar.gz ~/$DEPLOY_PATH
fi

if [ $VM ]; then
  if [ -z $USER ]
  then
    echo "Deploy to $VM:$DEPLOY_PATH"
    scp slingshot-bootstrap.tar.gz $VM:$DEPLOY_PATH || echo "ERROR: could not deploy to $VM"
  else
    echo "Deploy to $USER@$VM:$DEPLOY_PATH"
    scp slingshot-bootstrap.tar.gz $USER@$VM:$DEPLOY_PATH || echo "ERROR: could not deploy to $VM"
  fi
fi
