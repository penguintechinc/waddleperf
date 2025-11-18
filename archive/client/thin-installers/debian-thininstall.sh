#! /bin/bash
$PPING_REPO = "wzv5/pping"

echo "Pulling latest version $VERSION"

sudo apt install iperf3 speedtest-cli httping python3-pip jq iputils-ping -y
pip3 install -r requirements.txt
ansible-playbook installer.yml -c local
export RUNMODE="thin"