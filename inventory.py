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

class ExampleInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.example_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory);

    # Example inventory for testing.
    def example_inventory(self):
        return {
            'group': {
                'hosts': ['192.168.28.71', '192.168.28.72'],
                'vars': {
                    'ansible_ssh_user': 'vagrant',
                    'ansible_ssh_private_key_file':
                        '~/.vagrant.d/insecure_private_key',
                    'example_variable': 'value'
                }
            },
            '_meta': {
                'hostvars': {
                    '192.168.28.71': {
                        'host_specific_var': 'foo'
                    },
                    '192.168.28.72': {
                        'host_specific_var': 'bar'
                    }
                }
            }
        }

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()
# Get the inventory.
ExampleInventory()
sys.exit()

# ---- emel02 edits

# Requests is used to send HTTP GET and POST messages, allows for REST API access.
# installation:
#   sudo apt install python-pip
#   sudo pip install requests
import requests

# Returns input in json format
def to_json(input):
    return json.dumps(input, indent = 2, sort_keys=True)

def ipam_get_token():
    
    ipam_username = "gollenet5"
    ipam_password = "gollenet5"
    
    # Get IPAM API Token
    ipam_request = requests.post(ipam_url_token_request, auth=(ipam_username, ipam_password), timeout=10)
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to ipam token: " + str(output))
    
    return ipam_request.json()['data']['token']

