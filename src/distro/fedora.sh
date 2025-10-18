#!/usr/bin/env bash

#TEST: When you use same home partition when you switch distro, selinux context is not correct
#NOTE: this happens because of on of the rsync subcommand not get selinux context right
#TODO: add option
selinux_context() {
  log_info "Restoring SELinux context for home directory..."

  # Execute command directly instead of using log_cmd
  if ! restorecon -R /home/; then
    log_error "Failed to restore SELinux context for /home/"
    return 1
  fi

  log_info "SELinux context restored successfully."
}

#TODO: need little research on this to make it more efficient
mirror_country_change() {
  log_info "Changing Fedora mirror country..."
  # on /etc/yum.repos.d/fedora.repo and similar repos need only `&country=de` in the end on metalink
  # metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-$releasever&arch=$basearch&country=de
  # variable mirror_country="de" handled on variable.sh
  # also there is 3 metalink on the files generally, [fedora-source], [fedora] and [fedora-debuginfo]
  # also need to commeent the baseurl
}
