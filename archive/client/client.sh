#!/bin/bash
if [ "$RUN_MODE" != "docker" ]; then
    echo "Error: RUN_MODE environment variable is not set to 'docker'."
    echo "Are you looing for thinclient? If so, run thinclient.py!"
    exit 1
fi
ansible-playbook entrypoint.yml  -c local --tags run 

sed -i 's/ \{2,\}/ /g' /opt/waddleperf/iperf3-client

py4web run web/apps
