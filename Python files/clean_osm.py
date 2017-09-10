#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code for cleaning OSM files 
Author: Rupa Bisaria

Cleans few keys for a 'tag' element of the elements 'node' and 'way' from the OSM file

"""

import xml.etree.cElementTree as ET
import re
from collections import defaultdict
import string


class cleanOSM(object):
    
    def __init__(self, dirty_value, mapping = {}, expected_values = []):
        '''
        Initializes an cleanOSM instance
        
        value: value attribute of an element for cleaning
        
        mapping: dictionary mapping dirty values to clean values
        
        expected_values: list of expected values for the given key
                
        '''
        self.dirty_value = dirty_value
        self.mapping = mapping
        self.expected_values = expected_values
           
    def clean_value(self):
        '''
        For given value and a mapping dictionary replace with the clean value
        from the dictionary
        
        @return : string which is cleaned version of passed string
        '''
        if self.dirty_value in self.mapping.keys():
            return self.mapping[self.dirty_value]
        else:
            return self.dirty_value
    
    def set_to_none(self):
        '''
        Substitute dirty value with NaN
        
        @return : None
        '''
        return 'None'
                           

    def update_street_name(self):
        '''
        For given street name and a mapping dictionary remove abbreviations 
        and correct case by mapping against supplied dictionary
        eg: Sibaytah St => Sibaytah Street

        @return: string which is cleaned version of passed string

        '''
        
        clean_value = self.dirty_value
        
        # Iterate over each key in 'mapping'
        for key in self.mapping:
            # check if the key is in the street name
            if key in self.dirty_value:
                key_regex = r"\b(" + key + r")\b(\.|\`)?"
                
                # check for the regex and substitute it for the value of key in 'mapping'
                if re.search(key_regex, self.dirty_value):
                    clean_value = re.sub(key_regex, self.mapping[key], self.dirty_value)   
                    
        return clean_value

        
    def replfunc(self, m):
        '''
        For a given regex match return with second group in uppercase and 
        remove whitespace between the groups

        @return: string with second group of the regex match in uppercase
        '''
        return (m.groups()[0]+m.groups()[1].upper()).strip()


    def street_letter_to_uppercase_and_removegap(self, name):
        '''           
        Capture a street name with digits attached to letters in  using a 
        regex and convert the attached alphabate to upper case
        eg: Street 6a => Street 6A
        eg: 11 B => 11B
             2-A => 2A
        @return: string which is cleaned version of passed string
        '''
        clean_value = name
        
        # regex for getting street number with digits followed letter(s)
        regex = r"(\d{1,2})\s?\-?([a-z|A-Z]{1,2})\b"
        
        if re.search(regex, name):
            return re.sub(regex, lambda x: self.replfunc(x), name) 
        return clean_value
    
        
    def switchfunc(self, m, index_1, index_2):
        '''
        For a given regex match return with first group in uppercase and 
        switch position of first and second groups

        @return: string first group of regex in upper case and the respective
        positions of the two groups switched
        '''
        return m.groups()[index_1]+m.groups()[index_2].upper()

        
    def switch_digit_position(self, name):
        '''
        Capture street numbers with letter preceeding the digit using 
        a regex and  switch the position of digit and letter
        eg E11 => 11E
        
        @return: string which is cleaned version of passed string
        '''
        # regex for getting street number with digits followed letter(s)
        clean_value = name
        regex = r"\b([A-Z])(\d{1,2})\b"
        if re.search(regex, name):
            return re.sub(regex, lambda x: self.switchfunc(x,1,0), name) 
        return clean_value

        
    def remove_hypen_space_and_switch(self, name):
        '''
        Capture street number with hypen between digit and letter 
        using a regex and remove hyphen 
        eg: M-26 => 26M
        
        @return: string which is cleaned version of passed string
        '''
        clean_value = name
        regex = r"(?<!(Plot No\. ))([A-Z])[\-|\s](\d{1,2})\b"
        if re.search(regex, name):
            return re.sub(regex, lambda x: self.switchfunc(x,2,1), name) 
        return clean_value

        
    def remove_brackets(self, name):
        '''
        Capture street number with brackets and 'th' suffix using a 
        regex and remove brackets and suffix 'th' or 'rd'
        eg: Sa'ada Street (19th) => Sa'ada Street 19
        
        @return: string which is cleaned version of passed string
        '''
        clean_value = name
        regex = r"\(?(\d{1,2})(th|rd|st|TH|nd)\)?"
        if re.search(regex, name):
            return re.sub(regex, lambda x:x.groups()[0], name) 
        return clean_value

    
    def add_street_prefix(self, name):
        '''
        Using regex capture check if street number is without 'Street' prefix or 
        suffix and add it as prefix
        eg: 11B => Street 11B  
        
        @return: string which is cleaned version of passed string
        '''
        clean_value = name
        # Exclude all string preceeded by 'Street','France','Center' and '(Di)strict'
        regex = r"(?<!(Street |France |Center |strict ))(\b\d{1,2}[A-Z]{1}\b)(?! Street| Sikka)"
        regex_1 = r"^(\b\d{1,2}\b)$"
        if re.search(regex, name):
            return re.sub(regex, lambda x: "Street "+x.groups()[1], name) 
        elif re.search(regex_1, name):
            return re.sub(regex_1, lambda x: "Street "+x.groups()[0], name) 
        
        return clean_value

       
    def switch_number(self, m):
        '''
        For a given regex match return switched position of first and second 
        groups and insert a white space between them
        
        @return: string with the respective positions of the two groups switched
        '''
        return m.groups()[2]+" " + m.groups()[1]

        
    def put_number_after_street(self, name):
        '''
        Capture street name with 'Street' as suffix using a regex and change it 
        to prefix
        eg: 17 Street => Street 17
        exception: 1 Street 17, Al Safa => 1 Street 17, Al Safa
        
        @return: string which is cleaned version of passed string
        '''
        clean_value = name
        regex = r"(?<!(\d{2} ))(\b\d{1,2}[A-Z]{0,1})\s(Street)(?! \d{2})"
        if re.search(regex, name):
            return re.sub(regex, lambda x: self.switch_number(x), name) 
        return clean_value
    
    def remove_non_street_values(self, name):
        '''
        Sets a name not in the expected street list to None, else returns 
        the name.
        
        eg: 
        `Ibn Sina Medical Centre`
        `24°26'24.5"N 54°27'03.8"E`
        `P.O. Box 34429`
        
        @return: string 
        '''
        if any(value in name for value in self.expected_values):
            return name
        return 'None'

    def extract_street(self, name):
        '''
        Extracts street name from the text
        
        eg: 
        `Jumeirah Village Triangle,  District 2, Street 5 =>  Street 5`
        
        @return: string for street name
        '''
        split_on = ['-',',']

        for char in split_on:
            if char in name:
                for name_part in name.split(char):
                    if any(value in name_part for value in self.expected_values): 
                        return name_part
        return name

    def clean_street_name(self):
        '''
        Uses functions for cleaning street name in a particular sequence to get
        clean street name for a given dirty name.
        
        @return: string clean name for a given dirty street name
        '''
        clean_name = self.update_street_name()
        clean_name = self.remove_brackets(string.capwords(clean_name))
        clean_name = self.street_letter_to_uppercase_and_removegap(clean_name) 
        clean_name = self.switch_digit_position(clean_name) 
        clean_name = self.remove_hypen_space_and_switch(clean_name) 
        clean_name = self.put_number_after_street(clean_name) 
        clean_name = self.add_street_prefix(clean_name) 
        clean_name = self.remove_non_street_values(clean_name)
        if clean_name != "None":
            clean_name = self.extract_street(clean_name)
        return clean_name
    
    def is_expected_city(self):
        '''
        Entries with string matching any city name from expected city list is 
        assigned the match from the list.
        eg: 
         'Jumeriah Lake Towers, Dubai':'Dubai',
        
        @return : tuple (bool,string) True if match, matching city
        
        '''
        
        for value in self.expected_values:
            if value in string.capwords(self.dirty_value):
                return (True,value)
        return (False,'')
    
    def clean_city_name(self):
        '''
        Entries with string matching any city name from expected city list is 
        assigned the match from the list.
        eg: 
         'Jumeriah Lake Towers, Dubai':'Dubai',
        
        For given street name and a mapping dictionary remove abbreviations 
        and correct case by mapping against supplied dictionary
        eg:       
         'fujairah': 'Fujairah',
         
        Arabic and numeric entries to 'None'. All other entries with no string
        matching any city name from expected city list is left as is.      
        
        @return: string which is cleaned version of passed string
        '''
        city_status = self.is_expected_city()
        regex_english = re.compile(r'^[a-z|A-Z]+.')
        wrong_entry = ['town','ME-12','AE','San Diego, CA']
        
        if city_status[0]:
            return city_status[1]
        elif self.dirty_value in self.mapping.keys():
            return self.clean_value()
        elif regex_english.search(self.dirty_value):
            if self.dirty_value in wrong_entry:
                return self.set_to_none()
            else:
                return string.capwords(self.dirty_value)         
        else:
            return self.set_to_none()
            
   
        
        