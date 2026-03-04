#!/usr/bin/env bash
#
# Script PATH: /usr/local/sbin/borg.sh
# Exclude file PATH: /usr/local/sbin/excludes.txt
#
set -o errexit
set -o nounset
set -o pipefail

# Check prerequisites
command -v borg >/dev/null 2>&1 || {
  echo >&2 "Borg is not installed. Please install it first."
  exit 1
}
[[ -d /mnt/backups/borgbackup ]] || {
  echo >&2 "Backup directory does not exist."
  exit 1
}

export BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes

BORG_HOME_REPO='/mnt/backups/borgbackup/home'
BORG_HOME_EXCLUDE_FILE="/usr/local/sbin/excludes.txt"
BORG_HOME_COMPRESSION='zstd,15'
BORG_HOME_BACKUP_NAME='{now:home-backup-%d-%m-%Y}'
BORG_HOME_BACKUP_SOURCE='/home/developer'

echo "Starting backup for home"

# --show-rc: if return 0 code, then it's successful
if ! borg create --list --filter=AME --progress --stats --exclude-caches --show-rc \
  --exclude-from "$BORG_HOME_EXCLUDE_FILE" \
  --compression "$BORG_HOME_COMPRESSION" "$BORG_HOME_REPO"::"$BORG_HOME_BACKUP_NAME" \
  "$BORG_HOME_BACKUP_SOURCE"; then
  echo "Backup of home directory failed" >&2
  exit 1
fi

echo "Backup of home directory complete"

if ! borg prune -v "$BORG_HOME_REPO" --list --stats --show-rc \
  --keep-daily=7 \
  --keep-weekly=4 \
  --keep-monthly=1; then
  echo "Pruning of home backups failed" >&2
  exit 1
fi

echo "Pruning of home backups complete"

if ! borg check "$BORG_HOME_REPO"; then
  echo "Check of home backups failed" >&2
  exit 1
fi
echo "borg check completed successfully"

if ! borg compact "$BORG_HOME_REPO"; then
  echo "Compaction of home backups failed" >&2
  exit 1
fi

echo "Compaction complete"

# Being paranoid here
sync

echo "Borg backup completed successfully"