# Depends on having an API token from IPAM
def ipam_get_devices(token):
    
    ipam_request = requests.get(ipam_url_devices, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve devices: " + str(output))
        
    return ipam_request.json()['data']

# Depends on having an API token from IPAM
def ipam_get_device_types(token):
    
    ipam_request = requests.get(ipam_url_device_types, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve device types: " + str(output))
        
    device_types = {}
    # ipam_request returns all device types as a list, we make it a dict where the ID-number is the key
    for device_type in ipam_request.json()['data']:        
        device_types[device_type['tid']] = {}
        device_types[device_type['tid']]['tname'] = device_type['tname']
        device_types[device_type['tid']]['tdescription'] = device_type['tdescription']  
              
    return device_types

# Depends on having an API token from IPAM
# Depends on inventory having devices in it
def ipam_get_device_addresses(token):
    
    # 1. Get devices from IPAM
    ipam_request = requests.get(ipam_url_devices, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve devices: " + str(output))
        
    devices = {}
    for device in ipam_request.json()['data']:
        devices[device['hostname']]       = device
        
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

# Depends on having an API token from IPAM
# Retrieves all subnets in the section, returns a dict where subnetid is key
def ipam_get_section_subnets(token):
    
    section_subnets = {}
    ipam_request = requests.get(ipam_url_section_subnets, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve section subnets: " + str(ipam_request.json()))
    
    # Turns list output into a dict, where subnetId is key
    for subnet in ipam_request.json()['data']:
        section_subnets[subnet['id']] = subnet
        
    return section_subnets

# Depends on having an API token from IPAM
# Returns vrfs as a dict, where id is key    
def ipam_get_vrfs(token):
    
    vrfs = {}
    ipam_request = requests.get(ipam_url_vrf, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve vrf: " + str(ipam_request.json()))
        
    for vrf in ipam_request.json()['data']:
        vrfs[vrf['vrfId']] = vrf
    
    return vrfs
    
# Depends on having an API token from IPAM
# Returns l2domains as a dict, where id is key
def ipam_get_l2domains(token):
    
    l2domains = {}
    ipam_request = requests.get(ipam_url_l2domains, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve l2domains: " + str(ipam_request.json()))
        
    for l2domain in ipam_request.json()['data']:
        
        if l2domain['sections'] != ipam_section:
            continue
            
        l2domains[l2domain['id']] = l2domain
    
    return l2domains
    
def ipam_get_vlans(token):
    
    vlans = {}
    ipam_request = requests.get(ipam_url_vlan, headers={'token': token })
    if ipam_request.json()['code'] != 200:
        sys.exit("Error: Unable to retrieve vlans: " + str(ipam_request.json()))
    
    for vlan in ipam_request.json()['data']:
        
        vlans[vlan['vlanId']] = vlan
    
    return vlans

def build_inventory_hostvars_devices(inventory, devices):

    for host in devices:
        
        inventory['_meta']['hostvars'][host['hostname']] = {}
        inventory['_meta']['hostvars'][host['hostname']]['id']   = host['id']
        inventory['_meta']['hostvars'][host['hostname']]['type'] = host['type']
        if host['ip'] is not None: 
            inventory['_meta']['hostvars'][host['hostname']]['ansible_host'] = host['ip']
    
    return inventory

# By default, only the device type ID is added to the inventory. This function adds the name of the device type as 'tname'.
def build_inventory_hostvars_device_types(inventory):
    
    # We add the name of the device type as "tname" for each host, allows for grouping based on device type name. 
    for host, host_values in inventory['_meta']['hostvars'].iteritems():
        inventory['_meta']['hostvars'][host]['tname'] = device_types[host_values['type']]['tname']
        
    return

# Depends on inventory tname variables being set
def build_inventory_groups(inventory):
        
    # Add devices in their respective device type group:
    for host, host_values in inventory['_meta']['hostvars'].iteritems():
        
        # Create group if not exists:
        if host_values['tname'] not in inventory:
            inventory[host_values['tname']] = {}
            inventory[host_values['tname']]['hosts'] = []
        
        # Add host to group:    
        inventory[host_values['tname']]['hosts'].append(host)
    
    return

# Depends on device_addresses already being generated.
# Depends on section_subnets having all subnets in a dict
# Adds interfaces and their IP-address under inventory->hostvars->device->interface
def build_inventory_hostvars_device_interface(device_addresses):
        
    # Loop through every host
    for host, host_values in device_addresses.iteritems():
                
        # If host does not have a key named interface, create it:
        if 'interface' not in inventory['_meta']['hostvars'][host]:
            inventory['_meta']['hostvars'][host]['interface'] = {}
        
        for interface in host_values:
            
            # We use the subnetId to find the name of the subnet. A bit clunky but necessary.
            interface_name   = section_subnets[interface['subnetId']]['description']
            interface_values = {}
            
            # subnet vars
            interface_values['ipv4'] = interface['ip'] + "/" + section_subnets[interface['subnetId']]['mask']
            
            # address vars
            interface_values['interface']   = interface['custom_interface']
            interface_values['description'] = interface['description']
            interface_values['port']        = interface['custom_port']
            interface_values['state']       = "present"
            
            # VLAN vars:
            if section_subnets[interface['subnetId']]['vlanId'] in vlans:
                interface_values['vlan']           = {}
                interface_values['vlan']['id']     = vlans[ section_subnets[interface['subnetId']]['vlanId'] ]['vlanId']
                interface_values['vlan']['number'] = vlans[ section_subnets[interface['subnetId']]['vlanId'] ]['number']
            
            # VRF vars
            if section_subnets[interface['subnetId']]['vrfId'] in vrfs:
                interface_values['vrf']              = {}
                interface_values['vrf']['id']        = section_subnets[interface['subnetId']]['vrfId']
                interface_values['vrf']['name']      = vrfs[interface_values['vrf']['id']]['name']
                interface_values['vrf']['rd']        = vrfs[interface_values['vrf']['id']]['rd']
                interface_values['vrf']['rt_import'] = vrfs[interface_values['vrf']['id']]['custom_rt_import']
                interface_values['vrf']['rt_export'] = vrfs[interface_values['vrf']['id']]['custom_rt_export']
            
            inventory['_meta']['hostvars'][host]['interface'][interface_name] = interface_values

    return
    
def build_inventory_vrf(vrfs):
    
    inventory['vrf'] = {}
    for vrf_id, vrf_value in vrfs.iteritems():
        inventory['vrf'][vrf_id] = vrf_value
    
    return

# IPAM variables:
# https://phpipam.net/api/api_documentation/
ipam_url_token_request      = "http://ipam.golle.org/api/gollenet5/user/"
ipam_url_devices            = "http://ipam.golle.org/api/gollenet5/devices/"
ipam_url_device_types       = "http://ipam.golle.org/api/gollenet5/tools/device_types/"
ipam_url_section_subnets    = "http://ipam.golle.org/api/gollenet5/sections/5/subnets/"
ipam_url_vrf                = "http://ipam.golle.org/api/gollenet5/vrf/"
ipam_url_l2domains          = "http://ipam.golle.org/api/gollenet5/l2domains/"
ipam_url_vlan               = "http://ipam.golle.org/api/gollenet5/vlan/"
ipam_section                = "5"

# Basic inventory skeleton as supported by ansible: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#tuning-the-external-inventory-script
inventory = {
    '_meta': {
        'hostvars': {        
        }
    },
    'P': {
        'hosts': [
        ],
        'vars': {
            "ansible_connection": "network_cli",
            "ansible_network_os": "ios",
            "ansible_password"  : "admin1",
            "ansible_user"      : "admin1",
            "isis": {
                "metric_crosslink": 15,
                "metric_downlink": 100,
                "metric_uplink": 10,
                "net_area": 49.0007,
                "state": "present"
            },
            'ldp': {
                'state': "present"
            }
        }
    },
    'PE': {
        'hosts': [
        ],
        'vars': {
            "ansible_connection": "network_cli",
            "ansible_network_os": "iosxr",
            "ansible_password"  : "admin1",
            "ansible_user"      : "admin1",
            "isis": {
                "metric_crosslink": 15,
                "metric_downlink": 1000,
                "metric_uplink": 100,
                "net_area": 49.0007,
                "state": "present"
            },
            'ldp': {
                'state': "present"
            }
        }
    },
    'PEER': {
        'hosts': [
        ],
        'vars': {
            "ansible_connection": "netconf",
            "ansible_network_os": "junos",
            "ansible_password"  : "admin1",
            "ansible_user"      : "admin1",
            "isis": {
                "metric_crosslink": 15,
                "metric_downlink": 1000,
                "metric_uplink": 100,
                "net_area": 49.0007,
                "state": "present"
            },
            'ldp': {
                'state': "present"
            }
        }
    },
    'ME': {
        'hosts': [
        ],
        'vars': {
            "ansible_connection"     : "network_cli",
            "ansible_network_os"     : "sros",
            "ansible_password"       : "admin",
            "ansible_user"           : "admin",
            "ansible_ssh_common_args": '-oKexAlgorithms=diffie-hellman-group1-sha1',
            "isis": {
                "metric_crosslink": 10,
                "metric_downlink": 10,
                "metric_uplink": 1000,
                "net_area": 49.0007,
                "state": "present"
            },
            'ldp': {
                'state': "present"
            }
        }
    }
}

def main():

    # Get data from IPAM:
    token            = ipam_get_token()
    # devices          = ipam_get_devices(token)
    device_types     = ipam_get_device_types(token)
    vrfs             = ipam_get_vrfs(token)
    vlans            = ipam_get_vlans(token)
    section_subnets  = ipam_get_section_subnets(token)
    devices, device_addresses = ipam_get_device_addresses(token)

    # Get devices from IPAM, add to inventory
    build_inventory_vrf(vrfs)
    # l2domains   = ipam_get_l2domains()
    build_inventory_hostvars_devices(inventory, devices)

    # Get device types, add as groups in inventory
    inventory = build_inventory_hostvars_device_types(inventory, devices)
    build_inventory_groups(inventory)

    # Get device addresses, add as interfaces under device hostvars in inventory
    #print(json.dumps(device_addresses, indent = 2, sort_keys=True))

    build_inventory_hostvars_device_interface(device_addresses)

    print to_json(inventory)

main()