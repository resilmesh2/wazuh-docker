#!/usr/bin/env sh
/etc/init.d/wazuh-agent start
tail -F /var/ossec/logs/ossec.log
