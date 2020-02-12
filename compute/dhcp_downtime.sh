#!/bin/bash

#echo "Stopping tripleo_ovn_controller"
systemctl stop tripleo_ovn_controller
#echo "Sleeping 5 seconds"
sleep 5
#echo "Starting the awesome script in the background"
python test_dhcp_request.py -n reference -i reference &
script_pid=$!
#echo "Starting tripleo_ovn_controller"
systemctl start tripleo_ovn_controller
#echo "Waiting for the awesome script to finish"
wait $script_pid
