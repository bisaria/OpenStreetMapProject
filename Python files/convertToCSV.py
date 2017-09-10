#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for parsing the elements in the OSM XML file, transforming them from document 
format to tabular format for converting into csv files. 

The process for this transformation is as follows:
- Iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the 
  correct format
- Write each data structure to the appropriate .csv files

## Shape Element Function
Author: Rupa Bisaria

The function takes as input an iterparse Element object and returns a dictionary in 
a specific format.

### When the element top level tag is "node":
The dictionary returned have the format {"node": .., "node_tags": ...}

The "node" field holds a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset

The "node_tags" field holds a list of dictionaries, one per secondary tag. Each dictionary 
have the following fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after 
    the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.


- If a node has no secondary tags then the "node_tags" field just contains an empty list.

### When the element top level tag is "way":
The dictionary have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

The "way" field hold a dictionary of the following top level way attributes:
- id
- user
- uid
- version
- timestamp
- changeset

The "way_tags" field hold a list of dictionaries, same as "node_tags".

"way_nodes" hold a list of dictionaries, one for each nd child tag.  Each dictionary have the 
fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within
            the way element

## Get Element Function
Provided by Upacity

## Validate Element Function
Provided by Upacity

## Process Map Function
Provided by Upacity

"""


import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema
from clean_osm import cleanOSM

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
ARABICKEY = re.compile(r'((\:ar)|\b(ar))$$')

mapping_street_name = { 
            "St.": "Street",
            "St": "Street",
            "street": "Street",
            "Rd.": "Road",
            "Rd": "Road",
            "road": "Road"
            }
expected_street_name = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Slipway", "Way","Walk", "Highway", "Roundabout","Exit",
            "Link","Track","Corniche"]
mapping_city = {
     'A Ain': 'Al Ain',
     'Al AIn':'Al Ain',
     'sharja': 'Sharjah',
     'Duba': 'Dubai',
     'Mussafah M 45- Abu Dhabi': 'Mussafah',
     'Musaffah Industrial Area': 'Mussafah',
     'Duabi': 'Dubai',
     'Al Safa 1': 'Dubai',
     'Al Safa 2': 'Dubai',
     'Jumeirah 1': 'Dubai',
     'Jumeirah 3': 'Dubai',
     'Jumeirah Village Circle': 'Dubai',
     'Sjarjah':'Sharjah',
     'samha': 'Al Samha',
     'JVT': 'Dubai',        
     'Al Quoz Industrial Area 2':'Dubai',
     'Jumeirah Lakes Towers':'Dubai',
     'JLT Cluster Y':'Dubai',
     'Karama': 'Al Karama'   
}

expected_cities = ['Abu Dhabi','Dubai','Dibba Al-Fujairah','Al Ain','Fujairah','Sharjah', 'Al Karama','Al Nud',
                   'Mussafah','Ajman','Saadiyat Island','Al Reem Island','Khalifa City A','Khalifa City B',
                   'Khalifa City C','Al Towayya','Hatta','Al Khan','Al Maryah Island','Muhammad Bin Zayed City',
                   'Al Karama','Al Samha', 'Umm Al Quwain','Ras al Khaimah','Yas Island','Hatta']

mapping_surface = {'running surface': 'running_surface',
                   'Elevated': 'elevated',
                   'paving_stoness': 'paving_stones',
                   'pavin':'paving',
                   'paving stones':'paving_stones',
                   'unpaveds':'unpaved',
                   'unpaved`':'unpaved', 
                   'paving`': 'paving', 
                   'asphalt`':'asphalt'}

mapping_building = {
    'Airport_terminal': 'terminal',
    'Office_And_entrance': 'commercial', 
    'MAJ Building': 'yes', 
    'Complex_A_&_B': 'yes',
    'yes;mosque': 'mosque',
    'Tourist_Exhibition': 'yes',
    'Gate 3':'yes',
    'Offices': 'commercial',
    'office': 'commercial'
}
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


class UnicodeDictWriter(csv.DictWriter, object):
        """Extend csv.DictWriter to handle Unicode input"""

        def writerow(self, row):
            super(UnicodeDictWriter, self).writerow({
                k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
            })

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)


class ConvertToCSV(object):
    
    def __init__(self, osm_file, validate):
        '''
        Initializes an auditOSM instance
        
        osm_file: OSM file for cleaning and converting to csv    
        
        validate: Boolean for validation requirement
                
        '''
        self.osm_file = osm_file
        self.validate = validate
          
     
    def shape_element(self, element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                      problem_chars=PROBLEMCHARS, arabic_chars = ARABICKEY, default_tag_type='regular'):
        """Clean and shape node or way XML element to Python dict"""

        node_attribs = {}
        way_attribs = {}
        way_nodes = []
        tags = []  

        if element.tag == 'node':
            
            for i in range(len(node_attr_fields)):
                node_attribs[node_attr_fields[i]] = element.get(node_attr_fields[i])
                
            for tag in element.iter("tag"):
                if re.search(problem_chars, tag.attrib['k']):
                    continue
                if re.search(arabic_chars, tag.attrib['k']):
                    continue

                tag_attrib = {}
                tag_attrib['id'] = element.get('id')

                # Clean street names
                if (tag.attrib['k'] == "addr:street"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_street_name, expected_street_name).clean_street_name() 

                # Clean building
                elif (tag.attrib['k'] == "building"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_building).clean_value()

                # Clean surface
                elif (tag.attrib['k'] == "surface"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_surface).clean_value()
    
                # Clean oneway
                elif (tag.attrib['k'] == "oneway"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v']).set_to_none()
    
                # Clean city names
                elif (tag.attrib['k'] == "addr:city"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'],  mapping_city, expected_cities).clean_city_name()

                else:
                    tag_attrib['value'] = tag.attrib['v']
                    
                if re.search(LOWER_COLON, tag.attrib['k']):
                    tag_attrib['type'], tag_attrib['key'] =  tag.attrib['k'].split(':',1)
                else:
                    tag_attrib['key'] =  tag.attrib['k']
                    tag_attrib['type'] = default_tag_type
                                 
                tags.append(tag_attrib)
                
            return {'node': node_attribs, 'node_tags': tags}
        
        elif element.tag == 'way':
            
            for i in range(len(way_attr_fields)):
                way_attribs[way_attr_fields[i]] = element.get(way_attr_fields[i])

            nd_index = 0
            for nd in element.iter("nd"):
                nd_attrib = {}
                nd_attrib['id'] = element.get('id')
                nd_attrib['node_id'] = nd.attrib['ref']
                nd_attrib['position'] = nd_index
                nd_index += 1
                way_nodes.append(nd_attrib)

            for tag in element.iter("tag"):
                if re.search(PROBLEMCHARS, tag.attrib['k']):
                    continue
                if re.search(arabic_chars, tag.attrib['k']):
                    continue
                    
                tag_attrib = {}
                tag_attrib['id'] = element.get('id')
                
                # Clean street names
                if (tag.attrib['k'] == "addr:street"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_street_name, expected_street_name).clean_street_name() 

                # Clean building
                elif (tag.attrib['k'] == "building"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_building).clean_value()

                # Clean surface
                elif (tag.attrib['k'] == "surface"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'], mapping_surface).clean_value()
    
                # Clean oneway
                elif (tag.attrib['k'] == "oneway"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v']).set_to_none()
    
                # Clean city names
                elif (tag.attrib['k'] == "addr:city"):
                    tag_attrib['value'] = cleanOSM(tag.attrib['v'],  mapping_city, expected_cities).clean_city_name()
                
                else:
                    tag_attrib['value'] = tag.attrib['v']
                    
                if re.search(LOWER_COLON, tag.attrib['k']):
                    tag_attrib['type'], tag_attrib['key'] =  tag.attrib['k'].split(':',1)
                else:
                    tag_attrib['key'] =  tag.attrib['k']
                    tag_attrib['type'] = default_tag_type
                                  
                tags.append(tag_attrib)
                
            return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

    
    def get_element(self, tags=('node', 'way', 'relation')):
        """Yield element if it is the right type of tag"""

        context = ET.iterparse(self.osm_file, events=('start', 'end'))
        _, root = next(context)
        for event, elem in context:
            if event == 'end' and elem.tag in tags:
                yield elem
                root.clear()


    def validate_element(self, element, validator, schema=SCHEMA):
        """Raise ValidationError if element does not match schema"""
        if validator.validate(element, schema) is not True:
            field, errors = next(validator.errors.iteritems())
            message_string = "\nElement of type '{0}' has the following errors:\n{1}"
            error_string = pprint.pformat(errors)

            raise Exception(message_string.format(field, error_string))
   
    
    def process_map(self):
        """Iteratively process each XML element and write to csv(s)"""

        with codecs.open(NODES_PATH, 'w') as nodes_file, \
            codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
            codecs.open(WAYS_PATH, 'w') as ways_file, \
            codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
            codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

            nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
            node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
            ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
            way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
            way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

            nodes_writer.writeheader()
            node_tags_writer.writeheader()
            ways_writer.writeheader()
            way_nodes_writer.writeheader()
            way_tags_writer.writeheader()

            validator = cerberus.Validator()

            for element in self.get_element(tags=('node', 'way')):
                el = self.shape_element(element)
                if el:
                    if self.validate is True:
                        self.validate_element(el, validator)

                    if element.tag == 'node':
                        nodes_writer.writerow(el['node'])
                        node_tags_writer.writerows(el['node_tags'])
                    elif element.tag == 'way':
                        ways_writer.writerow(el['way'])
                        way_nodes_writer.writerows(el['way_nodes'])
                        way_tags_writer.writerows(el['way_tags'])
                        