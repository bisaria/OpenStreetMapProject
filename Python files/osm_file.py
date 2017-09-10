#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code for handling OSM files as provided by Udacity

Since the OSM file size under consideration might be as big as 50MB if not more, it
may not be feasible to audit and clean the full data at one go, due to likely memory 
and time issues. 

Hence, multiple sample files are created by picking out every n-th top element from 
the OSM file, where n is a variable to be decided as per required size of the sample 
file. This makes auditing and cleaning much faster. Finally, whole of OSM file may be 
taken for final auditing, cleaning and analysis.

## Get Element Function
The function takes the osm file and yield tag elements 'node', 'way' and 'relation'

## Create Sample File Function
The function takes the osm file and extacts every n-th element from it and creates 
and writes an osm sample file.

"""

import xml.etree.cElementTree as ET

class OSMFile(object):
    
    def __init__(self, osm_file, sample_file, sample_size):
        '''
        Initializes an OSMFile instance
        
        osm_file: OSM file for analysis
        
        sample_file: Sample file created from the OSM file
        
        sample_size: Used to create a sample file by taking every sample_size-th 
                        top level element from the OSM file
        
        '''
        self.osm_file = osm_file
        self.sample_size = sample_size
        self.sample_file = sample_file
        
    
    def get_element(self, tags=('node', 'way', 'relation')):
        '''
        Yields element if it is the right type of tag

        tags: tag elements to be extracted from osm_file 

        Reference:
        http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
        '''

        context = iter(ET.iterparse(self.osm_file, events=('start', 'end')))
        _, root = next(context)
        
        for event, elem in context:
            if event == 'end' and elem.tag in tags:
                yield elem
                root.clear()
            
    def create_sample_file(self):
        '''
        Creates and writes an osm sample file by taking every sample_size-th 
        top level element from the OSM file.
        
        Sample file is used for auditing and cleaning the osm data. Multiple
        sample files of various sizes are used for the purpose, before running 
        the codes on the full osm file. 
        
        '''
        k = self.sample_size
        
        with open(self.sample_file, 'wb') as output: 
            output.write('<?xml version="1.0" encoding="UTF-8"?>\n') 
            output.write('<osm>\n ')

            # Write every kth top level element
            for i, element in enumerate(self.get_element()):
                if i % k == 0:
                    output.write(ET.tostring(element, encoding='utf-8'))

            output.write('</osm>')

    