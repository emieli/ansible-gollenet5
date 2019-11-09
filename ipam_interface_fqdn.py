#!/usr/bin/env python

import os
import sys
import argparse

try:
    import json
except ImportError:
    import simplejson as json
    
import requests

# Returns input in json format
def to_json(input):
    return json.dumps(input, indent = 2, sort_keys=True)

def ipam_get_token():
    
    ipam_username = "gollenet5"
    ipam_password = "gollenet5"
    
    # Get IPAM API Token
    ipam_request = requests.post(ipam_url_token_request, auth=(ipam_username, ipam_password))
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to ipam token: " + str(output))
    
    return ipam_request.json()['data']['token']

# Depends on having an API token from IPAM
# Depends on inventory having devices in it
def ipam_get_device_addresses(token):
    
    # 1. Get devices from IPAM
    ipam_request = requests.get(ipam_url_devices, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve devices: " + str(output))
        
    devices = {}
    for device in ipam_request.json()['data']:
        #devices[device['hostname']]       = device
        devices[device['id']]       = device
        
    # 2. Get device addresses
    device_addresses = {}
    for host, host_values in devices.iteritems():
      
        # Loop through all hosts, getting their addresses
        ipam_url_device_addresses = ipam_url_devices + host_values['id'] + "/addresses/"
        ipam_request = requests.get(ipam_url_device_addresses, headers={'token': token })
        if ipam_request.json()['code'] != 200:
            sys.exit("Error: Unable to retrieve device addresses: " + str(ipam_request.json()))
          
        if 'data' not in ipam_request.json():
            continue
      
        device_addresses[host] = ipam_request.json()['data']
    
    return devices, device_addresses    

# IPAM variables:
# https://phpipam.net/api/api_documentation/
ipam_url_token_request      = "http://ipam.golle.org/api/gollenet5/user/"
ipam_url_devices            = "http://ipam.golle.org/api/gollenet5/devices/"
ipam_url_section_subnets    = "http://ipam.golle.org/api/gollenet5/sections/5/subnets/"
ipam_url_addresses    		= "http://ipam.golle.org/api/gollenet5/addresses/"

def ipam_set_interface_hostname(token, devices, device_addresses):
	
	for device, device_address in device_addresses.iteritems():
		
		# Get hostname from devices list:
		hostname = devices[address['deviceId']]['hostname']
		
		for address in device_address:
			
			# Use custom_port if it has value, otherwise use custom_interface:
			if address['custom_port'] is not None:
				fqdn = hostname + "_" + address['custom_port'].replace("/", "-") + ".golle5.net"
			else:
				fqdn = hostname + "_" + address['custom_interface'].replace("/", "-") + ".golle5.net"
				
			# Send PATCH message to IPAM with the updated hostname field:
			payload 	 = { 'hostname': fqdn }
			url 		 = ipam_url_addresses + address['id']
			ipam_request = requests.patch(url, payload, headers={'token': token })
    		if ipam_request.json()['code'] != 200:
    		    sys.exit("Error: Unable to update address: " + str(ipam_request.json()))
    		
    		# Print what we did
    		print "Address updated in IPAM: " + fqdn
	
	return

def main():

    # Get data from IPAM:
    token            			= ipam_get_token()
    devices, device_addresses   = ipam_get_device_addresses(token)
    
    # Update IPAM address with the hostname_<interface>.golle5.net FQDN:
    ipam_set_interface_hostname(token, devices, device_addresses)
    
main()