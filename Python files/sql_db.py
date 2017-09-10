# required python imports
import pandas as pd
import sqlite3
import pandas as pd

"""
Code for creating database tables and inserting data in the table.
Author: Rupa Bisaria

"""

class dbSQL(object):
    
    def __init__(self):
        '''
        Initializes an dbSQL instance
        
        connection: connection to the database                  
        '''
        self.connection = sqlite3.connect('osm.db', timeout=10) # default is 5 seconds, per docs.python.org/2/library/sqlite3.html#sqlite3.connect which often caused 'database is locked' error
            
    def create_table(self, table_name, table_schema):
        '''
        Creates database table by a given name as per a given schema
        
        '''
        c = self.connection.cursor()
        c.execute(table_schema)
        self.connection.commit()
        
    def insert_data(self, table_name, csv_file):
        '''
        Inserts values in a given database table from a given csv file
        
        '''
        self.connection.text_factory = lambda x: x.decode('latin-1')

        df_nodes = pd.read_csv(csv_file)
        df_nodes.to_sql(table_name, self.connection, if_exists='append', index=False)
        
    def close_connection(self):
        '''
        Closes database connection
        '''
        self.connection.close()
        