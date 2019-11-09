#!/usr/bin/env python

# Example custom dynamic inventory script for Ansible, in Python:
# https://www.jeffgeerling.com/blog/creating-custom-dynamic-inventories-ansible

import os
import sys
import argparse

try:
    import json
except ImportError:
    import simplejson as json
    
# Requests is used to send HTTP GET and POST messages, allows for REST API access.
# installation (change pip to pip3 for python3):
#   sudo apt install python-pip
#   sudo pip install requests
import requests

# Returns input in json format
def to_json(input):
    return json.dumps(input, indent = 2, sort_keys=True)
    
class c_phpipam:
    
    def __init__(self):
    
        ipam_username          = "gollenet5"
        ipam_password          = "gollenet5"
        ipam_url_token_request = "http://ipam.golle.org/api/gollenet5/user/"
        
        # Get IPAM API Token, save to self.token
        r = requests.post(ipam_url_token_request, auth=(ipam_username, ipam_password), timeout=10)
        if r.json()['code'] != 200:
            sys.exit("Error: Unable to ipam token: " + str(output))
        
        self.token = r.json()['data']['token']
        
        self.devices, self.device_addresses = self.get_device_addresses()
        self.device_types = self.get_device_types()
        self.section_subnets = self.get_section_subnets()
        self.vrfs = self.get_vrfs()
        self.vlans = self.get_vlans()
    
    def send_request_get(self, url):
        r = requests.get(url, headers={'token': self.token })
        if r.json()['code'] != 200:
            sys.exit("Error: Unable to retrieve " + url + ": " + str(r.json()))
        return r.json()['data']
    
    # Patch messages update existing entried in the IPAM with new values
    def send_request_patch(self, url, payload):
        r = requests.patch(url, payload, headers={'token': self.token })
        if r.json()['code'] != 200:
            sys.exit("Error: Unable to update address: " + str(r.json()))
        return r.json()['data']
            
    def get_device_types(self):
        
        url = "http://ipam.golle.org/api/gollenet5/tools/device_types/" 
        device_types = {}
        
        for device_type in self.send_request_get(url):        
            device_types[device_type['tid']] = {}
            device_types[device_type['tid']]['tname'] = device_type['tname']
            device_types[device_type['tid']]['tdescription'] = device_type['tdescription']  
         
        return device_types
        
    def get_device_addresses(self):
        
        url_devices = "http://ipam.golle.org/api/gollenet5/devices/"            
        
        # Get Devices from IPAM
        devices = {}
        for device in self.send_request_get(url_devices):
            devices[device['hostname']] = device
        
        # For each device, get their addresses from IPAM
        device_addresses = {}
        for host, host_values in devices.items():          
            device_addresses[host] = self.send_request_get(url_devices)
            
        return devices, device_addresses

    def get_section_subnets(self):
        
        url = "http://ipam.golle.org/api/gollenet5/sections/5/subnets/"
        section_subnets = {}
        for subnet in self.send_request_get(url):
            section_subnets[subnet['id']] = subnet
            
        return section_subnets

    def get_vrfs(self):
        
        url = "http://ipam.golle.org/api/gollenet5/vrf/"
        vrfs = {}            
        for vrf in self.send_request_get(url):
            vrfs[vrf['vrfId']] = vrf
        
        return vrfs
        
    def get_vlans(self):
        
        url = "http://ipam.golle.org/api/gollenet5/vlan/"
        vlans = {}
        for vlan in self.send_request_get(url):
            vlans[vlan['vlanId']] = vlan
        
        return vlans

# ipam = c_phpipam()
# print to_json(ipam.vlans)
        
class c_inventory(object):
    
    def __init__(self):
        
        # Read CLI args:
        self.args = self.get_cli_args()
        if self.args.list:
            #print to_json(self.inventory)
            pass
        elif self.args.host:
            #print "You wanted host " + self.args.host
            pass
        else:
            sys.exit("No list or host argument given, add -h for help menu.")
            
        # Minimum accepted inventory by ansible:
        self.inventory = {'_meta': {'hostvars': {}}}
        
        # Get data from IPAM to populate our inventory
        self.ipam = c_phpipam()
        
        self.inventory['_meta']['hostvars'] = self.inventory_hostvars()
        self.inventory_groups()
                
        print (to_json(self.inventory))
    
    # Return the command line args passed to the script
    def get_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        return parser.parse_args()
    
    # Return all host variables as learned from IPAM:
    def inventory_hostvars(self):
        
        hostvars = {}
        for host, host_values in self.ipam.devices.items():
            
            hostvars[host] = {}
            hostvars[host]['id']   = host_values['id']
            
            # Add name and id of device type to hostvars
            hostvars[host]['type'] = host_values['type']
            
            # If a device IP is manually set in IPAM, use it over resolving hostname in DNS:
            if host_values['ip'] is not None:
                hostvars[host]['ansible_host'] = host_values['ip']
            
        return hostvars
    
    # Adds hosts to their respective groups, built from ipam.devices and ipam.device_types:    
    def inventory_groups(self):
        
        for host, host_values in self.ipam.devices.items():
            
            # We use hostvars['type'] to get the name of the device type (P,PE,PEER etc), which we create as a group in Ansible:            
            group_id   = host_values['type']
            group_name = self.ipam.device_types[group_id]['tname']
            
            # Create group if not exists:
            if group_name not in self.inventory:
                self.inventory[group_name] = {}
                self.inventory[group_name]['hosts'] = []
                
            # Add host to group:
            self.inventory[group_name]['hosts'].append(host)
            
    def inventory_hostvars_interfaces(self):
        
        # Loop through every host
        for host, host_values in self.device_addresses.items():
                  
            # If host does not have a key named interface, create it:
            if 'interface' not in inventory['_meta']['hostvars'][host]:
                inventory['_meta']['hostvars'][host]['interface'] = {}
          
            for interface in host_values:
              
                # We use the subnetId to find the name of the subnet. A bit clunky but necessary.
                interface_name   = self.section_subnets[interface['subnetId']]['description']
                interface_values = {}
              
                # subnet vars
                interface_values['ipv4'] = interface['ip'] + "/" + self.section_subnets[interface['subnetId']]['mask']
              
                # address vars
                interface_values['interface']   = interface['custom_interface']
                interface_values['description'] = interface['description']
                interface_values['port']        = interface['custom_port']
                interface_values['state']       = "present"
              
                # VLAN vars:
                if section_subnets[interface['subnetId']]['vlanId'] in vlans:
                    interface_values['vlan']           = {}
                    interface_values['vlan']['id']     = vlans[self.section_subnets[interface['subnetId']]['vlanId']]['vlanId']
                    interface_values['vlan']['number'] = vlans[self.section_subnets[interface['subnetId']]['vlanId']]['number']
              
                # VRF vars
                if section_subnets[interface['subnetId']]['vrfId'] in vrfs:
                    interface_values['vrf']              = {}
                    interface_values['vrf']['id']        = self.section_subnets[interface['subnetId']]['vrfId']
                    interface_values['vrf']['name']      = vrfs[interface_values['vrf']['id']]['name']
                    interface_values['vrf']['rd']        = vrfs[interface_values['vrf']['id']]['rd']
                    interface_values['vrf']['rt_import'] = vrfs[interface_values['vrf']['id']]['custom_rt_import']
                    interface_values['vrf']['rt_export'] = vrfs[interface_values['vrf']['id']]['custom_rt_export']
              
                inventory['_meta']['hostvars'][host]['interface'][interface_name] = interface_values

        print(inventory)        

# Script "starts" here:
c_inventory()

