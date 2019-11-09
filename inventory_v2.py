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
# installation:
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
        ipam_request = requests.post(ipam_url_token_request, auth=(ipam_username, ipam_password), timeout=10)
        if ipam_request.json()['code'] != 200:
            sys.exit("Error: Unable to ipam token: " + str(output))
        
        self.token = ipam_request.json()['data']['token']
        
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
        for host, host_values in devices.iteritems():          
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
        
        # Minimum accepted inventory by ansible:
        self.inventory = {'_meta': {'hostvars': {'TEST': {}}}}
        
        # Read CLI args:
        self.read_cli_args()
        
        if self.args.list:
            print to_json(self.inventory)
        elif self.args.host:
            print "You wanted host " + self.args.host
        else:
            sys.exit("No list or host argument given, add -h for help menu.")
    
    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

c_inventory()




# ---- emel02 edits

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

# main()


### Script template:
# class ExampleInventory(object):

#     def __init__(self):
#         self.inventory = {}
#         self.read_cli_args()

#         # Called with `--list`.
#         if self.args.list:
#             self.inventory = self.example_inventory()
#         # Called with `--host [hostname]`.
#         elif self.args.host:
#             # Not implemented, since we return _meta info `--list`.
#             self.inventory = self.empty_inventory()
#         # If no groups or vars are present, return an empty inventory.
#         else:
#             self.inventory = self.empty_inventory()

#         print json.dumps(self.inventory);

#     # Example inventory for testing.
#     def example_inventory(self):
#         return {
#             'group': {
#                 'hosts': ['192.168.28.71', '192.168.28.72'],
#                 'vars': {
#                     'ansible_ssh_user': 'vagrant',
#                     'ansible_ssh_private_key_file':
#                         '~/.vagrant.d/insecure_private_key',
#                     'example_variable': 'value'
#                 }
#             },
#             '_meta': {
#                 'hostvars': {
#                     '192.168.28.71': {
#                         'host_specific_var': 'foo'
#                     },
#                     '192.168.28.72': {
#                         'host_specific_var': 'bar'
#                     }
#                 }
#             }
#         }

#     # Empty inventory for testing.
#     def empty_inventory(self):
#         return {'_meta': {'hostvars': {}}}

#     # Read the command line args passed to the script.
#     def read_cli_args(self):
#         parser = argparse.ArgumentParser()
#         parser.add_argument('--list', action = 'store_true')
#         parser.add_argument('--host', action = 'store')
#         self.args = parser.parse_args()
# # Get the inventory.
# ExampleInventory()