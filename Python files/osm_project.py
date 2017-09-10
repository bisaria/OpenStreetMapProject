#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project code for working on the osm file 
Author: Rupa Bisaria

This script loads, audits and cleans the osm file for the project. The clean data
is finally converted to csv and saved as dabase tables in sqlite. Finally, the data
is queried to answer few questions about the data.

Following are the tentative approach adopted in the process:

1. Sample files of varying sizes from the full osm file were created for working 
on the scripts for audit and cleaning. Full file was used finally once the script 
worked without any error. 

2. Since the project required to work only on 'tag' element of 'node' and 'way' 
tags, a sorted list of it's 'k' attributes in descending order of their frequency
of occurence was created. Few attributes from the top ten in the list were selected 
for audit and cleaning purpose.

3. General approach for each auditing task was to, either start with an expected 
list of values if possible, or else, audit the data without a expected list and 
create a list by comparing the existing values with the expected values as per wiki.

4. In case of later, a second round of audit was done with expected list in tow, 
thereby getting a list of unexpected, dirty entries.

5. These dirty values were then cleaned using various techniques, starting from 
mapping to correct values, to using regex to correct the errors wherever possible.

6. Quite a few errors were difficult to verify and were either set to 'None' or 
left as is, on a case to case basis.

7. Finally shape function was used to shape the clean data in the required format 
for converting it to csv file

8. Thus formatted data structure was finally converted to csv files for further
analysis.

9. These csv files were used for creating the database tables in sqlite using pre
specified schema.

10. Databse thus created was queried to answer some specific questions.

