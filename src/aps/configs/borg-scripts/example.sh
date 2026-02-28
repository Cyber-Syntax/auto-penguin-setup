#!/bin/sh
# The following example script is meant to be run daily by the root user on different local machines. 
# It backs up a machine’s important files (but not the complete operating system) 
# to a repository ~/backup/main on a remote server. 
# Some files which aren’t necessarily needed in this backup are excluded. 
# See borg help patterns on how to add more exclude options.
#
# After the backup this script also uses the borg prune subcommand to keep only 
# a certain number of old archives and deletes the others.
# Finally, it uses the borg compact subcommand to remove deleted objects 
# from the segment files in the repository to preserve disk space.
#
# Before running, make sure that the repository is initialized as documented in 
# Remote repositories and that the script has the correct permissions to be executable by the root user,
#  but not executable or readable by anyone else, i.e. root:root 0700.
#
# You can use this script as a starting point and modify it where it’s necessary to fit your setup.
#
# Do not forget to test your created backups to make sure everything you need is being 
# backed up and that the prune command is keeping and deleting the correct backups.

# Setting this, so the repo does not need to be given on the commandline:
export BORG_REPO=ssh://username@example.com:2022/~/backup/main

# See the section "Passphrase notes" for more infos.
export BORG_PASSPHRASE='XYZl0ngandsecurepa_55_phrasea&&123'

# some helpers and error handling:
info() { printf "\n%s %s\n\n" "$( date )" "$*" >&2; }
trap 'echo $( date ) Backup interrupted >&2; exit 2' INT TERM

info "Starting backup"

# Backup the most important directories into an archive named after
# the machine this script is currently running on:

borg create                         \
    --verbose                       \
    --filter AME                    \
    --list                          \
    --stats                         \
    --show-rc                       \
    --compression lz4               \
    --exclude-caches                \
    --exclude 'home/*/.cache/*'     \
    --exclude 'var/tmp/*'           \
                                    \
    ::'{hostname}-{now}'            \
    /etc                            \
    /home                           \
    /root                           \
    /var

backup_exit=$?

info "Pruning repository"

# Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
# archives of THIS machine. The '{hostname}-*' matching is very important to
# limit prune's operation to this machine's archives and not apply to
# other machines' archives also:

borg prune                          \
    --list                          \
    --glob-archives '{hostname}-*'  \
    --show-rc                       \
    --keep-daily    7               \
    --keep-weekly   4               \
    --keep-monthly  6

prune_exit=$?

# actually free repo disk space by compacting segments

info "Compacting repository"

borg compact

compact_exit=$?

# use highest exit code as global exit code
global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))
global_exit=$(( compact_exit > global_exit ? compact_exit : global_exit ))

if [ ${global_exit} -eq 0 ]; then
    info "Backup, Prune, and Compact finished successfully"
elif [ ${global_exit} -eq 1 ]; then
    info "Backup, Prune, and/or Compact finished with warnings"
else
    info "Backup, Prune, and/or Compact finished with errors"
fi

exit ${global_exit}