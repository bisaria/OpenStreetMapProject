## OpenStreetMap Project
***

This project map data from Dubai-Abu Dhabi region from [https://www.openstreetmap.org](https://s3.amazonaws.com/metro-extracts.mapzen.com/dubai_abu-dhabi.osm.bz2) and uses data munging techniques, such as assessing the quality of the data for validity, accuracy, completeness, consistency and uniformity to clean the OpenStreetMap data. This clean data was saved to SQL database, as per a pre-specified data schema.

Html report for this project can be accessed [here](https://htmlpreview.github.io/?https://github.com/bisaria/OpenStreetMapProject/blob/master/Project%20Report/OpenStreetMapProject.html#data-exploration).

### PDF file

  * OpenStreetMapProject
  
    Complete project report as per project rubric.

### Python Script

Following are the python scripts used for the project:

  * audit_osm
  
      Script that audits any 'k' attribute for a 'tag' element of the elements 'node' and 
'way' from an OSM file

  * clean_osm
  
      Script for Cleaning few keys for a 'tag' element of the elements 'node' and 'way' from the OSM file

  * osm_file
  
      Script for handling OSM files as provided by Udacity
  
  * convertToCSV
  
      Script for parsing the elements in the OSM XML file, transforming them from document 
format to tabular format for converting into csv files. 

  * schema
  
      Pre defined schema for csv as provided by Udacity
  
  * sql_db
      
      Script for creating a sql database table and inserting data in the table
      
  * osm_project
  
      Script for loading, auditing and cleaning the osm file. The clean data
is then converted to csv and saved as dabase tables in sqlite. Finally, the data
is queried to answer few questions about the data.

### Text Files

  * data_selection.txt
  
    Brief description about the map area selected for the project
  
  * references.txt
  
    List of references for the project
    
### OSM file

  Sample osm file of approximately 8MB created from the original osm file used in the project.
  
    
