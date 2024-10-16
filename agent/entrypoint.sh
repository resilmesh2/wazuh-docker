#!/usr/bin/env sh
/etc/init.d/wazuh-agent start
cd /agent/openc2_actuator
mkfifo actuator_logs
python3 -m actuator | tee actuator_logs | tail -F actuator_logs /var/ossec/logs/ossec.log 2>&1
