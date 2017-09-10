#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code for auditing OSM files 
Author: Rupa Bisaria

Audits any 'k' attribute for a 'tag' element of the elements 'node' and 
'way' from an OSM file

"""

import xml.etree.cElementTree as ET
import re
from collections import defaultdict


class auditOSM(object):
    
    def __init__(self, osm_file, key, expected_values = []):
        '''
        Initializes an auditOSM instance
        
        osm_file: OSM file for auditing    
        
        key: key attribute of an element for audit
        
        expected_values: list of expected values for the given key
        
        '''
        self.osm_file = osm_file
        self.key = key
        self.expected = expected_values
        
     
    def is_key_match(self, elem):
        '''
        Checks if the 'k' attribute of an element is same as the 
        given key
        
        elem: element whose attribute is to be checked
        
        @return: Bool if key matches the attribute 'k'
        
        '''
        return (elem.attrib['k'] == self.key)
    

    def audit_key(self):
        '''
        Audits the given key against a list of expected values. 
        
        For all 'tag' elements of the elements 'node' and 'way', if the 
        attribute 'k' matches the given key, then checks for it's value 
        in the list of expected values. If the value is not in the list 
        it is added to a set of unique values.
        
        @return: list of unique values for a given key
        '''
        osmfile = open(self.osm_file, "r")
        unique_values = set()
        for event, elem in ET.iterparse(self.osm_file, events=("start",)):
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if self.is_key_match(tag):
                        if tag.attrib['v'] not in self.expected:
                            unique_values.add(tag.attrib['v'])               

        osmfile.close()
        return list(unique_values)
   
    
    def audit_street_type(self, street_types, street_name):
        '''
        Looks for street type in the street name using a regex. If the street
        type is not in the dictionary of expected street types, adds it to the
        default dictionary passed from audit_street function
        
        street_types: default dictionary of street types with key as street 
                        type and value as street names
                        
        street_name: String value from the tag with key = 'addr:street'
        
        '''
        street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
        m = street_type_re.search(street_name)
        if m:
            street_type = m.group()
            if street_type not in self.expected:
                street_types[street_type].add(street_name)

    
    def audit_street(self):
        '''
        Opens the OSM file and for every 'tag' element for 'node' or 'way' tags, looks
        for 'addr:street' key. Value of the key is the street name, which is searched 
        using a regex for the street type. If the street type is not in a list of expected
        street types, the street name is added to a default dictionary.
         
        @return: default dictionary of street types with key as street 
                        type and value as street names
        '''     
        
        osmfile = open(self.osm_file, "r")
        street_types = defaultdict(set)
        
        for event, elem in ET.iterparse(osmfile, events=("start",)):
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if self.is_key_match(tag):
                        self.audit_street_type(street_types, tag.attrib['v'])
        osmfile.close()
        return street_types    
    
    
    
    