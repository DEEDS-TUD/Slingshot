#!/bin/bash
set -u
set -e

# Install a package
# $1 - the name of the package
function install() {
  local -r package="$1"; shift
  if ! dpkg -s "$package" > /dev/null; then
    echo -e "Installing package"
    apt-get -y install "$package"
  else
    echo -e "$package is installed, skip"
  fi
}

# Replace mirror in sources.list with old-releases.ubuntu.com
# $1 - name of release
function replace_sourceslist() {
  echo -e "Ubuntu version is $1"
  echo -e "Update sources.list, mirror is now old-releases.ubuntu.com\n"
  cp /etc/apt/sources.list{,_backup}
  echo "deb http://old-releases.ubuntu.com/ubuntu/ $1 main restricted universe multiverse" > /etc/apt/sources.list
  echo "deb http://old-releases.ubuntu.com/ubuntu/ $1-updates main restricted universe multiverse" >> /etc/apt/sources.list
  echo "deb http://old-releases.ubuntu.com/ubuntu/ $1-security main restricted universe multiverse" >> /etc/apt/sources.list
}

# Check for ubuntu version
function update_sourceslist() {
  local -r -a old_versions=( 6.10 7.04 7.10 8.04 8.10 9.04 9.10 11.04 11.10 )
  for old_version in "${old_versions[@]}"; do
    if [[ "$version" == "$old_version" ]]; then
      replace_sourceslist "$code_name"
      break
    fi
  done
}

# Check if script is executed as root
function check_for_root() {
  if [[ $EUID -ne 0 ]]; then
     echo "This script must be run as root" 1>&2
     exit 1
  fi
}

function system_update() {
  echo -e "Update system!\n"
  apt-get -y update
  apt-get -y upgrade
}

function install_required_packages() {
  local -r -a system_packages=(
    openssh-server
    build-essential
    git-core
    mysql-server
    python-mysqldb
    libmysqlclient15-dev
    python-dev
    libxml2-dev
    libxslt1-dev
    curl
    vim-common
    screen
  )
  local -r -a pythonbrew_packages=(
    libbz2-dev
    libsqlite3-dev
    libgdbm-dev
    libssl-dev
    libexpat1-dev
    libncurses5-dev
  )

  # install system packages
  echo -e "Installing system packages\n"
  for package in "${system_packages[@]}"; do
    install "$package"
  done

  # install requirements for pythonbrew
  echo -e "\nInstalling pythonbrew requirements\n"
  for package in "${pythonbrew_packages[@]}"; do
    install "$package"
  done
}

function set_up_mysql() {
  # adjust mysql settings
  echo -e "Adjusting MySQL settings\n"
  sed -i -r "s/^(#\s*)?(max_allowed_packet\s*=\s*).*$/\2500M/g" /etc/mysql/my.cnf
  sed -i -r "s/^(#\s*)?(max_connections\s*=\s*).*$/\2100/" /etc/mysql/my.cnf
  sed -i -r "s/^(#\s*)?(bind-address\s*=\s*).*$/\20.0.0.0/" /etc/mysql/my.cnf
  /etc/init.d/mysql restart
}

function non_root() {
  chmod +x vm_setup.sh
  echo -e "Switching to normal user\n"
  su slingshot -c './vm_setup.sh -u'
  echo -e "Finished non root setup\n"
}

function parse_lsb_release() {
  version=$(awk '/RELEASE/{split($0,a,"="); print a[2]}' /etc/lsb-release)
  code_name=$(awk '/CODENAME/{split($0,a,"="); print a[2]}' /etc/lsb-release)
}

function set_terminal() {
  export TERM=linux
}

function set_locale() {
  export LANGUAGE=en_US.utf8
  export LANG=en_US.utf8
  export LC_ALL=en_US.utf8
  update-locale
}

function restart_system() {
  shutdown -r now
}

function main() {
  check_for_root
  set_locale
  set_terminal
  parse_lsb_release
  update_sourceslist
  system_update
  install_required_packages
  set_up_mysql
  non_root
  restart_system
}

main

