#!/bin/bash
echo "Username: "
read IPERF_USERNAME
echo "Password: "
read IPERF_PASSWORD
ansible-playbook /opt/manager/entrypoint.yml  -c local --tags hash
