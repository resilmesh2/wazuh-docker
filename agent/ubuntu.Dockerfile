FROM ubuntu:22.04
LABEL org.opencontainers.image.authors="ekam.purin@um.es,d.montoroaguilera@um.es"

# Wazuh manager address
ARG manager_ip
# Complete Wazuh agent version string.  Will take the form A.B.C[-D].
ARG agent_version="4.7.2-1"

ENV WAZUH_MANAGER $manager_ip

# Move entrypoint file
WORKDIR /agent
COPY entrypoint.sh ./

# Set up Wazuh package repository as a source
RUN apt-get update && \
    apt-get install -y curl gpg && \
    curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | \
    gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import && \
    chmod 644 /usr/share/keyrings/wazuh.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | \
    tee -a /etc/apt/sources.list.d/wazuh.list && \
    # Refresh package list after adding a new remote
    apt-get update

# Monitoring packages
RUN apt-get install -y netcat ncat lsof
# Wazuh agent
RUN apt-get install -y wazuh-agent=$agent_version && \
    # Protects the package from accidental upgrades
    apt-mark hold wazuh-agent

# OpenC2 Actuator
COPY openc2/actuator/openapi.yaml openc2/openapi-generator-cli.sh openc2/actuator/config-python-flask.json ./
COPY openc2/actuator/python-flask ./openc2_actuator
RUN apt-get install -y maven jq && \
    ./openapi-generator-cli.sh generate -g python-flask -c config-python-flask.json -i openapi.yaml -o openc2_actuator && \
    apt-get purge -y maven jq && \
    apt-get autoremove -y
RUN apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r openc2_actuator/requirements.txt && \
    apt-get purge -y python3-pip && \
    apt-get autoremove -y

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "./entrypoint.sh" ]
