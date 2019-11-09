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
        
        self.devices          = self.get_devices()
        self.device_addresses = self.get_device_addresses()
        self.device_types = self.get_device_types()
        self.section_subnets = self.get_section_subnets()
        self.vrfs = self.get_vrfs()
        self.vlans = self.get_vlans()
    
    def send_request_get(self, url):
        
        """ Returns data returned from GET request to PHPIPAM API: 
        GET is used to retrieve the IPAM records as specified in the URL
        
        https://phpipam.net/api/api_documentation/ 
        """
        
        r = requests.get(url, headers={'token': self.token })
        if r.json()['code'] != 200:
            sys.exit("Error: Unable to retrieve " + url + ": " + str(r.json()))
        return r.json()['data']
    
    def send_request_patch(self, url, payload):
        
        """ PATCH is used to update existing PHPIPAM IPAM records """
        
        r = requests.patch(url, payload, headers={'token': self.token })
        if r.json()['code'] != 200:
            sys.exit("Error: Unable to update address: " + str(r.json()))
        return r.json()['data']
        
    def get_devices(self):
        
        """ Return list of all devices """
        
        url = "http://ipam.golle.org/api/gollenet5/devices/"
        return self.send_request_get(url)
            
    def get_device_types(self):
        
        """ Return dict of all device types, indexed by type ID """
        
        url = "http://ipam.golle.org/api/gollenet5/tools/device_types/" 
        device_types = {}
        
        for device_type in self.send_request_get(url):        
            device_types[device_type['tid']] = {}
            device_types[device_type['tid']]['tname'] = device_type['tname']
            device_types[device_type['tid']]['tdescription'] = device_type['tdescription']  
         
        return device_types
        
    def get_device_addresses(self):
        
        """ Loops through all devices in self.devices and retrieves their addresses as a list.
        Returns all lists in a dict, indexed by device hostname.
        """
        
        device_addresses = {}
        for device in self.devices:
            url = "http://ipam.golle.org/api/gollenet5/devices/{}/addresses/".format(device['id'])
            device_addresses[device['hostname']] = self.send_request_get(url)

        return device_addresses

    def get_section_subnets(self):
        
        """ Return dict of all subnets in IPAM, indexed by subnet id """
        
        url = "http://ipam.golle.org/api/gollenet5/sections/5/subnets/"
        section_subnets = {}
        for subnet in self.send_request_get(url):
            section_subnets[subnet['id']] = subnet
            
        return section_subnets

    def get_vrfs(self):
        
        """ Return dict of all VRFs in IPAM, indexed by vrfId """
        
        url = "http://ipam.golle.org/api/gollenet5/vrf/"
        vrfs = {}            
        for vrf in self.send_request_get(url):
            vrfs[vrf['vrfId']] = vrf
        
        return vrfs
        
    def get_vlans(self):
        
        """ Return dict of all vlans in IPAM, indexed by vlanId """
        
        url = "http://ipam.golle.org/api/gollenet5/vlan/"
        vlans = {}
        for vlan in self.send_request_get(url):
            vlans[vlan['vlanId']] = vlan
        
        return vlans

# ipam = c_phpipam()
# print to_json(ipam.vlans)
        
class c_inventory:
    
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
        #self.inventory = {'_meta': {'hostvars': {}}}
        self.inventory = {
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
        
        # Get data from IPAM to populate our inventory
        self.ipam = c_phpipam()
        
        self.inventory['_meta']['hostvars'] = self.inventory_hostvars()
        self.inventory_add_devices_to_groups()
        self.inventory_groupvars()
                
        print (to_json(self.inventory))
    
    def get_cli_args(self):
        
        """ Return the command line args passed to the script """
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        return parser.parse_args()
    
    # Return all host variables as learned from IPAM:
    def inventory_hostvars(self):
        
        """ Returns hostvars as a dict where each key is the device hostname """
        
        hostvars = {}
        for device in self.ipam.devices:
            hostvars[device['hostname']] = {}
            hostvars[device['hostname']]['id']      = device['id']
            hostvars[device['hostname']]['type']    = device['type']
            
            # If a device IP is manually set in IPAM, use it over resolving hostname in DNS:
            if device['ip'] is not None:
                hostvars[device['hostname']]['ansible_host'] = device['ip']
        
        return hostvars
    
    def inventory_groupvars(self):
        
        groupvars = {
            'P': {
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
        
        sys.exit(groupvars['P'])
        
            
            
    
    def inventory_add_devices_to_groups(self):
        
        """ Dynamically adds hosts to their respective to inventory groups. 
        If possible, find a way to return a value that can be merged into self.inventory.
        Right now self.inventory is being edited directly, which is not optimal.
        """
        
        for device in self.ipam.devices:
            
            group_id    = device['type']
            group_name  = self.ipam.device_types[group_id]['tname']
            
            # Create group if doesn't exist:
            if group_name not in self.inventory:
                self.inventory[group_name] = {}
                self.inventory[group_name]['hosts'] = []
            
            # Add device to group: (does not work)
            self.inventory[group_name]['hosts'].append(device['hostname'])
        
            
    def inventory_hostvars_interfaces(self):
        
        # Loop through every device
        for device, device_values in self.device_addresses.items():
                  
            # If device does not have a key named interface, create it:
            if 'interface' not in inventory['_meta']['hostvars'][device]:
                inventory['_meta']['hostvars'][device]['interface'] = {}
          
            for interface in device_values:
              
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
              
                inventory['_meta']['hostvars'][device]['interface'][interface_name] = interface_values

        print(inventory)        

# Script "starts" here:
c_inventory()


