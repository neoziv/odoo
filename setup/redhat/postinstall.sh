#!/bin/sh

set -e

neoziv_CONFIGURATION_DIR=/etc/neoziv
neoziv_CONFIGURATION_FILE=$neoziv_CONFIGURATION_DIR/neoziv.conf
neoziv_DATA_DIR=/var/lib/neoziv
neoziv_GROUP="neoziv"
neoziv_LOG_DIR=/var/log/neoziv
neoziv_LOG_FILE=$neoziv_LOG_DIR/neoziv-server.log
neoziv_USER="neoziv"
ABI=$(rpm -q --provides python3 | awk '/abi/ {print $NF}')

if ! getent passwd | grep -q "^neoziv:"; then
    groupadd $neoziv_GROUP
    adduser --system --no-create-home $neoziv_USER -g $neoziv_GROUP
fi
# Register "$neoziv_USER" as a postgres user with "Create DB" role attribute
su - postgres -c "createuser -d -R -S $neoziv_USER" 2> /dev/null || true
# Configuration file
mkdir -p $neoziv_CONFIGURATION_DIR
# can't copy debian config-file as addons_path is not the same
if [ ! -f $neoziv_CONFIGURATION_FILE ]
then
    echo "[options]
; This is the password that allows database operations:
; admin_passwd = admin
db_host = False
db_port = False
db_user = $neoziv_USER
db_password = False
addons_path = /usr/lib/python${ABI}/site-packages/neoziv/addons
" > $neoziv_CONFIGURATION_FILE
    chown $neoziv_USER:$neoziv_GROUP $neoziv_CONFIGURATION_FILE
    chmod 0640 $neoziv_CONFIGURATION_FILE
fi
# Log
mkdir -p $neoziv_LOG_DIR
chown $neoziv_USER:$neoziv_GROUP $neoziv_LOG_DIR
chmod 0750 $neoziv_LOG_DIR
# Data dir
mkdir -p $neoziv_DATA_DIR
chown $neoziv_USER:$neoziv_GROUP $neoziv_DATA_DIR

INIT_FILE=/lib/systemd/system/neoziv.service
touch $INIT_FILE
chmod 0700 $INIT_FILE
cat << EOF > $INIT_FILE
[Unit]
Description=neoziv Open Source ERP and CRM
After=network.target

[Service]
Type=simple
User=neoziv
Group=neoziv
ExecStart=/usr/bin/neoziv --config $neoziv_CONFIGURATION_FILE --logfile $neoziv_LOG_FILE
KillMode=mixed

[Install]
WantedBy=multi-user.target
EOF
