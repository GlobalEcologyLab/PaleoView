# Python modules
from os import chdir, getcwd, system, path, listdir
import filecmp
import string

# Python extension modules (requires extension installation)
import numpy as np
import pandas as pd
from netCDF4 import Dataset
from docx import Document

# Tool library module
from PaleoclimateToolDataFileHelper import PaleoclimateToolDataFileHelper
## Main program

# Create the Paleoclimate Tool Data File Helper
data_helper = PaleoclimateToolDataFileHelper()

# Set the climate data, mask, and bias correction directories
chdir(path.join(getcwd(), '..'))
current_tool_version_directory = getcwd()
chdir(path.join(getcwd(), '..'))
tool_directory = getcwd()
data_helper.setClimateDataSource('local')
#data_helper.setClimateDataDirectory(path.join(tool_directory, 'Climate Data'))
data_helper.setClimateDataDirectory(r'C:/Users/shaythorne/Desktop/PaleoView/Tests/NetCdfClimateData')
data_helper.getCurrentNetCdfDataIntervals()
data_helper.setRegionMaskDirectory(path.join(current_tool_version_directory, 'Map Data'))
data_helper.setBiasCorrectionDirectory(path.join(current_tool_version_directory, 'Bias Corrections'))
data_helper.setFileGenerationDirectory(path.join(current_tool_version_directory, 'Test', 'DataFileTests'))

self = data_helper
parameter = 'relative_humidity'
##root_interval_str = '5000BP-1989AD'
##self.climate_data_directory['path']
##(parameter+'-'+root_interval_str+'.nc')
##rootgrp = Dataset(path.join(self.climate_data_directory['path'], (parameter+'-'+root_interval_str+'.nc')), 'r')
##rootgrp.groups.keys()
##sub_interval_str = u'1000BP-0BP'
##year_str = '0BP'
##month_index = 10
##rootgrp.groups[sub_interval_str].variables[year_str][month_index]
##rootgrp.variables['decimals'][:]
