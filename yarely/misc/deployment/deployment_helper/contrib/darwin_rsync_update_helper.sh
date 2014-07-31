#!/bin/sh

# Launch the rsync deployment helper and schedule a reboot if any codebases
# have been changed.  This script will pass all arguments through to the
# deployment helper.
# 
# To schedule a reboot, the user running this script must be listed in sudoers
# with permission to launch /sbin/shutdown without a password.  EG:
#
# pdnet ALL=NOPASSWD:/sbin/shutdown
# 

proc_name="`basename $0`"
change_log_file="`mktemp -t $proc_name`" || exit 1

helper="$HOME/proj/yarely/misc/deployment/deployment_helper/rsync_deployment_helper.py"

$helper --change-log-file "$change_log_file" "$@"

# If the change log file is not empty, schedule a reboot.
if [ -s "$change_log_file" ]; then
    sudo -n /sbin/shutdown -r +15
fi

rm "$change_log_file"
