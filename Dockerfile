FROM wazuh/resilmesh_tap_wazuh_manager:4.9.0

RUN yum install pip -y && yum clean all && pip3 install nats-py --no-cache-dir