"""

# Required python imports
import pprint
import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import pandas as pd
import os
import matplotlib.pyplot as plt

# Custom python files for the project
from osm_file import OSMFile  # OSM file handling script
from audit_osm import auditOSM # Auditing script
from clean_osm import cleanOSM # Cleaning script
from convertToCSV import ConvertToCSV # Script to shape the data and save to csv
from sql_db import dbSQL # Script for sqlite database

# OSM file names for files from Dubai-Abu Dhabi region
OSM_FILE = "dubai_abu-dhabi.osm"  # Full data file 
SAMPLE_FILE = "dubai_abu-dhabi_sample.osm" # Sample data file


NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# Create sample file and save to the directory
k = 60  # for creating the submitted sample file
OSMFile(OSM_FILE, SAMPLE_FILE, k).create_sample_file()

# Get file size in MB
os.path.getsize(OSM_FILE) >> 20
# 503L

# Count all the tags in the osm fil
def count_tags(filename):
        # Create a dictionary of tags
        tag_dict = {}
        # Iteratively parse through the data and add all elements in the dictionary
        for event, elem in ET.iterparse(filename):
            if elem.tag not in tag_dict.keys():
                tag_dict[elem.tag] = 1
            else:
                tag_dict[elem.tag] += 1
        return tag_dict
    
tags = count_tags(OSM_FILE)
# pprint.pprint(tags)
# {'bounds': 1,
# 'member': 13442,
# 'nd': 2892316,
# 'node': 2431529,
# 'osm': 1,
# 'relation': 4072,
# 'tag': 1055634,
# 'way': 324346}
    
# Function to get the count of all 'k' attributes of 'tag' element and 
# sort them by frequency of their occurence
def get_keys_count(filename):    
    all_keys = defaultdict(set)
    sorted_keys = []
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] in all_keys.keys():
                    all_keys[tag.attrib['k']] += 1
                else:
                    all_keys[tag.attrib['k']] = 1
                    
    # sort by value in descending order
    for w in sorted(all_keys, key=all_keys.get, reverse=True):
        sorted_keys.append((w, all_keys[w]))
        
    return sorted_keys

# Count 'tag' elements 'k' attribute for the osm file
all_keys = get_keys_count(OSM_FILE)

# Get number of unique keys
print len(all_keys)
# 862

# Get top 20 keys used 
for key in all_keys[0:20]:
    print key   
#('highway', 183227)
#('source', 91029)
#('building', 88605)
#('name', 77374)
#('surface', 73926)
#('oneway', 69162)
#('addr:street', 52428)
#('lanes', 35757)
#('name:ar', 31158)
#('addr:housenumber', 29740)
#('amenity', 23222)
#('shop', 20169)
#('addr:city', 19997)
#('power', 17391)
#('addr:city:ar', 16049)
#('addr:street:ar', 15889)
#('landuse', 14473)
#('barrier', 13353)
#('maxspeed', 10581)
#('natural', 10299)

# Few key attributes from top 20 most frequently occuring ones are chosen for auditing and cleaning.

##**************************##
#      Audit building       ##
##**************************##

# Audit building and get a list of all building types
all_building = auditOSM(OSM_FILE, 'building').audit_key()

# cleaned expected_building list
expected_building = ['bridge',
 'shed',
 'industrial',
 'apartments',
 'terminal',
 'house',
 'parking',
 'nursery',
 'college',
 'terrace',
 'church',
 'yes',
 'detached',
 'hangar',
 'palace',
 'service',
 'no',
 'residential',
 'hospital',
 'mosque',
 'dormitory',
 'stable',
 'warehouse',
 'barn',
 'public',
 'cabin',
 'manufacture',
 'entrance',
 'transportation',
 'government',
 'kiosk',
 'train_station',
 'hotel',
 'commercial',
 'kindergarten',
 'supermarket',
 'hut',
 'garages',
 'construction',
 'grandstand',
 'golf_club',
 'canopy',
 'pagoda',
 'school',
 'semidetached_house',
 'university',
 'collapsed',
 'roof',
 'garage',
 'security_tower',
 'bunker',
 'tower',
 'retail',
 'storage_tank',
 'greenhouse']

# Audit against the expected values to get a list of dirty entries
dirty_building_types = auditOSM(OSM_FILE, 'building', expected_building).audit_key()
# print dirty_building_types
# ['Office_And_entrance', 'office', 'Airport_terminal', 'Gate 3', 'Tourist_Exhibition', 'Offices', 'yes;mosque', 'MAJ Building', 'Complex_A_&_B']

# map wrong entries to clean values
#https://wiki.openstreetmap.org/wiki/Map_Features#Building  
mapping_building = {
    'Airport_terminal': 'terminal',
    'Office_And_entrance': 'commercial', # wiki: Use building=commercial with office=* to describe the type of office
    'MAJ Building': 'yes', # wiki: Use this value where it is not possible to determine a more specific value. 
    'Complex_A_&_B': 'yes',
    'yes;mosque': 'mosque',
    'Tourist_Exhibition': 'yes',
    'Gate 3':'yes',
    'Offices': 'commercial',
    'office': 'commercial'
}

##**************************##
#      Clean building       ##
##**************************##

for building in auditOSM(OSM_FILE, 'building').audit_key():
    print cleanOSM(building, mapping_building).clean_value()

##**************************##
#      Audit surface       ##
##**************************##

all_surfaces = auditOSM(OSM_FILE, 'surface').audit_key()

# cleaned expected_surface list
expected_surface = ['astroturf',
 'asphalt',
 'bricks',
 'wood',
 'hard',
 'pebblestone',
 'earth',
 'paved2',
 'compacted',
 'ground',
 'asphalt_no_1',
 'unpaved',
 'mud',
 'unpaved;gravel',
 'gravel',
 'concrete:lanes',
 'paved',
 'sand;stone;gravel',
 'artificial_turf',
 'dirt',
 'cobblestone',
 'unpaved;asphalt',
 'tartan',
 'paving_stones',
 'bing',
 'metal',
 'rocks',
 'sett',
 'concrete',
 'sand',
 'dirt/sand',
 'paving_stone',
 'grass']

# Get dirty surface entries by auditing against expected values
dirty_surface_types = auditOSM(OSM_FILE, 'surface', expected_surface).audit_key()
# print dirty_surface_types
# ['unpaveds', 'running surface', 'asphalt`', 'Elevated', 'unpaved`', 'paving stones', 'paving_stoness', 'pavin', 'paving`']


# map dirty values to clean values
mapping_surface = {'running surface': 'running_surface',
                   'Elevated': 'elevated',
                   'paving_stoness': 'paving_stones',
                   'pavin':'paving',
                   'paving stones':'paving_stones',
                   'unpaveds':'unpaved',
                   'unpaved`':'unpaved', 
                   'paving`': 'paving', 
                   'asphalt`':'asphalt'}

##**************************##
#      Clean surface        ##
##**************************##

for dirty_surface in auditOSM(OSM_FILE, 'surface').audit_key():
    print cleanOSM(dirty_surface, mapping_surface).clean_value()
    
##**************************##
#      Audit oneway         ##
##**************************##

# get expected values of oneway from the wiki
# Refer: https://wiki.openstreetmap.org/wiki/Key:oneway
expected_oneway = ['yes','no','-1','reversible','alternating']

# Find dirty values bu auditing against expected values
dirty_oneway_types = auditOSM(OSM_FILE, 'oneway', expected_oneway).audit_key()
# print dirty_oneway_types
# ['Street 43', 'tertiary']

# Count number of tags with wrong entries
count = 0
for event, elem in ET.iterparse(OSM_FILE, events=("start",)):
    if elem.tag == "node" or elem.tag == "way":
        for tag in elem.iter("tag"):
            if tag.attrib['k'] == 'oneway':
                if tag.attrib['v'] in dirty_oneway_types:
                    count += 1
                    
                
# print count
# 6

##**************************##
#      Clean oneway         ##
##**************************##

for dirty_oneway in auditOSM(OSM_FILE, 'oneway').audit_key():
    print cleanOSM(dirty_oneway).set_to_none()
    
##**************************##
#      Audit addr:city      ##
##**************************##

# List of few major cities in the region
expected_cities = ['Abu Dhabi','Dubai','Dibba Al-Fujairah','Al Ain','Fujairah','Sharjah', 'Al Karama','Al Nud',
                   'Mussafah','Ajman','Saadiyat Island','Al Reem Island','Khalifa City A','Khalifa City B',
                   'Khalifa City C','Al Towayya','Hatta','Al Khan','Al Maryah Island','Muhammad Bin Zayed City',
                   'Al Karama','Al Samha', 'Umm Al Quwain','Ras al Khaimah','Yas Island','Hatta']


# Audit city entry against expected_cities list and extract those which do not feature in the list
all_cities = auditOSM(OSM_FILE, 'addr:city', expected_cities).audit_key()

# ap some of the spelling mistakes etc. to the clean values
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

##**************************##
#      Clean addr:city      ##
##**************************##

for city in all_cities:
    print city, ' => ', cleanOSM(city, mapping_city, expected_cities).clean_city_name()

##**************************##
#   Audit arabic entries    ##
##**************************##

## addr:street:ar
for street in auditOSM(OSM_FILE, 'addr:street:ar').audit_key()[0:10]:
    print street
    
## name:ar
for name in auditOSM(OSM_FILE, 'name:ar').audit_key()[0:10]:
    print name    
    
# All such tags to be ignored.

##**************************##
#     Audit addr:street     ##
##**************************##

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Slipway", "Way","Walk", "Highway", "Roundabout","Exit",
            "Link","Track","Corniche"]

# Audit with the expected list of street types and find types not in the list
street_types = auditOSM(OSM_FILE,'addr:street', expected).audit_street()
pprint.pprint(dict(street_types))

# Mapping dictionary for correcting the discrepancies in the street name
mapping = { "St.": "Street",
            "St": "Street",
            "st.": "Street",
            "st": "Street",
            "sweet": "Street",
            "street": "Street",
            "Rd.": "Road",
            "Rd": "Road",
           "rd": "Road",
           "rd.": "Road",
            "road": "Road",
            "Roud": "Road",
            "Streetrr": "Street",
            "Street`": "Street",
            "Street3": "Street 3",
            "Street1": "Street 1",
            "ROAD": "Road",
           "Streeet": "Street",
           "Steet": "Street",
           "Sreet": "Street",
           "STREET": "Street",
           "Rounadabout":"Roundabout",
           "blvd":"Boulevard",
           "exit":"Exit",
           "track":"Track",
           "Atreet":"Street",
           "Road:":"Road",
           "StreetAl": "Street, Al",
           "corniche":"Corniche"
            }

##**************************##
#     Clean addr:street     ##
##**************************##
for _, ways in street_types.iteritems():
    for name in ways:
        print name, "=>", cleanOSM(name, mapping, expected).clean_street_name()
        
##**************************##
#     Convert to csv        ##
##**************************##

ConvertToCSV(OSM_FILE, validate=True).process_map()

##**************************##
#  Create database tables   ##
##**************************##

nodes_schema = """CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
)"""

nodes_tags_schema = """CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
)"""

ways_schema = """CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
)"""

ways_tags_schema = """CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
)"""

ways_nodes_schema = """CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
)"""

db = dbSQL()

db.create_table('nodes', nodes_schema)
db.insert_data('nodes', NODES_PATH)

db.create_table('nodes_tags', nodes_tags_schema)
db.insert_data('nodes_tags', NODE_TAGS_PATH)

db.create_table('ways', ways_schema)
db.insert_data('ways', WAYS_PATH)

db.create_table('ways_tags', ways_tags_schema)
db.insert_data('ways_tags', WAY_TAGS_PATH)

db.create_table('ways_nodes', ways_nodes_schema)
db.insert_data('ways_nodes', WAY_NODES_PATH)

db.close_connection()

##**************************##
#      Query database       ##
##**************************##

conn = sqlite3.connect('osm.db', timeout=10)
c = conn.cursor()

# Number of unique user
cursor = conn.execute("SELECT COUNT(DISTINCT(uid)) from nodes")
print "Unique uid count  = ", cursor.fetchone()[0]
# Unique uid count  =  2450

# Number of nodes
cursor = conn.execute("SELECT COUNT(*) FROM nodes")
print "Node count  = ", cursor.fetchone()[0]
# Node count  =  2431529

# Number of ways
cursor = conn.execute("SELECT COUNT(*) FROM ways")
print "Way count  = ", cursor.fetchone()
# Way count  =  (324346,)

# Top ten users
df = pd.read_sql_query("SELECT user, uid, COUNT(user) as num FROM nodes \
                    GROUP BY uid ORDER BY num DESC;", conn)
df[0:10]

# Top ten contributions by most active user
df = pd.read_sql_query("SELECT ways_tags.key as key, COUNT(ways_tags.key) as num FROM ways_tags \
                    JOIN ways ON ways_tags.id = ways.id \
                    WHERE ways.uid = '561234' \
                    GROUP BY ways_tags.key ORDER BY num DESC;", conn)
df[0:10]

# Way with maximum number of nodes
cursor = conn.execute("SELECT A.id, MAX(A.node_count) FROM (SELECT id, COUNT(node_id) AS node_count FROM ways_nodes \
                    GROUP BY id) A")
print "(Tag Id, Node Count)  = ", cursor.fetchall()
# Node count  =  [(404074917, 1960)]

# All way tags with number of nodes more than 1000
cursor = conn.execute("SELECT A.id, A.node_count FROM (SELECT id, COUNT(node_id) AS node_count FROM ways_nodes \
                    GROUP BY id) A WHERE A.node_count > 1000")
print "(Tag Id, Node Count) = ", cursor.fetchall()
# (Tag Id, Node Count) =  [(170139278, 1086), (171171012, 1075), (194470882, 1094), (205958924, 1226), (216720271, 1628), (393225171, 1408), (393249907, 1434), (393254003, 1180), (393420807, 1266), (402883870, 1592), (402884861, 1450), (404074917, 1960), (404089376, 1469), (440574399, 1062), (440574403, 1133), (440574568, 1524), (440574586, 1264)]

# Count the number of keys for each of these ids
cursor = conn.execute("SELECT COUNT(ways_tags.key) FROM ways_tags \
                    WHERE id IN (SELECT A.id FROM (SELECT id, COUNT(node_id) AS node_count FROM ways_nodes \
                    GROUP BY id) A WHERE A.node_count > 1000) \
                    GROUP BY id")
print "Associated keys and values  = ", cursor.fetchall()
# Associated keys and values  =  [(10,), (2,), (2,), (2,), (2,), (2,), (1,), (1,), (3,), (3,), (3,), (3,)]

## What is the feature here??
cursor = conn.execute("SELECT key, value FROM ways_tags \
                        WHERE id = '402884861'")
print "Associated keys and values  = ", cursor.fetchall()
# Associated keys and values  =  [(u'natural', u'coastline')]

# Number of rows in ways_tags grouped by keys
df = pd.read_sql_query("SELECT key, COUNT(key) as num FROM ways_tags \
                    GROUP BY key ORDER BY num DESC;", conn)
df[1:10]

# Plot the bar chart
fig = plt.figure(figsize = (9,3))
ax = fig.add_subplot(111)
a = 0.85
df[0:10].plot(kind='bar',
                stacked=False,
                ax=ax,
                alpha=a, 
                legend=False, 
                title="Top ten keys in ways",
                color='#39CCCC',    
                grid=False)

ax.set_xticklabels(['highway','building','surface','oneway','name','lanes','source','street','landuse','maxspeed'],
                    fontsize=8, alpha=a, rotation=0)
for label in ax.get_yticklabels():
        label.set_fontsize(8)
        label.set_alpha(a)
    
# Set labels
plt.xlabel('Keys')
plt.ylabel('Count')

plt.show()

# Number of rows in nodes_tags grouped by keys
df = pd.read_sql_query("SELECT key, COUNT(key) as num FROM nodes_tags \
                    GROUP BY key ORDER BY num DESC;", conn)
df[0:10]

# Plot the bar chart
fig = plt.figure(figsize = (9,3))
ax = fig.add_subplot(111)
a = 0.85
df[0:10].plot(kind='bar',
                stacked=False,
                ax=ax,
                alpha=a, 
                legend=False, 
                title="Top ten keys in nodes",
                color='#39CCCC',    
                grid=False)

ax.set_xticklabels(['source','street','name','housenumber','shop','city','power','amenity','hughway','en'],
                    fontsize=8, alpha=a, rotation=0)
for label in ax.get_yticklabels():
        label.set_fontsize(8)
        label.set_alpha(a)
    
# Set labels
plt.xlabel('Keys')
plt.ylabel('Count')

plt.show()

# Close database connection
conn.close()

##******************************************************
