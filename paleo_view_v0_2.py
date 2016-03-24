# Python modules
import base64
import string
import sys
import Tkinter as tk
import ttk
from Crypto.Cipher import AES
from os import chdir, environ, getcwd, listdir, mkdir, path
from shutil import copyfile
from StringIO import StringIO
from time import time, localtime, strftime
from tkFileDialog import *
from tkFont import Font
from tkMessageBox import *
import warnings
warnings.simplefilter('ignore')

# Python extension modules (requires extension installation)
import numpy as np
import pandas as pd

# Python extension Matplot and Basemap modules
from mpl_toolkits.basemap import Basemap
import FileDialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib import rcParams

# Mac version?
MAC_VERSION = False

# Tool library modules
from PaleoclimateToolDataFileHelper import PaleoclimateToolDataFileHelper

# TEST FLAG: Write stdout and stderr to console (not log files)
DEBUG = True

# Code for encrypting/decrypting the proxy password when saved/retrieved from the config file
BLOCK_SIZE = 32
PADDING = ' '
PadPassword = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(PadPassword(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
PASSWORDKEY = '\xe7Z\xb2\xc9\x03\xb4\x8c\x04A\xfe\x97\xc3\xf9\xc7\xd2\x1c\xb9\x1eh\xd0\x91E/\xdb\xc9\x9f\xf0\xda\x8e\x06\xae\xd5' # set using os.urandom(BLOCK_SIZE)

## Application GUI
## * Constructs tool GUI components
## * Defines and follows a workflow of step completion
## * Performs tool operations utilising climate data helper module
class ApplicationGUI(tk.Frame) :

    ## GUI Initilisation Methods ############################################################################################################################################

    # Initialise GUI and workflow
    def __init__(self, user_application_data_directory, master=None) :

        tk.Frame.__init__(self, master)
        self.grid()

        # Create the Paleoclimate data file helper
        self.data_file_helper = PaleoclimateToolDataFileHelper(application_gui=self)

        # Configuration file (initially in the same directory as the tool, but copied to user application data directory)
        self.tool_config_file = 'paleo_view_config.txt'

        # User application data directory
        self.user_application_data_directory = user_application_data_directory

        # Initialise config parameters
        self.climate_data_source = 'url' # local/url
        self.climate_data_url = 'https://dl.dropboxusercontent.com/sh/upmj85imokepgts/'
        self.climate_data_proxy_active = False
        self.climate_data_proxy_url = 'http://example.proxy.com:80/'
        self.climate_data_proxy_username = ''
        self.climate_data_proxy_password = ''
        self.climate_data_directory = ''
        self.default_file_generation_directory = ''
        self.default_file_generation_directory_set = False
        self.region_mask_directory = path.join(getcwd(), 'Map Data')
        self.bias_correction_directory = path.join(getcwd(), 'Bias Corrections')
        self.public_release = True
        self.show_extended_colour_palettes_in_advance = False

        # Current directory locations
        self.current_figure_save_directory = ''

        # Tool generation log file
        self.tool_generation_log_file = 'paleo_view_generation_log.txt'
        self.tool_generation_log_entry = { 'data_type' : None,
                                           'data_action' : None,
                                           'parameter_group' : None,
                                           'parameter' : None,
                                           'time_unit' : None,
                                           'time_unit_value' : None,
                                           'region' : None,
                                           'period_from' : { 'year' : None, 'postfix' : None },
                                           'period_until' : { 'year' : None, 'postfix' : None },
                                           'interval_step' : None,
                                           'interval_size' : None,
                                           'bias_correction' : False,
                                           'utilise_delta' : False,
                                           'delta_as_percent' : False,
                                           'delta_reference' : { 'year' : None, 'postfix' : None },
                                           'grids_generated' : None,
                                           'figure' : None,
                                           'existing' : False,
                                           'statistics_generated' : False,
                                           'statistics_table' : None }

        # Maximum maps and time series points
        self.maximum_maps = 20
        self.maximum_time_series_points = 500
        self.maximum_interval_steps = self.maximum_maps - 1 # self.maximum_time_series_points

        # Month codes, names, shortnames
        self.month_codes = self.data_file_helper.getMonthCodes()
        self.month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        self.month_shortnames = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

        # Grid region statistics keys and names
        self.grid_region_statistics_keys = ['minimum', 'percentile_5th', 'percentile_25th', 'percentile_50th', 'percentile_75th', 'percentile_95th', 'maximum',
                                            'grid_mean', 'grid_stdev', 'area_mean', 'area_stdev']
        self.grid_region_statistics_names = { 'minimum' : 'Minimum',
                                              'percentile_5th' : '5th Percentile',
                                              'percentile_25th' : 'Q1',
                                              'percentile_50th' : 'Median',
                                              'percentile_75th' : 'Q3',
                                              'percentile_95th' : '95th Percentile',
                                              'maximum' : 'Maximum',
                                              'grid_mean' : 'Mean (grid)',
                                              'grid_stdev' : 'Stdev (grid)',
                                              'area_mean' : 'Area Mean',
                                              'area_stdev' : 'Area Stdev' }

        # Configuration relating to tool options:
        self.tool_option_parameters = ['climate_data_source', 'climate_data_directory', 'climate_data_url', 'climate_data_proxy_active',
                                       'climate_data_proxy_url', 'climate_data_proxy_username', 'climate_data_proxy_password',
                                       'default_file_generation_directory', 'default_file_generation_directory_set', 'public_release',
                                       'show_extended_colour_palettes_in_advance']
        self.tool_option_parameter_types = { 'climate_data_source' : str, 'climate_data_directory' : str, 'climate_data_url' : str,
                                             'climate_data_proxy_active' : bool, 'climate_data_proxy_url' : str, 'climate_data_proxy_username' : str,
                                             'climate_data_proxy_password' : str, 'default_file_generation_directory' : str,
                                             'default_file_generation_directory_set' : bool, 'public_release' : bool, 'show_extended_colour_palettes_in_advance' : bool }

        # Parameter fixed range colour scheme # TODO: establish values via config
        self.parameter_fixed_range_colour_scheme = { 'temperature' : { 'mean-temperature' : { 'value' : {}, 'delta' : {} },
                                                                       'minimum-temperature' : { 'value' : {}, 'delta' : {} },
                                                                       'maximum-temperature' : { 'value' : {}, 'delta' : {} },
                                                                       'diurnal-temperature-range' : { 'value' : {}, 'delta' : {} },
                                                                       'annual-temperature-range' : { 'value' : {}, 'delta' : {} },
                                                                       'isothermality' : { 'value' : {}, 'delta' : {} },
                                                                       'temperature-seasonality' : { 'value' : {}, 'delta' : {} } },
                                                     'precipitation' : { 'mean-precipitation' : { 'value' : {}, 'delta' : {} },
                                                                         'precipitation-seasonality' : { 'value' : {}, 'delta' : {} } },
                                                     'humidity' : { 'specific-humidity' : { 'value' : {}, 'delta' : {} },
                                                                    'relative-humidity' : { 'value' : {}, 'delta' : {} } },
                                                     'sea-level-pressure' : { 'sea-level-pressure' : { 'value' : {}, 'delta' : {} } } }
        self.parameter_fixed_range_colour_scheme['temperature']['mean-temperature']['value'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['mean-temperature']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['minimum-temperature']['value'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['minimum-temperature']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['maximum-temperature']['value'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['maximum-temperature']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['diurnal-temperature-range']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['diurnal-temperature-range']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['annual-temperature-range']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['annual-temperature-range']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['isothermality']['value'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['isothermality']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['temperature-seasonality']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['temperature']['temperature-seasonality']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['precipitation']['mean-precipitation']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['precipitation']['mean-precipitation']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['precipitation']['mean-precipitation']['%delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['precipitation']['precipitation-seasonality']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['precipitation']['precipitation-seasonality']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['humidity']['specific-humidity']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['humidity']['specific-humidity']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['humidity']['relative-humidity']['value'] = { 'min' : 0.0, 'first_boundary' : None, 'last_boundary' : None, 'max' : 100.0 }
        self.parameter_fixed_range_colour_scheme['humidity']['relative-humidity']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['sea-level-pressure']['sea-level-pressure']['value'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }
        self.parameter_fixed_range_colour_scheme['sea-level-pressure']['sea-level-pressure']['delta'] = { 'min' : None, 'first_boundary' : None, 'last_boundary' : None, 'max' : None }

        # Load config from file and warn if file not found
        config_warning = self.loadConfig()
        if config_warning :
            showwarning('Error Loading Configuration', config_warning)

        # Set the climate data source, url and directory, and the file generation, mask, and bias correction directories
        self.data_file_helper.setClimateDataSource(self.climate_data_source)
        self.data_file_helper.setClimateDataUrl(self.climate_data_url)
        self.data_file_helper.setClimateDataProxy(self.climate_data_proxy_active, self.climate_data_proxy_url, self.climate_data_proxy_username, self.climate_data_proxy_password)
        self.data_file_helper.setClimateDataDirectory(self.climate_data_directory)
        self.data_file_helper.setFileGenerationDirectory(self.default_file_generation_directory)
        self.data_file_helper.setRegionMaskDirectory(self.region_mask_directory)
        self.data_file_helper.setBiasCorrectionDirectory(self.bias_correction_directory)

        # Tool Process steps
        self.process_step = {}
        self.process_step['data_type'] = { 'number' : '1', 'dependents' : [], 'completed': False }
        self.process_step['parameter_selection'] = { 'number' : '2', 'dependents' : ['data_type'], 'completed': False }
        self.process_step['region_selection'] = { 'number' : '3', 'dependents' : ['data_type', 'parameter_selection'], 'completed': False }
        self.process_step['period_interval'] = { 'number' : '4', 'dependents' : ['data_type', 'parameter_selection', 'region_selection'], 'completed': False }
        self.process_step['bias_correction'] = { 'number' : '5', 'dependents' : ['data_type', 'parameter_selection', 'region_selection', 'period_interval'], 'completed': False }
        self.process_step['delta'] = { 'number' : '6', 'dependents' : ['data_type', 'parameter_selection', 'region_selection', 'period_interval', 'bias_correction'], 'completed': False }
        self.process_step['generation'] = { 'number' : '7', 'dependents' : ['data_type', 'parameter_selection', 'region_selection', 'period_interval', 'bias_correction', 'delta'], 'completed': False }

        # Process frames
        self.createMenu()

        # Configure the font for tool headings
        default_font = Font(font='TkDefaultFont')
        tool_label_font = Font(family=default_font.cget('family'), size=default_font.cget('size'), weight='bold')

        # Tool sections
        self.main_frame = tk.LabelFrame(self, padx=10, pady=5)
        self.createDataTypeFrame()
        self.createParameterSelectionFrame()
        self.createRegionSelectionFrame()
        self.createPeriodIntervalFrame()
        self.createDeltaFrame()
        self.createBiasCorrectionFrame()
        self.createGenerationFrame()
        self.main_frame.grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=5, pady=5)

        # Set initial Period Interval Values
        self.setInitialPeriodIntervalValues()

        # Flag when validation warnings are pending
        self.validation_warning_pending = False

        # Flag when warning produced by update call to validation method
        self.warning_shown_for_update_validation = False

        # Flag for forcing shifting focus when validation is triggered by option menus
        self.force_shift_focus = False

        # Flag warning messages so as to avoid calling additional validation checks triggered by focusout events
        self.currently_showing_warning_message = False

        # Setup colour schemes and palettes
        self.map_colour_schemes = ['fixed_range', '90%_range']
        self.map_colour_scheme_selection = ['Fixed range', '90% range']
        self.map_colour_scheme = 'fixed_range'
        self.map_colour_palette = '' # set within palette setup
        #self.auto_map_colour_palette = True
        self.reverse_map_colour_palette = False
        self.map_colour_boundary_lines = True
        self.map_colour_zero_boundary = False
        self.setupColourPalettes()

        # Use contoured colour maps?
        self.use_contoured_grid_maps = True

        # Show grid map land_boundaries?
        self.show_grid_map_land_boundaries = True

        # Map grid
        self.show_map_grid_lines = True
        self.map_grid_includes = ['ticks', 'lines']
        self.map_grid_include_selection = ['ticks only', 'lines']
        self.map_grid_include = 'ticks'
        self.map_grid_spaces = [2.5, 5.0, 10.0, 15.0, 30.0]
        self.map_grid_space_selection = ['2.5', '5.0', '10.0', '15.0', '30.0']
        self.map_grid_space = None # use region grid space when not defined

    # Load configuration from a file and return warning if any
    def loadConfig(self) :
        warning = ''
        orig_config_file_path = path.join(getcwd(), self.tool_config_file)
        user_config_file_path = path.join(self.user_application_data_directory, self.tool_config_file)
        if not path.exists(user_config_file_path) and path.exists(orig_config_file_path) :
            copyfile(orig_config_file_path, user_config_file_path)
        if path.exists(user_config_file_path) :
            f = open(user_config_file_path)
            lines = f.readlines()
            f.close()
            for line in lines :
                if line.find('=') != -1 :
                    name = 'self.' + line.split('=')[0].strip()
                    value = line.split('=',1)[1].strip()
                    # Decrypt proxy password
                    if name == 'self.climate_data_proxy_password' :
                        cipher = AES.new(PASSWORDKEY)
                        value = DecodeAES(cipher, value)
                    try :
                        exec(name + ' = eval(value)')
                    except Exception, e :
                        exec(name + ' = value')
        else :
            warning = 'Could not find configuration file. Using default configuration.'
        return warning

    # Get tool options
    def getToolOptions(self, option_parameters=None) :
        if not option_parameters :
            option_parameters = self.tool_option_parameters
        tool_options = {}
        for option in option_parameters :
            tool_options[option] = eval('self.'+option)
        return tool_options

    # Set tool options, including updating config file
    def setToolOptions(self, tool_options) :

        config_file_path = path.join(self.user_application_data_directory, self.tool_config_file)

        # Read config file
        if path.exists(config_file_path) :

            # Read file lines
            f = open(config_file_path)
            file_lines = f.readlines()
            f.close()

            # Ensure last line has newline char
            if len(file_lines) > 0 :
                if file_lines[len(file_lines)-1].find('\n') == -1 :
                    file_lines[len(file_lines)-1] += '\n'

        else :
            file_lines = []

        # Set options within tool and config file lines
        for option, value in tool_options.items() :

            # Set within tool
            name = 'self.' + option
            exec(name + ' = value')

            # Encrypt proxy password
            if option == 'climate_data_proxy_password' :
                cipher = AES.new(PASSWORDKEY)
                value = EncodeAES(cipher, value)

            # Set within config file lines
            found_within_file = False
            for i, line in enumerate(file_lines) :
                if line.find(option) != -1 :
                    if line.find('=') != -1 :
                        if line.split('=')[0].strip() == option :
                            file_lines[i] = line.split('=')[0] + '= ' + str(value) + '\n'
                            found_within_file = True
            if not found_within_file :
                file_lines.append(option + ' = ' + str(value) + '\n')

        # Write config file
        f = open(config_file_path, 'w')
        f.writelines(file_lines)
        f.close()

    # Method setup colour palettes
    def setupColourPalettes(self) :
        self.colour_palettes = ['rainbow', 'red_blue', 'ar4', 'extended_red_blue']
        self.map_colour_palette = 'rainbow'
        self.extended_colour_palettes = ['extended_red_blue']
        rainbow = ['#fa58f4', '#0000ff', '#819ff7', '#81f7f3', '#04b431', '#44ff00', '#ffff00', '#fe9a2e', '#fec3d2', '#ff0000', '#cc3300']
        rainbow_reversed = rainbow[:]
        rainbow_reversed.reverse()
        red_blue = ['#0000ac', '#0000ff', '#8888ff', '#a9a9ff', '#d5d5ff', '#ffffff', '#ffd7d7', '#ffaaaa', '#ff6464', '#ff0000', '#cc3300']
        red_blue_reversed = red_blue[:]
        red_blue_reversed.reverse()
        ar4 = ['#668bf1', '#94b0fe', '#b1c4fa', '#d1dcfb', '#eaeffc', '#ffffce', '#ffe898', '#ffc98e', '#f3a24b', '#ff8257', '#fc551d']
        ar4_reversed = ar4[:]
        ar4_reversed.reverse()
        extended_red_blue = ['#7a0000', '#b50000', '#df0000', '#ff0000', '#fa563d', '#ffa495', '#ff7338', '#ffa161', '#fdb56b', '#fecd80',
                           '#f5ecc3', '#d7e2ff', '#b3ccf5', '#97b4fa', '#84a6ff', '#6989ec', '#4c80e6', '#3366d9', '#054baa', '#07378c',
                           '#0a2864', '#0a0931'] # already reversed
        extended_red_blue_reversed = extended_red_blue[:]
        extended_red_blue.reverse()
        self.colour_palette_lists = { False : { 'rainbow' : rainbow, 'red_blue' : red_blue, 'ar4' : ar4, 'extended_red_blue' : extended_red_blue },
                                      True : { 'rainbow' : rainbow_reversed, 'red_blue' : red_blue_reversed, 'ar4' : ar4_reversed, 'extended_red_blue' : extended_red_blue_reversed } }
        self.colourmaps = { False : { 'rainbow' : LinearSegmentedColormap.from_list('rainbow', rainbow, N=11),
                                      'red_blue' : LinearSegmentedColormap.from_list('red_blue', red_blue, N=11),
                                      'ar4' : LinearSegmentedColormap.from_list('ar4', ar4, N=11),
                                      'extended_red_blue' : LinearSegmentedColormap.from_list('extended_red_blue', extended_red_blue[6:17], N=11) },
                            True : { 'rainbow' : LinearSegmentedColormap.from_list('rainbow_reversed', rainbow_reversed, N=11),
                                     'red_blue' : LinearSegmentedColormap.from_list('red_blue_reversed', red_blue_reversed, N=11),
                                     'ar4' : LinearSegmentedColormap.from_list('ar4_reversed', ar4_reversed, N=11),
                                     'extended_red_blue' : LinearSegmentedColormap.from_list('extended_red_blue_reversed', extended_red_blue_reversed[5:16], N=11) } }

    # Menu GUI (will grow over time)
    def createMenu(self) :

        # Menu bar
        top = self.winfo_toplevel()
        self.menu_bar = tk.Menu(top, postcommand=self.shiftFocus)
        top['menu'] = self.menu_bar

        # File menu
        self.file_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.entryconfigure(0, state=tk.DISABLED)
        self.file_menu.add_command(label='Quit', command=self.quit)

        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label='Edit', menu=self.edit_menu)
        self.edit_menu.entryconfigure(0, state=tk.DISABLED)
        self.edit_menu.add_command(label='Map Options', command=self.editMapOptions)
        self.edit_menu_indices = { 'map_options' : 1 }

        # Configure menu
        self.configure_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label='Configure', menu=self.configure_menu)
        self.configure_menu.entryconfigure(0, state=tk.DISABLED)
        self.configure_menu.add_command(label='Climate Data Location', command=self.configureClimateDataLocation)
        self.configure_menu.add_command(label='Default Output Directory', command=self.configureDefaultFileGenerationDirectory)
        self.configure_menu_indices = { 'climate_data_directory' : 1, 'default_file_generation_directory' : 2 }
        #self.configure_menu.entryconfigure(self.configure_menu_indices['default_file_generation_directory'], state=tk.DISABLED)

    # GUI for Step 1: Data Type
    def createDataTypeFrame(self) :

        step_number = self.process_step['data_type']['number']
        #self.data_type_frame = tk.LabelFrame(self, text='Step '+step_number+': Data Type', padx=10, pady=5)
        self.data_type_frame = self.main_frame

        # Data type and action lists
        self.data_type_keys = ['map', 'series']
        self.data_type_selection = ['Map Grid', 'Time Series']
        self.data_action_keys = ['view', 'files']
        self.data_action_selection = ['View', 'Generate Data Files']
        #self.data_action_selection = { 'map' : ['View Map Plot', 'Generate Data Files'], 'series' : ['View Series Plot', 'Generate Data File'] }

        # Parameter text variables
        self.data_type_text = tk.StringVar()
        self.data_type_text.set(self.data_type_selection[0])
        self.data_action_text = tk.StringVar()
        self.data_action_text.set(self.data_action_selection[0])
        #self.data_action_text = { 'map' : tk.StringVar(), 'series' : tk.StringVar() }
        #self.data_action_text['map'].set(self.data_action_selection['map'][0])
        #self.data_action_text['series'].set(self.data_action_selection['series'][0])
        
        # Register validation and selection behaviour methods
        select_data_type = self.data_type_frame.register(self.selectDataType)
        select_data_action = self.data_type_frame.register(self.selectDataAction)
        forced_shift_focus = self.data_type_frame.register(self.shiftFocus)

        # Entry/selection fields
        self.data_type_menu = tk.OptionMenu(self.data_type_frame, self.data_type_text, *self.data_type_selection)
        self.data_type_menu.config(highlightthickness=0, anchor=tk.W, )
        self.data_type_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.data_type_keys) :
            self.data_type_menu['menu'].entryconfigure(i, command=(select_data_type, selection))
        self.data_action_menu = tk.OptionMenu(self.data_type_frame, self.data_action_text, *self.data_action_selection)
        self.data_action_menu.config(highlightthickness=0, anchor=tk.W)
        self.data_action_menu['menu'].config(postcommand=(forced_shift_focus, True))
        #self.data_action_menu = {}
        #self.data_action_menu['map'] = tk.OptionMenu(self.data_type_frame, self.data_action_text['map'], *self.data_action_selection['map'])
        #self.data_action_menu['series'] = tk.OptionMenu(self.data_type_frame, self.data_action_text['series'], *self.data_action_selection['series'])
        #self.data_action_menu['map'].config(highlightthickness=0, anchor=tk.W)
        #self.data_action_menu['series'].config(highlightthickness=0, anchor=tk.W)
        #self.data_action_menu['map']['menu'].config(postcommand=(forced_shift_focus, True))
        #self.data_action_menu['series']['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.data_action_keys) :
            self.data_action_menu['menu'].entryconfigure(i, command=(select_data_action, selection))
            #self.data_action_menu['map']['menu'].entryconfigure(i, command=(select_data_action, 'map', selection))
            #self.data_action_menu['series']['menu'].entryconfigure(i, command=(select_data_action, 'series', selection))

        # Arrange fields on frame with labels
        row = 0
        tk.Label(self.data_type_frame, text='Data:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.data_type_menu.grid(row=row, column=1, sticky=tk.W+tk.E, padx=0, pady=5)
        self.data_action_menu.grid(row=row, column=2, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        #self.data_action_menu['series'].grid(row=row, column=2, sticky=tk.NW+tk.SE, padx=5, pady=5)
        #self.data_action_menu['series'].grid_remove()
        #self.data_action_menu['map'].grid(row=row, column=2, sticky=tk.NW+tk.SE, padx=5, pady=5)

        #self.data_type_frame.grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=5, pady=5)

    # GUI for Step 2: Parameter Selection
    def createParameterSelectionFrame(self) :

        step_number = self.process_step['parameter_selection']['number']
        #self.parameter_selection_frame = tk.LabelFrame(self, text='Step '+step_number+': Parameter Selection', padx=10, pady=5)
        self.parameter_selection_frame = self.main_frame
        self.time_unit_frame = self.main_frame

        # Parameter codes, maps and selection lists
        self.parameter_group_selection = ['Temperature', 'Precipitation', 'Humidity', 'Sea Level Pressure', 'Southern Oscillation'] # Sync array order
        self.parameter_group_codes = ['temperature', 'precipitation', 'humidity', 'sea-level-pressure', 'southern-oscillation']     # ^
        self.parameter_group_code_map = {}
        self.parameter_group_selection_map = {}
        for i, group_code in enumerate(self.parameter_group_codes) :
            self.parameter_group_code_map[group_code] = self.parameter_group_selection[i]
            self.parameter_group_selection_map[self.parameter_group_selection[i]] = group_code
        self.parameter_via_group_selection = {} # Sync order of arrays
        self.parameter_via_group_codes = {}     # ^
        self.parameter_via_group_selection['temperature'] = ['Mean Temperature', 'Minimum Temperature', 'Maximum Temperature', 'Diurnal Temperature Range', 'Annual Temperature Range', 'Isothermality', 'Temperature Seasonality']
        self.parameter_via_group_codes['temperature'] = ['mean-temperature', 'minimum-temperature', 'maximum-temperature', 'diurnal-temperature-range', 'annual-temperature-range', 'isothermality', 'temperature-seasonality']
        self.parameter_via_group_selection['precipitation'] = ['Mean Precipitation', 'Precipitation Seasonality']
        self.parameter_via_group_codes['precipitation'] = ['mean-precipitation', 'precipitation-seasonality']
        self.parameter_via_group_selection['humidity'] = ['Specific Humidity', 'Relative Humidity']
        self.parameter_via_group_codes['humidity'] = ['specific-humidity', 'relative-humidity']
        self.parameter_via_group_selection['sea-level-pressure'] = ['Sea Level Pressure']
        self.parameter_via_group_codes['sea-level-pressure'] = ['sea-level-pressure']
        self.parameter_via_group_selection['southern-oscillation'] = ['SOI', 'ENSO']
        self.parameter_via_group_codes['southern-oscillation'] = ['soi', 'enso']
        self.parameter_via_group_code_map = {}
        self.parameter_via_group_selection_map = {}
        for group_code in self.parameter_group_code_map.keys() :
            self.parameter_via_group_code_map[group_code] = {}
            self.parameter_via_group_selection_map[group_code] = {}
            for i, parameter_code in enumerate(self.parameter_via_group_codes[group_code]) :
                self.parameter_via_group_code_map[group_code][parameter_code] = self.parameter_via_group_selection[group_code][i]
                self.parameter_via_group_selection_map[group_code][self.parameter_via_group_selection[group_code][i]] = parameter_code
        self.parameter_restricted_via_data_type = {}
        self.parameter_restricted_via_data_type['Map Grid'] = {}
        self.parameter_restricted_via_data_type['Map Grid']['southern-oscillation'] = [] # non-gridded data

        # Parameter unit strings
        self.parameter_unit_string = { 'temperature' : {}, 'precipitation' : {}, 'humidity' : {}, 'sea-level-pressure' : {}, 'southern-oscillation' : {} }
        for parameter in ['mean-temperature', 'minimum-temperature', 'maximum-temperature', 'diurnal-temperature-range', 'annual-temperature-range'] :
            self.parameter_unit_string['temperature'][parameter] = u'\u00B0' + 'C'
        for parameter in ['isothermality', 'temperature-seasonality'] :
            self.parameter_unit_string['temperature'][parameter] = ''
        self.parameter_unit_string['precipitation']['mean-precipitation'] = 'mm/day'
        self.parameter_unit_string['precipitation']['precipitation-seasonality'] = ''
        self.parameter_unit_string['humidity']['specific-humidity'] = 'gm/kg'
        self.parameter_unit_string['humidity']['relative-humidity'] = '%'
        self.parameter_unit_string['sea-level-pressure']['sea-level-pressure'] = 'hPa'
        self.parameter_unit_string['southern-oscillation']['soi'] = ''
        self.parameter_unit_string['southern-oscillation']['enso'] = ''

##        # Parameter default colour palettes
##        self.parameter_default_colour_palette = { 'temperature' : {}, 'precipitation' : {}, 'humidity' : {}, 'sea-level-pressure' : {} }
##        for parameter in ['mean-temperature', 'minimum-temperature', 'maximum-temperature'] :
##            self.parameter_default_colour_palette['temperature'][parameter] = { 'value' : 'blue_yellow_red', 'delta' : 'blue_yellow_red' }
##        for parameter in ['diurnal-temperature-range', 'annual-temperature-range'] :
##            self.parameter_default_colour_palette['temperature'][parameter] = { 'value' : 'yellow_orange_red', 'delta' : 'blue_yellow_red' }
##        for parameter in ['isothermality', 'temperature-seasonality'] :
##            self.parameter_default_colour_palette['temperature'][parameter] = { 'value' : 'yellow_orange_red', 'delta' : 'blue_yellow_red' }
##        self.parameter_default_colour_palette['precipitation']['mean-precipitation'] = { 'value' : 'precip_cm', 'delta' : 'precip_delta_cm' }
##        self.parameter_default_colour_palette['precipitation']['precipitation-seasonality'] = { 'value' : 'precip_cm', 'delta' : 'precip_delta_cm' }
##        self.parameter_default_colour_palette['humidity']['specific-humidity'] = { 'value' : 'white_blue', 'delta' : 'humid_delta_cm' }
##        self.parameter_default_colour_palette['humidity']['relative-humidity'] = { 'value' : 'white_blue', 'delta' : 'humid_delta_cm' }
##        self.parameter_default_colour_palette['sea-level-pressure']['sea-level-pressure'] = { 'value' : 'yellow_orange_red', 'delta' : 'blue_yellow_red' }

        # Parameters for time units
        self.time_unit_selection = ['Month', 'Season', 'Annual', 'User-defined', 'All Months']
        self.time_unit_months_selection = self.month_names
        self.time_unit_seasons_selection = ['DJF', 'MAM', 'JJA', 'SON']
        self.selected_time_unit_month_indices = [0]
        self.time_unit_seasons_month_indices = { 'DJF' : [0,1,11], 'MAM' : [2,3,4], 'JJA' : [5,6,7], 'SON' : [8,9,10] }
        self.current_user_defined_time_unit_month_indices = []
        self.time_unit_restricted_via_data_type = {}
        self.time_unit_restricted_via_data_type['Map Grid'] = ['Month', 'Season', 'Annual', 'User-defined']
        self.time_unit_restricted_via_parameter = {}
        self.time_unit_restricted_via_parameter['temperature'] = {}
        self.time_unit_restricted_via_parameter['temperature']['annual-temperature-range'] = ['Annual']
        self.time_unit_restricted_via_parameter['temperature']['temperature-seasonality'] = ['Annual']
        self.time_unit_restricted_via_parameter['precipitation'] = {}
        self.time_unit_restricted_via_parameter['precipitation']['precipitation-seasonality'] = ['Annual']
        self.time_unit_is_all_months = False

        # Parameter text variables
        self.parameter_group_text = tk.StringVar()
        self.parameter_group_text.set(self.parameter_group_selection[0])
        self.parameter_via_group_text = {}
        self.parameter_via_group_text['temperature'] = tk.StringVar()
        self.parameter_via_group_text['precipitation'] = tk.StringVar()
        self.parameter_via_group_text['humidity'] = tk.StringVar()
        self.parameter_via_group_text['sea-level-pressure'] = tk.StringVar()
        self.parameter_via_group_text['southern-oscillation'] = tk.StringVar()
        self.parameter_via_group_text['temperature'].set(self.parameter_via_group_selection['temperature'][0])
        self.parameter_via_group_text['precipitation'].set(self.parameter_via_group_selection['precipitation'][0])
        self.parameter_via_group_text['humidity'].set(self.parameter_via_group_selection['humidity'][0])
        self.parameter_via_group_text['sea-level-pressure'].set(self.parameter_via_group_selection['sea-level-pressure'][0])
        self.parameter_via_group_text['southern-oscillation'].set(self.parameter_via_group_selection['southern-oscillation'][0])
        self.time_unit_text = tk.StringVar()
        self.time_unit_text.set(self.time_unit_selection[0])
        self.time_unit_months_text = tk.StringVar()
        self.time_unit_months_text.set(self.time_unit_months_selection[0])
        self.time_unit_seasons_text = tk.StringVar()
        self.time_unit_seasons_text.set(self.time_unit_seasons_selection[0])
        self.time_unit_other_text = tk.StringVar()
        self.time_unit_other_text.set('')

        # Register validation and selection behaviour methods
        select_parameter_group = self.parameter_selection_frame.register(self.selectParameterGroup)
        select_parameter = self.parameter_selection_frame.register(self.selectParameter)
        select_time_unit = self.time_unit_frame.register(self.selectTimeUnit)
        forced_shift_focus = self.time_unit_frame.register(self.shiftFocus)

        # Entry/selection fields
        self.parameter_group_menu = tk.OptionMenu(self.parameter_selection_frame, self.parameter_group_text, *self.parameter_group_selection)
        self.parameter_group_menu.config(highlightthickness=0, anchor=tk.W)
        self.parameter_group_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, group_code in enumerate(self.parameter_group_codes) :
            self.parameter_group_menu['menu'].entryconfigure(i, command=(select_parameter_group, group_code))
        # Dynamic parameter fields
        self.parameter_via_group_menu = {}
        for group_code in self.parameter_group_codes :
            if len(self.parameter_via_group_codes[group_code]) > 1 :
                self.parameter_via_group_menu[group_code] = tk.OptionMenu(self.parameter_selection_frame, self.parameter_via_group_text[group_code], *self.parameter_via_group_selection[group_code])
                self.parameter_via_group_menu[group_code].config(highlightthickness=0, anchor=tk.W)
                self.parameter_via_group_menu[group_code]['menu'].config(postcommand=(forced_shift_focus, True))
                for i, parameter_code in enumerate(self.parameter_via_group_codes[group_code]) :
                    self.parameter_via_group_menu[group_code]['menu'].entryconfigure(i, command=(select_parameter, group_code, parameter_code))
            else :
                self.parameter_via_group_menu[group_code] = tk.Label(self.parameter_selection_frame, text='')

        # Time unit fields
        self.time_unit_menu = tk.OptionMenu(self.time_unit_frame, self.time_unit_text, *self.time_unit_selection)
        self.time_unit_menu.config(highlightthickness=0, anchor=tk.W)
        self.time_unit_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.time_unit_selection) :
            self.time_unit_menu['menu'].entryconfigure(i, command=(select_time_unit, selection))
        # Dynamic time unit fields
        self.time_unit_months_menu = tk.OptionMenu(self.time_unit_frame, self.time_unit_months_text, *self.time_unit_months_selection)
        self.time_unit_months_menu.config(highlightthickness=0, anchor=tk.W)
        self.time_unit_months_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.time_unit_months_selection) :
            self.time_unit_months_menu['menu'].entryconfigure(i, command=(select_time_unit, selection, 'months'))
        self.time_unit_seasons_menu = tk.OptionMenu(self.time_unit_frame, self.time_unit_seasons_text, *self.time_unit_seasons_selection)
        self.time_unit_seasons_menu.config(highlightthickness=0, anchor=tk.W)
        self.time_unit_seasons_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.time_unit_seasons_selection) :
            self.time_unit_seasons_menu['menu'].entryconfigure(i, command=(select_time_unit, selection, 'seasons'))
        self.time_unit_other_label = tk.Label(self.time_unit_frame, textvariable=self.time_unit_other_text)

        # Arrange fields on frame with labels
        row = 1
        tk.Label(self.parameter_selection_frame, text='Parameter:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.parameter_group_menu.grid(row=row, column=1, sticky=tk.W+tk.E, padx=0, pady=5)
        for group in self.parameter_via_group_codes :
            self.parameter_via_group_menu[group].grid(row=row, column=2, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
            self.parameter_via_group_menu[group].grid_remove()
        self.current_parameter_group_field = self.parameter_via_group_menu[self.parameter_group_codes[0]]
        self.current_parameter_group_field.grid()
        row = 2
        tk.Label(self.time_unit_frame, text='Time unit:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.time_unit_menu.grid(row=row, column=1, sticky=tk.W+tk.E, padx=0, pady=5)
        self.time_unit_seasons_menu.grid(row=row, column=2, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        self.time_unit_seasons_menu.grid_remove()
        self.time_unit_other_label.grid(row=row, column=2, columnspan=2, sticky=tk.NW+tk.SW, padx=5, pady=5)
        self.time_unit_other_label.grid_remove()
        self.time_unit_months_menu.grid(row=row, column=2, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        self.current_time_unit_field = self.time_unit_months_menu

        # Potentially restrict parameters and time units
        self.restrictParameters()
        self.restrictTimeUnit()

        #self.parameter_selection_frame.grid(row=1, column=0, sticky=tk.NW+tk.SE, padx=5, pady=0)

    # GUI for Step 3: Region Selection
    def createRegionSelectionFrame(self) :

        step_number = self.process_step['parameter_selection']['number']
        #self.region_selection_frame = tk.LabelFrame(self, text='Step '+step_number+': Region Selection', padx=10, pady=5)
        self.region_selection_frame = self.main_frame

        # Region selection lists
        self.region_codes = ['globe', 'land', 'land-0-21KBP', 'ocean', 'ocean-0-21KBP', 'northern-hemisphere', 'southern-hemisphere', 'equatorial-pacific', 'n3', 'n3-4', 'n4',
                             'usa', 'canada', 'mexico', 'brazil', 'africa', 'europe', 'india', 'china', 'japan', 'australia-nz', 'central-asia',
                             'middle-east', 'east-former-soviet-union', 'west-former-soviet-union', 'rola', 'south-east-asia', 'west-pacific',
                             'alaska', 'greenland', 'antarctica', 'arctic-islands']
        self.region_codes[5:] = sorted(self.region_codes[5:])
        self.region_codes.append('user-defined')
        self.region_code_map = {}
        self.region_is_time_dependent = {}
        self.region_selection = []
        for region_code in self.region_codes :
            if region_code == 'globe' :
                region_name = 'Global'
            elif region_code in ['usa', 'rola'] :
                region_name = region_code.upper()
            elif region_code in ['n3-4'] :
                region_name = region_code.title().replace('-', '.')
            elif region_code == 'australia-nz' :
                region_name = 'Australia/NZ'
            elif region_code in ['land', 'ocean'] :
                region_name = region_code.title() + ' (fixed)'
            elif region_code in ['land-0-21KBP'] :
                region_name = 'Land (time dependent)'
            elif region_code in ['ocean-0-21KBP'] :
                region_name = 'Ocean (time dependent)'
            else :
                region_name = region_code.replace('-', ' ').title()
            self.region_code_map[region_code] = region_name
            if region_code in ['land-0-21KBP', 'ocean-0-21KBP'] :
                self.region_is_time_dependent[region_code] = True
            else :
                self.region_is_time_dependent[region_code] = False
            self.region_selection.append(region_name)
        self.region_mask = self.data_file_helper.loadRegionMask(self.region_codes[0])
        self.current_region = self.region_codes[0]
        self.current_user_defined_region_mask = self.region_mask*0

        # Region bounding box
        self.region_bounding_box = {}
        self.region_bounding_box['globe'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['land'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['ocean'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['land-0-21KBP'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['ocean-0-21KBP'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['northern-hemisphere'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['southern-hemisphere'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['equatorial-pacific'] = { 'centre': 180, 'lat' : [-30,30], 'lon' : [125,300], 'grid' : 10 }
        self.region_bounding_box['n3'] = { 'centre': 180, 'lat' : [-30,30], 'lon' : [125,300], 'grid' : 10 }
        self.region_bounding_box['n3-4'] = { 'centre': 180, 'lat' : [-30,30], 'lon' : [125,300], 'grid' : 10 }
        self.region_bounding_box['n4'] = { 'centre': 180, 'lat' : [-30,30], 'lon' : [125,300], 'grid' : 10 }
        self.region_bounding_box['usa'] = { 'centre': 0, 'lat' : [15,60], 'lon' : [-130,-55], 'grid' : 10 }
        self.region_bounding_box['canada'] = { 'centre': 0, 'lat' : [35,80], 'lon' : [-150,-45], 'grid' : 10 }
        self.region_bounding_box['mexico'] = { 'centre': 0, 'lat' : [5,40], 'lon' : [-125,-80], 'grid' : 10 }
        self.region_bounding_box['brazil'] = { 'centre': 0, 'lat' : [-45,15], 'lon' : [-80,-25], 'grid' : 10 }
        self.region_bounding_box['africa'] = { 'centre': 0, 'lat' : [-40,40], 'lon' : [-20,55], 'grid' : 10 }
        self.region_bounding_box['europe'] = { 'centre': 0, 'lat' : [30,75], 'lon' : [-25,40], 'grid' : 10 }
        self.region_bounding_box['india'] = { 'centre': 0, 'lat' : [0,45], 'lon' : [60,100], 'grid' : 10 }
        self.region_bounding_box['china'] = { 'centre': 0, 'lat' : [15,60], 'lon' : [70,140], 'grid' : 10 }
        self.region_bounding_box['japan'] = { 'centre': 0, 'lat' : [25,50], 'lon' : [125,150], 'grid' : 10 }
        self.region_bounding_box['australia-nz'] = { 'centre': 180, 'lat' : [-50,-5], 'lon' : [110,185], 'grid' : 10 }
        self.region_bounding_box['central-asia'] = { 'centre': 0, 'lat' : [20,60], 'lon' : [35,120], 'grid' : 10 }
        self.region_bounding_box['middle-east'] = { 'centre': 0, 'lat' : [10,45], 'lon' : [30,65], 'grid' : 10 }
        self.region_bounding_box['east-former-soviet-union'] = { 'centre': 180, 'lat' : [40,85], 'lon' : [55,195], 'grid' : 10 }
        self.region_bounding_box['west-former-soviet-union'] = { 'centre': 0, 'lat' : [40,80], 'lon' : [15,65], 'grid' : 10 }
        self.region_bounding_box['rola'] = { 'centre': 0, 'lat' : [-60,30], 'lon' : [-95,-45], 'grid' : 10 }
        self.region_bounding_box['south-east-asia'] = { 'centre': 0, 'lat' : [-15,35], 'lon' : [65,155], 'grid' : 10 }
        self.region_bounding_box['west-pacific'] = { 'centre': 180, 'lat' : [-35,25], 'lon' : [130,240], 'grid' : 10 }
        self.region_bounding_box['alaska'] = { 'centre': 180, 'lat' : [50,75], 'lon' : [190,225], 'grid' : 10 }
        self.region_bounding_box['greenland'] = { 'centre': 0, 'lat' : [55,90], 'lon' : [-75,-10], 'grid' : 10 }
        self.region_bounding_box['antarctica'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }
        self.region_bounding_box['arctic-islands'] = { 'centre': 0, 'lat' : [55,85], 'lon' : [-130,-55], 'grid' : 10 }
        self.region_bounding_box['user-defined'] = { 'centre': 0, 'lat' : [-90,90], 'lon' : [-180,180], 'grid' : 10 }

        # Other parameters for regions

        # Parameter text variables
        self.region_selection_text = tk.StringVar()
        self.region_selection_text.set(self.region_selection[0])
        self.view_edit_region_button_text = tk.StringVar(value='View Region')

        # Register validation and selection behaviour methods
        select_region = self.region_selection_frame.register(self.selectRegion)
        forced_shift_focus = self.region_selection_frame.register(self.shiftFocus)

        # Entry/selection fields
        self.region_selection_menu = tk.OptionMenu(self.region_selection_frame, self.region_selection_text, *self.region_selection)
        self.region_selection_menu.config(highlightthickness=0, anchor=tk.W)
        self.region_selection_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.region_codes) :
            self.region_selection_menu['menu'].entryconfigure(i, command=(select_region, selection))
        self.view_edit_region_button = tk.Button(self.region_selection_frame, textvariable=self.view_edit_region_button_text, state=tk.NORMAL, command=self.viewEditRegion)

        # Arrange fields on frame with labels
        row = 3
        tk.Label(self.region_selection_frame, text='Region:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.region_selection_menu.grid(row=row, column=1, sticky=tk.W+tk.E, padx=0, pady=5)
        self.view_edit_region_button.grid(row=row, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)

        #self.parameter_selection_frame.grid(row=1, column=0, sticky=tk.NW+tk.SE, padx=5, pady=0)

    # GUI for Step 4: Period
    def createPeriodIntervalFrame(self) :

        step_number = self.process_step['period_interval']['number']
        #self.data_type_frame = tk.LabelFrame(self, text='Step '+step_number+': Data Type', padx=10, pady=5)
        self.period_interval_frame = self.main_frame

        # Period and interval lists
        self.period_postfix_keys = ['BP', 'AD']
        self.period_postfix_selection = ['Before Present: <=1950', 'Anno Domini: 1951-1989']

        # Parameter text variables
        self.period_text = { 'from' : tk.StringVar(), 'until' : tk.StringVar() }
        self.period_postfix_text = { 'from' : tk.StringVar(), 'until' : tk.StringVar() }
        self.period_postfix_text['from'].set(self.period_postfix_keys[1])
        self.period_postfix_text['until'].set(self.period_postfix_keys[1])
        self.interval_step_text = tk.StringVar()
        self.interval_size_text = tk.StringVar()
        self.current_interval_steps_text = tk.StringVar()
        
        # Register validation and selection behaviour methods
        validate_period = self.period_interval_frame.register(self.validatePeriod)
        period_spinbox_arrow_press = self.period_interval_frame.register(self.periodSpinboxArrowPress)
        select_period_postfix = self.period_interval_frame.register(self.selectPeriodPostfix)
        validate_interval_step = self.period_interval_frame.register(self.validateIntervalStep)
        validate_interval_size = self.period_interval_frame.register(self.validateIntervalSize)
        interval_step_spinbox_arrow_press = self.period_interval_frame.register(self.intervalStepSpinboxArrowPress)
        interval_size_spinbox_arrow_press = self.period_interval_frame.register(self.intervalSizeSpinboxArrowPress)
        forced_shift_focus = self.period_interval_frame.register(self.shiftFocus)

        # Entry/selection fields
        period_from_frame = tk.Frame(self.period_interval_frame)
        period_until_frame = tk.Frame(self.period_interval_frame)
        interval_step_frame = tk.Frame(self.period_interval_frame)
        interval_size_frame = tk.Frame(self.period_interval_frame)

        self.period_ranges = { 'BP' : { 'min' : 0, 'max' : 22000, 'max-entry' : 21000 }, 'AD' : { 'min' : 1, 'max' : 1989 } }
        self.current_period_values = { 'from' : range(0, 1969, 20), 'until' : range(1940, 1989, 20) }
        self.period_bp_range_for_all_months = 1000 # used to avoid memory problems caused by 22000 spinbox values
        self.previous_period_text_value = { 'from' : '1920', 'until' : '1980' }
        self.previous_period_changed_via = { 'from' : 'forced', 'until' : 'forced' }
        self.current_valid_period_value = { 'from' : 1920, 'until' : 1980 }
        self.period_entry = {}
        self.period_entry['from'] = tk.Spinbox(period_from_frame, textvariable=self.period_text['from'], values=tuple(map(str, self.current_period_values['from'])), width=6, justify=tk.CENTER)
        self.period_entry['from'].config(validate='all', validatecommand=(validate_period, '%P', '%V', 'from'))
        self.period_entry['from'].config(command=(period_spinbox_arrow_press, 'from'))
        self.period_entry['until'] = tk.Spinbox(period_until_frame, textvariable=self.period_text['until'], values=tuple(map(str, self.current_period_values['until'])), width=6, justify=tk.CENTER)
        self.period_entry['until'].config(validate='all', validatecommand=(validate_period, '%P', '%V', 'until'))
        self.period_entry['until'].config(command=(period_spinbox_arrow_press, 'until'))

        self.period_postfix_menu = {}
        self.period_postfix_menu['from'] = tk.OptionMenu(period_from_frame, self.period_postfix_text['from'], *self.period_postfix_selection)
        self.period_postfix_menu['until'] = tk.OptionMenu(period_until_frame, self.period_postfix_text['until'], *self.period_postfix_selection)
        #self.period_postfix_menu['until'] = tk.Menubutton(period_until_frame, textvariable=self.period_postfix_text['until']) #, relief=tk.RAISED, bd=2)
        self.period_postfix_menu['from'].config(highlightthickness=0, anchor=tk.W)
        self.period_postfix_menu['until'].config(highlightthickness=0, anchor=tk.W)
        self.period_postfix_menu['from']['menu'].config(postcommand=(forced_shift_focus, True, 'from'))
        self.period_postfix_menu['until']['menu'].config(postcommand=(forced_shift_focus, True, 'until'))
        for i, selection in enumerate(self.period_postfix_keys) :
            self.period_postfix_menu['from']['menu'].entryconfigure(i, command=(select_period_postfix, 'from', selection))
            self.period_postfix_menu['until']['menu'].entryconfigure(i, command=(select_period_postfix, 'until', selection))
        self.period_postfix_menu['until']['menu'].entryconfigure(0, state=tk.DISABLED)

        self.interval_step_range = { 'min' : 5, 'max' : 10000 }
        self.interval_step_values = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
        self.current_interval_step_values = [5, 10, 20, 50]
        self.current_valid_interval_step_value = 20
        self.previous_interval_step_text_value = '20'
        self.interval_step_entry = tk.Spinbox(interval_step_frame, textvariable=self.interval_step_text, values=tuple(map(str, self.current_interval_step_values)), width=6, justify=tk.CENTER)
        self.interval_step_entry.config(validate='all', validatecommand=(validate_interval_step, '%P', '%V'))
        self.interval_step_entry.config(command=(interval_step_spinbox_arrow_press))
        self.current_interval_steps = 3

        self.interval_size_range = { 'min' : 5, 'max' : 100 }
        self.interval_size_values = [5, 10, 20, 50, 100]
        self.current_interval_size_values = [5, 10, 20]
        self.current_valid_interval_size_value = 20
        self.previous_interval_size_text_value = '20'
        self.interval_size_entry = tk.Spinbox(interval_size_frame, textvariable=self.interval_size_text, values=tuple(map(str, self.current_interval_size_values)), width=6, justify=tk.CENTER)
        self.interval_size_entry.config(validate='all', validatecommand=(validate_interval_size, '%P', '%V'))
        self.interval_size_entry.config(command=(interval_size_spinbox_arrow_press))

        # Arrange fields on frame with labels
        row = 4
        tk.Label(self.period_interval_frame, text='Period from:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.period_entry['from'].grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.period_postfix_menu['from'].grid(row=0, column=1, sticky=tk.W, padx=5, pady=0)
        period_from_frame.grid(row=row, column=1, sticky=tk.NW+tk.SE, padx=0, pady=5)
        row = 4
        tk.Label(self.period_interval_frame, text='Interval step:').grid(row=row, column=2, sticky=tk.NW+tk.SW, padx=3, pady=0)
        self.interval_step_entry.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        tk.Label(interval_step_frame, text='years').grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=5)#, pady=4)
        interval_step_frame.grid(row=row, column=3, sticky=tk.NW+tk.SW, padx=0, pady=5)
        row = 5
        tk.Label(self.period_interval_frame, text='Period until:').grid(row=row, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.period_entry['until'].grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.period_postfix_menu['until'].grid(row=0, column=1, sticky=tk.W, padx=5, pady=0)
        period_until_frame.grid(row=row, column=1, sticky=tk.NW+tk.SE, padx=0, pady=5)
        row = 5
        tk.Label(self.period_interval_frame, text='Interval size:').grid(row=row, column=2, sticky=tk.NW+tk.SW, padx=3, pady=0)
        self.interval_size_entry.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        tk.Label(interval_size_frame, text='years').grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=5)#, pady=4)
        interval_size_frame.grid(row=row, column=3, sticky=tk.NW+tk.SW, padx=0, pady=5)
        row = 8
        tk.Label(self.period_interval_frame, textvariable=self.current_interval_steps_text).grid(row=row, column=0, columnspan=4, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.period_interval_frame.columnconfigure(0, weight=1)
        self.period_interval_frame.columnconfigure(1, weight=1000)
        self.period_interval_frame.columnconfigure(2, weight=1)
        self.period_interval_frame.columnconfigure(3, weight=1000)

        #self.data_type_frame.grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=5, pady=5)

    # Initilisation for Step 4: Set initial Period Interval Values
    def setInitialPeriodIntervalValues(self) :
        self.period_text['from'].set(str(self.current_valid_period_value['from']))
        self.period_text['until'].set(str(self.current_valid_period_value['until']))
        self.interval_step_text.set(str(self.current_valid_interval_step_value))
        self.interval_size_text.set(str(self.current_valid_interval_size_value))
        self.updateCurrentIntervalSteps()

    # GUI for Step 5: Delta
    def createDeltaFrame(self) :

        step_number = self.process_step['delta']['number']
        #generation_frame = tk.LabelFrame(self, text='Step '+step_number+': Downscale Generation', padx=10, pady=5)
        self.delta_frame = self.main_frame

        # Delta reference period lists
        self.delta_reference_period_codes = ['previous', 'next', 'present-day', 'oldest-record', 'user-defined']
        self.delta_reference_value = { 'previous' : { 'year' : 1920, 'postfix' : 'AD' }, 'next' : { 'year' : 1980, 'postfix' : 'AD' },
                                       'present-day' : { 'year' : 1980, 'postfix' : 'AD' }, 'oldest-record' : { 'year' : 21000, 'postfix' : 'BP' },
                                       'user-defined' : { 'year' : 1900, 'postfix' : 'AD' } }
        self.delta_reference_interval_pre_text = { 'previous' : '1920 AD', 'next' : '1980 AD', 'present-day' : '1980 AD', 'oldest-record' : '21000 BP', 'user-defined' : '' }
        self.delta_reference_interval_post_text = { 'previous' : ' (from)', 'next' : ' (until)', 'present-day' : ' (present day)', 'oldest-record' : ' (oldest record)', 'user-defined' : 'User-defined' }
        self.utilise_delta_pre_text = { 'view' : 'View', 'files' : 'Generate' }
        self.utilise_delta_post_text = ' change relative to:'
        self.delta_as_percent_parameters = { 'temperature' : ['isothermality', 'temperature-seasonality'], 'precipitation' : ['mean-precipitation', 'precipitation-seasonality'], 'humidity' : [], 'sea-level-pressure' : [], 'southern-oscillation' : [] }
        self.delta_as_percent_parameters_defaults = { 'temperature' : { 'isothermality' : True, 'temperature-seasonality' : True },
                                                      'precipitation' : { 'mean-precipitation' : True, 'precipitation-seasonality' : True } }

        # Delta text variables
        self.utilise_delta = tk.IntVar()
        self.utilise_delta.set(1)
        self.utilise_delta_text = tk.StringVar()
        self.utilise_delta_text.set(self.utilise_delta_pre_text['view'] + self.utilise_delta_post_text)
        self.delta_as_percent = tk.IntVar()
        self.delta_reference_interval_text = tk.StringVar()
        self.delta_reference_interval_selection = []
        for code in self.delta_reference_period_codes :
            self.delta_reference_interval_selection.append(self.delta_reference_interval_pre_text[code] + self.delta_reference_interval_post_text[code])
        self.delta_reference_interval_text.set(self.delta_reference_interval_selection[0])
        self.delta_user_defined_reference_text = { 'year' : tk.StringVar(), 'postfix' : tk.StringVar() }
        
        # Register validation and selection behaviour methods
        select_delta_reference_interval = self.delta_frame.register(self.selectDeltaReferenceInterval)
        forced_shift_focus = self.delta_frame.register(self.shiftFocus)
        validate_delta_user_defined_reference = self.delta_frame.register(self.validateDeltaUserDefinedReference)
        select_delta_user_defined_reference_postfix = self.delta_frame.register(self.selectDeltaUserDefinedReferencePostfix)

        # Entry/selection fields
        delta_select_frame = tk.Frame(self.delta_frame)
        self.delta_checkbox = tk.Checkbutton(delta_select_frame, variable=self.utilise_delta, padx=0, command=self.deltaSelection)
        self.delta_as_percent_checkbox = tk.Checkbutton(delta_select_frame, variable=self.delta_as_percent, text='Use % change', padx=0, state=tk.NORMAL, command=self.deltaAsPercentSelection)
        delta_reference_frame = tk.Frame(self.delta_frame)
        self.delta_reference_interval_menu = tk.OptionMenu(delta_reference_frame, self.delta_reference_interval_text, *self.delta_reference_interval_selection)
        self.delta_reference_interval_menu.config(highlightthickness=0, anchor=tk.W, state=tk.NORMAL)
        self.delta_reference_interval_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, code in enumerate(self.delta_reference_period_codes) :
            self.delta_reference_interval_menu['menu'].entryconfigure(i, command=(select_delta_reference_interval, code))
        #self.delta_reference_interval_menu['menu'].entryconfigure(self.delta_reference_period_codes.index('next'), state=tk.DISABLED)

        self.current_delta_user_defined_reference_values = range(0, 1989, 20)
        self.previous_delta_user_defined_reference_text_value = str(self.delta_reference_value['user-defined']['year'])
        self.previous_delta_user_defined_reference_changed_via = 'forced'
        self.current_valid_delta_user_defined_reference_value = self.delta_reference_value['user-defined']['year']
        
        self.delta_user_defined_reference_frame = tk.Frame(delta_reference_frame)
        self.delta_user_defined_reference_entry = tk.Spinbox(self.delta_user_defined_reference_frame, textvariable=self.delta_user_defined_reference_text['year'], values=tuple(map(str, self.current_delta_user_defined_reference_values)), width=6, justify=tk.CENTER)
        self.delta_user_defined_reference_entry.config(validate='all', validatecommand=(validate_delta_user_defined_reference, '%P', '%V'))
        self.delta_user_defined_reference_entry.config(command=self.deltaUserDefinedReferenceSpinboxArrowPress)
        self.delta_user_defined_reference_postfix_menu = tk.OptionMenu(self.delta_user_defined_reference_frame, self.delta_user_defined_reference_text['postfix'], *self.period_postfix_selection)
        self.delta_user_defined_reference_postfix_menu.config(highlightthickness=0, anchor=tk.W)
        self.delta_user_defined_reference_postfix_menu['menu'].config(postcommand=(forced_shift_focus, True, 'delta-user-defined-reference'))
        for i, selection in enumerate(self.period_postfix_keys) :
            self.delta_user_defined_reference_postfix_menu['menu'].entryconfigure(i, command=(select_delta_user_defined_reference_postfix, selection))
        self.delta_user_defined_reference_text['postfix'].set(self.delta_reference_value['user-defined']['postfix'])
        self.delta_user_defined_reference_text['year'].set(str(self.delta_reference_value['user-defined']['year']))

        # Arrange fields on frame with labels
        row = 6
        self.delta_checkbox.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        tk.Label(delta_select_frame, textvariable=self.utilise_delta_text).grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.delta_as_percent_checkbox.grid(row=1, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.deltaAsPercentInclusion()
        delta_select_frame.grid(row=row, column=0, columnspan=2, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.delta_reference_interval_menu.grid(row=0, column=0, sticky=tk.W, padx=0, pady=0)
        self.delta_user_defined_reference_entry.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=5, pady=0)
        self.delta_user_defined_reference_postfix_menu.grid(row=0, column=1, sticky=tk.W, padx=0, pady=0)
        self.delta_user_defined_reference_frame.grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.delta_user_defined_reference_frame.grid_remove()
        delta_reference_frame.grid(row=row, column=2, columnspan=2, sticky=tk.NW+tk.SW, padx=5, pady=5)

    # GUI for Step 6: Bias Correction
    def createBiasCorrectionFrame(self) :

        step_number = self.process_step['bias_correction']['number']
        #bias_correction_frame = tk.LabelFrame(self, text='Step '+step_number+': Downscale Generation', padx=10, pady=5)
        self.bias_correction_frame = self.main_frame

        # Delta text variables
        self.utilise_bias_correction = tk.IntVar()
        self.utilise_bias_correction.set(0)
        self.enabled_bias_correction_set = True # initial setting when enabled
        
        # Register validation and selection behaviour methods
        forced_shift_focus = self.bias_correction_frame.register(self.shiftFocus)

        # Entry/selection fields
        bias_correction_select_frame = tk.Frame(self.bias_correction_frame)
        self.bias_correction_checkbox = tk.Checkbutton(bias_correction_select_frame, variable=self.utilise_bias_correction, padx=0, command=self.biasCorrectionSelection)
        self.bias_correction_checkbox.configure(state=tk.DISABLED)
        self.bias_correction_label = tk.Label(bias_correction_select_frame, text='Apply model bias correction')
        self.bias_correction_label.configure(state=tk.DISABLED)

        # Arrange fields on frame with labels
        row = 7
        self.bias_correction_checkbox.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.bias_correction_label.grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        bias_correction_select_frame.grid(row=row, column=0, columnspan=2, sticky=tk.NW+tk.SW, padx=0, pady=0)

    # GUI for Step 7: Generation
    def createGenerationFrame(self) :

        step_number = self.process_step['generation']['number']
        #generation_frame = tk.LabelFrame(self, text='Step '+step_number+': Downscale Generation', padx=10, pady=5)
        self.generation_frame = self.main_frame
        self.generation_options = { 'view' : { 'map' : 'View map grid plots', 'series' : 'View series plot' },
                                    'files' : { 'map' : 'Generate the grid data files', 'series' : 'Generate the series data file' } }

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # View
        self.view_frame = tk.Frame(self.generation_frame)
        self.view_button = tk.Button(self.view_frame, text='View', state=tk.NORMAL, command=self.viewPlot)
        self.view_label_text = tk.StringVar(value=self.generation_options['view']['map'])
        self.view_label = tk.Label(self.view_frame, textvariable=self.view_label_text, justify=tk.LEFT)
        self.view_button.grid(row=0, column=0, sticky=tk.W, padx=0, pady=5)
        tk.Label(self.view_frame, text=' :').grid(row=0, column=1, padx=0, pady=5)
        self.view_label.grid(row=0, column=2, sticky=tk.NW+tk.SW, padx=0, pady=5)    

        # File generation
        self.file_frame = tk.Frame(self.generation_frame)
        self.file_generation_completed = False

        # Data file type
        self.data_file_type_keys = ['csv', 'ascii', 'esri_ascii', 'netcdf']
        self.data_file_type_selection = ['CSV', 'ASCII', 'ESRI ASCII', 'NetCDF']
        self.data_file_types_for_data_type = { 'map' : ['csv', 'ascii', 'esri_ascii', 'netcdf'],
                                               'series' : ['csv', 'ascii', 'netcdf'] }
        self.data_file_type_text = tk.StringVar()
        self.data_file_type_text.set(self.data_file_type_selection[0])
        select_data_file_type = self.data_type_frame.register(self.selectDataFileType)
        forced_shift_focus = self.data_type_frame.register(self.shiftFocus)        
        self.data_file_type_menu = tk.OptionMenu(self.file_frame, self.data_file_type_text, *self.data_file_type_selection)
        self.data_file_type_menu.config(highlightthickness=0, anchor=tk.W)
        self.data_file_type_menu['menu'].config(postcommand=(forced_shift_focus, True))
        for i, selection in enumerate(self.data_file_type_keys) :
            self.data_file_type_menu['menu'].entryconfigure(i, command=(select_data_file_type, selection))
            if selection in self.data_file_types_for_data_type['map'] :
                self.data_file_type_menu['menu'].entryconfigure(i, state=tk.NORMAL)
            else :
                self.data_file_type_menu['menu'].entryconfigure(i, state=tk.DISABLED)
        tk.Label(self.file_frame, text='Data file type:').grid(row=0, column=0, columnspan=2, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.data_file_type_menu.grid(row=0, column=2, sticky=tk.W, padx=0, pady=5)        

        # Generation directory
        location_descr = 'Select location for generated files'
        if tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory']) :
            generate_directory = self.data_file_helper.splitPath(tool_option_values['default_file_generation_directory'])
            location_descr = 'File generation in \"' + generate_directory['name'] + '\"'
        self.generation_directory_button = tk.Button(self.file_frame, text='Select Directory', state=tk.NORMAL, command=self.selectGenerationDirectory)
        self.generation_directory_label_text = tk.StringVar(value=location_descr)
        self.generation_directory_label = tk.Label(self.file_frame, textvariable=self.generation_directory_label_text, justify=tk.LEFT)
        self.generation_directory_button.grid(row=1, column=0, sticky=tk.W+tk.E, padx=0, pady=5)
        tk.Label(self.file_frame, text=' :').grid(row=1, column=1, padx=0, pady=5)
        self.generation_directory_label.grid(row=1, column=2, sticky=tk.NW+tk.SW, padx=0, pady=5)

        # Generate
        self.generate_button = tk.Button(self.file_frame, text='Generate', state=tk.DISABLED, command=self.generateDataFiles)
        if tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory']) :
            self.generate_button.configure(state=tk.NORMAL)
        self.generate_label_text = tk.StringVar(value=self.generation_options['files']['map'])
        self.generate_label = tk.Label(self.file_frame, textvariable=self.generate_label_text, justify=tk.LEFT)
        self.generate_button.grid(row=2, column=0, sticky=tk.W+tk.E, padx=0, pady=5)
        tk.Label(self.file_frame, text=' :').grid(row=2, column=1, padx=0, pady=5)
        self.generate_label.grid(row=2, column=2, sticky=tk.NW+tk.SW, padx=0, pady=5)

        # Generation status bar
        self.generation_status_options = { 'view' : { 'data' : 'Loading data...', 'plot' : 'Generating plot...' },
                                           'files' : { 'map' : { 'data' : 'Loading data...', 'file' : 'Generating data files...' },
                                                       'series' : { 'data' : 'Loading data...', 'file' : 'Generating data file...' } } }
        self.generation_status_times = { 'view' : { 'map' : 10, 'time-dependent' : 100, 'contours' : 5, 'masks' : 5, 'series' : 5 },
                                         'files' : { 'map' : 1, 'series' : 1 } }
        self.generation_status_bar = ttk.Progressbar(self.generation_frame, orient='horizontal', mode='determinate')

        # Add frames to grid
        row = 9
        self.file_frame.grid(row=row, column=0, columnspan=4, sticky=tk.NW+tk.SE, padx=0, pady=0)
        self.file_frame.grid_remove()
        self.view_frame.grid(row=row, column=0, columnspan=4, sticky=tk.NW+tk.SE, padx=0, pady=0)
        row = 10
        self.generation_status_bar.grid(row=row, column=0, columnspan=4, sticky=tk.NW+tk.SE, padx=0, pady=5)
        self.generation_status_bar.grid_remove()

        #generation_frame.grid(row=2, column=0, sticky=tk.NW+tk.SE, padx=5, pady=5)

    ## Menu Methods ################################################################################################################################################

    # Menu Method: Edit map options
    def editMapOptions(self) :
        #print 'TODO: editMapOptions'

        self.focus_set()
        
        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.validation_warning_pending = False
            return True

        # Create or update edit window
        if hasattr(self, 'edit_map_options_window') :
            if self.edit_map_options_window.children :
                self.edit_map_options_window.focus_set()
            else :
                self.edit_map_options_window.destroy()
                self.createMapOptionsWindow()
        else :
            self.createMapOptionsWindow()        
        
    # Menu Method: Create Map Options Window
    def createMapOptionsWindow(self) :
        #print 'TODO: createMapOptionsWindow'

        # Create the view LHS distribution window
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            parent = self.view_climate_data_window
        else :
            parent = self
        self.edit_map_options_window = tk.Toplevel(parent)
        self.edit_map_options_window.title('Edit Map Options')
        self.edit_map_options_window.transient(parent)
        self.edit_map_options_window.focus_set()

        # Create Colour Scheme Selection from codes ['fixed_range', '90%_range']
        # self.map_colour_scheme, self.map_colour_schemes and self.map_colour_scheme_selection defined in initialise method
        tk.Label(self.edit_map_options_window, text='Colour scheme:', padx=0).grid(row=0, column=0, columnspan=2, sticky=tk.NW+tk.SW, padx=5, pady=0)
        select_map_colour_scheme = self.edit_map_options_window.register(self.selectMapColourScheme) # Register selection behaviour method
        self.map_colour_scheme_text = tk.StringVar(value=self.map_colour_scheme_selection[self.map_colour_schemes.index(self.map_colour_scheme)])
        self.map_colour_scheme_menu = tk.OptionMenu(self.edit_map_options_window, self.map_colour_scheme_text, *self.map_colour_scheme_selection)
        self.map_colour_scheme_menu.config(highlightthickness=0, anchor=tk.W)
        for i, selection in enumerate(self.map_colour_schemes) :
            self.map_colour_scheme_menu['menu'].entryconfigure(i, command=(select_map_colour_scheme, selection))
        self.map_colour_scheme_menu.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        #tk.Label(self.edit_map_options_window, text='', padx=0).grid(row=0, column=3, sticky=tk.NW+tk.SW, padx=0, pady=0)

        # Create Map Colour Palette Selection
        tk.Label(self.edit_map_options_window, text='Colour palette:', padx=0).grid(row=1, column=0, columnspan=2, sticky=tk.NW, padx=5, pady=0)
        tk.Label(self.edit_map_options_window, text='', padx=0).grid(row=2, column=0, sticky=tk.NW, padx=10, pady=0)
        #self.auto_map_colour_palette_int = tk.IntVar(value=int(self.auto_map_colour_palette))
        #self.auto_map_colour_palette_checkbox = tk.Checkbutton(self.edit_map_options_window, text='Use the default colour palette for the selected parameter', variable=self.auto_map_colour_palette_int, padx=0, command=self.setAutoMapColourPalette)
        #self.auto_map_colour_palette_checkbox.grid(row=2, column=1, columnspan=2, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.edit_map_options_frame = tk.Frame(self.edit_map_options_window, padx=0, pady=0)
        self.edit_map_options_colourbar = {}
        self.edit_map_options_radiobutton = {}
        self.createMapColourSelection()

        # Colour Palette Options
        tk.Label(self.edit_map_options_frame, text='Colour palette options:', padx=0).grid(row=len(self.colour_palettes), column=0, columnspan=2, sticky=tk.NW, padx=5, pady=0)
        self.reverse_map_colour_palette_int = tk.IntVar(value=int(self.reverse_map_colour_palette))
        self.reverse_map_colour_palette_checkbox = tk.Checkbutton(self.edit_map_options_frame, text='Reverse colour palettes', variable=self.reverse_map_colour_palette_int, padx=0, command=self.reverseColourPalettes)
        self.reverse_map_colour_palette_checkbox.grid(row=len(self.colour_palettes)+1, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        self.map_colour_boundary_lines_int = tk.IntVar(value=int(self.map_colour_boundary_lines))
        self.map_colour_boundary_lines_checkbox = tk.Checkbutton(self.edit_map_options_frame, text='Include boundary lines', variable=self.map_colour_boundary_lines_int, padx=0, command=self.setMapColourBoundaryLines)
        self.map_colour_boundary_lines_checkbox.grid(row=len(self.colour_palettes)+2, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            zero_boundary_checkbox_state = tk.NORMAL
        else :
            zero_boundary_checkbox_state = tk.DISABLED
            self.map_colour_zero_boundary = False
        self.map_colour_zero_boundary_int = tk.IntVar(value=int(self.map_colour_zero_boundary))
        self.map_colour_zero_boundary_checkbox = tk.Checkbutton(self.edit_map_options_frame, text='Set zero boundary', variable=self.map_colour_zero_boundary_int, state=zero_boundary_checkbox_state, padx=0, command=self.setMapColourZeroBoundary)
        self.map_colour_zero_boundary_checkbox.grid(row=len(self.colour_palettes)+3, column=1, sticky=tk.NW+tk.SW, padx=0, pady=0)

        # Colour palette frame
        self.edit_map_options_frame.grid(row=2, column=1, columnspan=2, padx=0, pady=0, sticky=tk.NW+tk.SE)

        # Contours?
        self.use_contoured_grid_maps_int = tk.IntVar(value=int(self.use_contoured_grid_maps))
        self.use_contoured_grid_maps_checkbox = tk.Checkbutton(self.edit_map_options_window, text='Generate contours', variable=self.use_contoured_grid_maps_int, padx=0, command=self.setUseContouredGridMaps)
        self.use_contoured_grid_maps_checkbox.grid(row=3, column=0, columnspan=3, sticky=tk.NW+tk.SW, padx=5, pady=0)

        # Land boundaries?
        self.show_grid_map_land_boundaries_int = tk.IntVar(value=int(self.show_grid_map_land_boundaries))
        self.show_grid_map_land_boundaries_checkbox = tk.Checkbutton(self.edit_map_options_window, text='Show land boundaries', variable=self.show_grid_map_land_boundaries_int, padx=0, command=self.setShowGridMapLandBoundaries)
        self.show_grid_map_land_boundaries_checkbox.grid(row=4, column=0, columnspan=3, sticky=tk.NW+tk.SW, padx=5, pady=0)

        # Map grid lines/ticks
        # self.map_grid_include/s/_selection and self.map_grid_space/s/_selection defined in initialise method
        show_grid_lines_frame = tk.Frame(self.edit_map_options_window, padx=0, pady=0)
        # Show lines/ticks?
        self.show_map_grid_lines_int = tk.IntVar(value=int(self.show_map_grid_lines))
        self.show_map_grid_lines_checkbox = tk.Checkbutton(show_grid_lines_frame, text='Show map grid', variable=self.show_map_grid_lines_int, padx=0, command=self.setShowMapGridLines)
        self.show_map_grid_lines_checkbox.grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=5, pady=0)
        # Ticks or lines?
        select_map_grid_include = self.edit_map_options_window.register(self.selectMapGridInclude) # Register selection behaviour method
        self.map_grid_include_text = tk.StringVar(value=self.map_grid_include_selection[self.map_grid_includes.index(self.map_grid_include)])
        self.map_grid_include_menu = tk.OptionMenu(show_grid_lines_frame, self.map_grid_include_text, *self.map_grid_include_selection)
        self.map_grid_include_menu.config(highlightthickness=0, anchor=tk.W)
        for i, selection in enumerate(self.map_grid_includes) :
            self.map_grid_include_menu['menu'].entryconfigure(i, command=(select_map_grid_include, selection))
        self.map_grid_include_menu.grid(row=0, column=1, padx=0, pady=0, sticky=tk.W)
        # Grid spacing?
        select_map_grid_space = self.edit_map_options_window.register(self.selectMapGridSpace) # Register selection behaviour method
        if self.map_grid_space :
            map_grid_space = self.map_grid_space
        else :
            map_grid_space = self.region_bounding_box[self.current_region]['grid']                
        self.map_grid_space_text = tk.StringVar(value=self.map_grid_space_selection[self.map_grid_spaces.index(map_grid_space)])
        self.map_grid_space_menu = tk.OptionMenu(show_grid_lines_frame, self.map_grid_space_text, *self.map_grid_space_selection)
        self.map_grid_space_menu.config(highlightthickness=0, anchor=tk.W)
        for i, selection in enumerate(self.map_grid_spaces) :
            self.map_grid_space_menu['menu'].entryconfigure(i, command=(select_map_grid_space, selection))
        tk.Label(show_grid_lines_frame, text='at', padx=0).grid(row=0, column=2, sticky=tk.NW+tk.SW, padx=5, pady=0)
        self.map_grid_space_menu.grid(row=0, column=3, padx=0, pady=0, sticky=tk.W)
        tk.Label(show_grid_lines_frame, text='degree intervals', padx=0).grid(row=0, column=4, sticky=tk.NW+tk.SW, padx=5, pady=0)
        show_grid_lines_frame.grid(row=5, column=0, columnspan=3, sticky=tk.NW+tk.SW, padx=0, pady=5)

        # Update plot button and text
        self.map_options_update_includes = []
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.map_options_update_button = tk.Button(self.edit_map_options_window, text='Update Plot', state=tk.DISABLED, command=self.updateGridPlotsUsingOptions)
            self.map_options_update_button.grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
            self.updating_plot_status_text = tk.StringVar() # 'Updating plot ...'
            tk.Label(self.edit_map_options_window, textvariable=self.updating_plot_status_text).grid(row=6, column=2, sticky=tk.NE+tk.SE, padx=10, pady=0)

        self.edit_map_options_window.columnconfigure(0, weight=1)
        self.edit_map_options_window.columnconfigure(1, weight=1)
        self.edit_map_options_window.columnconfigure(2, weight=100)

    # Menu Method: Create Map Colour Selection
    def createMapColourSelection(self) :

        # Create axes instances
        cols = np.arange(0, 1.2, 0.1)
        rows = np.arange(0, 1.2, 0.1)
        cols, rows = np.meshgrid(cols,rows)
        data = np.zeros((11, 11))
        data[:] = cols[:11,:11]
        steps = np.arange(0.0, 1.2, 0.1)
        self.edit_map_options_figures = []
        self.edit_map_options_canvas = []
        self.edit_map_options_plot_axes = []

        # Determine palettes available
        available_colour_palettes = []
        for colour_palette in self.colour_palettes :
            if colour_palette in self.extended_colour_palettes :
                if (self.map_colour_zero_boundary or self.show_extended_colour_palettes_in_advance) and self.mapZeroBoundaryPermitted() :
                    available_colour_palettes.append(colour_palette)
                    self.updateExtendedColourMaps(colour_palette)
            else :
                available_colour_palettes.append(colour_palette)

        # Resolve boundary line widths
        if self.map_colour_boundary_lines :
            linewidths = np.ones_like(steps)*rcParams['lines.linewidth']*0.5
            if self.map_colour_zero_boundary and self.mapZeroBoundaryPermitted() :
                colour_scheme_boundaries = self.calculateColourSchemeBoundaries()
                zero_index, colour_scheme_boundaries = self.adjustColourSchemeZeroBoundaries(colour_scheme_boundaries)
                linewidths[zero_index] *= 3

        # Draw colour bars and choice radio buttons
        self.map_colour_palette_text = tk.StringVar(value=self.map_colour_palette)
        for i, colour_palette in enumerate(self.colour_palettes) :

            # Only draw when available
            if colour_palette in available_colour_palettes :

                # Create colour bar
                self.edit_map_options_figures.append(Figure(figsize=(4,0.3), frameon=False, linewidth=0.0, dpi=100, edgecolor='w'))
                self.edit_map_options_plot_axes.append(self.edit_map_options_figures[i].add_axes([0.0, 0.15, 0.97, 0.7]))
                if self.map_colour_boundary_lines :
                    cb = ColorbarBase(self.edit_map_options_plot_axes[i], orientation='horizontal', ticks=[], cmap=self.colourmaps[self.reverse_map_colour_palette][colour_palette], boundaries=steps, drawedges=True)
                    cb.dividers.set_linewidths(linewidths[1:-1])
                    if self.map_colour_zero_boundary and zero_index in [0,11] :
                        self.edit_map_options_plot_axes[i].set_xlim(left=-0.002)
                        zero_boundary_x_value = { 0 : 0, 11 : 1 }
                        vl = self.edit_map_options_plot_axes[i].axvline(zero_boundary_x_value[zero_index], color='k', linewidth=linewidths[zero_index])
                else :
                    ColorbarBase(self.edit_map_options_plot_axes[i], orientation='horizontal', ticks=[], cmap=self.colourmaps[self.reverse_map_colour_palette][colour_palette])

                # Plot the colorbars
                self.edit_map_options_canvas.append(FigureCanvasTkAgg(self.edit_map_options_figures[i], master=self.edit_map_options_frame))
                self.edit_map_options_canvas[i].show()
                self.edit_map_options_canvas[i].get_tk_widget().configure(borderwidth=0, highlightthickness=0)
                self.edit_map_options_canvas[i].get_tk_widget().grid(row=i, column=1, padx=0, pady=5, sticky=tk.NW+tk.SW) #.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                # Create new radio buttons
                if colour_palette in available_colour_palettes :
                    if colour_palette in self.extended_colour_palettes and not self.map_colour_zero_boundary :
                        map_colour_radiobutton_state = tk.DISABLED
                    else :
                        map_colour_radiobutton_state = tk.NORMAL
                    map_colour_radiobutton = tk.Radiobutton(self.edit_map_options_frame, text=None, variable=self.map_colour_palette_text, value=colour_palette, state=map_colour_radiobutton_state, padx=0, command=self.selectMapColourPalette)
                    map_colour_radiobutton.grid(row=i, column=0, sticky=tk.NW+tk.SW)

            # Remove existing colour bars and radio buttons
            if self.edit_map_options_colourbar.has_key(colour_palette) and self.edit_map_options_radiobutton.has_key(colour_palette) :
                self.edit_map_options_colourbar[colour_palette].grid_forget()
                self.edit_map_options_radiobutton[colour_palette].grid_forget()

            # Re-assign when available
            if colour_palette in available_colour_palettes : 
                self.edit_map_options_colourbar[colour_palette] = self.edit_map_options_canvas[i].get_tk_widget()
                self.edit_map_options_radiobutton[colour_palette] = map_colour_radiobutton

    # Menu Method: Map Zero Boundary Permitted?
    def mapZeroBoundaryPermitted(self, precheck=False) :
        if precheck or (hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map') :
            if self.map_colour_scheme == '90%_range' :
                if min(self.grid_plot_statistics['region']['percentile_5th']) <= 0 and max(self.grid_plot_statistics['region']['percentile_95th']) >= 0 :
                    return True
                else :
                    return False
            else : # fixed_range
                return True
        else :
            return False

    # Menu Method: Update Map Extended Colour Maps
    def updateExtendedColourMaps(self, colour_palette) :
        #print 'TODO: updateExtendedColourMaps'
        colour_scheme_boundaries = self.calculateColourSchemeBoundaries()
        zero_index, colour_scheme_boundaries = self.adjustColourSchemeZeroBoundaries(colour_scheme_boundaries)
        self.colourmaps[False][colour_palette] = LinearSegmentedColormap.from_list(colour_palette, self.colour_palette_lists[False][colour_palette][(11-zero_index):(22-zero_index)], N=11)
        self.colourmaps[True][colour_palette] = LinearSegmentedColormap.from_list(colour_palette, self.colour_palette_lists[True][colour_palette][(11-zero_index):(22-zero_index)], N=11)

    # Menu Method: Update Map Colour Selection
    def updateMapColourSelection(self) :
        self.createMapColourSelection()

    # Menu Method: Update Grid Plots using Options
    def updateGridPlotsUsingOptions(self) :
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.update_idletasks()
            self.map_options_update_button.configure(state=tk.DISABLED)
            self.updating_plot_status_text.set('Updating plot ...')
            self.update_idletasks()
            self.updateGridPlots(update=self.map_options_update_includes)
            self.update_idletasks()
            self.view_climate_data_window.after_idle(lambda: self.updating_plot_status_text.set(''))

    # Menu Method: Select Map Colour Scheme
    def selectMapColourScheme(self, selected) :
        self.map_colour_scheme_text.set(self.map_colour_scheme_selection[self.map_colour_schemes.index(selected)]) # needed as OptionMenu menu item commands have been overridden
        self.map_colour_scheme = selected
        if self.map_colour_zero_boundary and not self.mapZeroBoundaryPermitted() :
            self.map_colour_zero_boundary_int.set(0)
            self.map_colour_zero_boundary = False
            if self.map_colour_palette in self.extended_colour_palettes :
                self.map_colour_palette = self.colour_palettes[0]
        self.after_idle(lambda: self.updateMapColourSelection())
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if 'colours' not in self.map_options_update_includes :
                self.map_options_update_includes.append('colours')
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Select Map Colour Palette
    def selectMapColourPalette(self) :
        #print 'TODO: selectMapColourPalette'
        self.map_colour_palette = self.map_colour_palette_text.get()
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if 'colours' not in self.map_options_update_includes :
                self.map_options_update_includes.append('colours')
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Set Auto Map Colour Palette # NOT IN USE
    def setAutoMapColourPalette(self) :
        self.auto_map_colour_palette = bool(self.auto_map_colour_palette_int.get())
        if self.auto_map_colour_palette :
            print 'TODO: update palette settings'

    # Menu Method: Reverse Colour Palettes
    def reverseColourPalettes(self) :
        #print 'TODO: reverseColourPalettes'
        self.reverse_map_colour_palette = bool(self.reverse_map_colour_palette_int.get())
        self.after_idle(lambda: self.updateMapColourSelection())
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if 'colours' not in self.map_options_update_includes :
                self.map_options_update_includes.append('colours')
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Set Map Colour Boundary Lines
    def setMapColourBoundaryLines(self) :
        #print 'TODO: setMapColourBoundaryLines'
        self.map_colour_boundary_lines = bool(self.map_colour_boundary_lines_int.get())
        self.after_idle(lambda: self.updateMapColourSelection())
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if 'colours' not in self.map_options_update_includes :
                self.map_options_update_includes.append('colours')
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Set Map Colour Zero Boundary
    def setMapColourZeroBoundary(self) :
        #print 'TODO: setMapColourZeroBoundary'
        self.map_colour_zero_boundary = bool(self.map_colour_zero_boundary_int.get())
        if self.map_colour_palette in self.extended_colour_palettes and not self.map_colour_zero_boundary :
            self.map_colour_palette = self.colour_palettes[0]
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if self.map_colour_zero_boundary and not self.mapZeroBoundaryPermitted() :
                if min(self.grid_plot_statistics['region']['percentile_5th']) > 0 :
                    showwarning('Zero boundary irresolvable ', 'Set zero boundary option cannot be used because the 5th percentile value is greater than zero.\nPlease choose another color scheme.')
                elif max(self.grid_plot_statistics['region']['percentile_95th']) < 0 :
                    showwarning('Zero boundary irresolvable', 'Set zero boundary option cannot be used because the 95th percentile value is less than zero.\nPlease choose another color scheme.')
                self.map_colour_zero_boundary_int.set(0)
                self.map_colour_zero_boundary = False
            else :
                if 'colours' not in self.map_options_update_includes :
                    self.map_options_update_includes.append('colours')
                self.map_options_update_button.configure(state=tk.NORMAL)
        self.after_idle(lambda: self.updateMapColourSelection())

    # Menu Method: Set Use Contoured Grid Maps
    def setUseContouredGridMaps(self) :
        #print 'TODO: setUseContouredGridMaps'
        self.use_contoured_grid_maps = bool(self.use_contoured_grid_maps_int.get())
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            if 'contoured' not in self.map_options_update_includes :
                self.map_options_update_includes.append('contoured')
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Set Show Grid Map Land Boundaries
    def setShowGridMapLandBoundaries(self) :
        #print 'TODO: setShowGridMapLandBoundaries'
        self.show_grid_map_land_boundaries = bool(self.show_grid_map_land_boundaries_int.get())
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Set Show Map Grid Lines
    def setShowMapGridLines(self) :
        #print 'TODO: setShowMapGridLines'
        self.show_map_grid_lines = bool(self.show_map_grid_lines_int.get())
        if self.show_map_grid_lines :
            self.map_grid_include_menu.configure(state=tk.NORMAL)
            self.map_grid_space_menu.configure(state=tk.NORMAL)
        else :
            self.map_grid_include_menu.configure(state=tk.DISABLED)
            self.map_grid_space_menu.configure(state=tk.DISABLED)
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Select Map Grid Include
    def selectMapGridInclude(self, selected) :
        #print 'TODO: selectMapGridInclude'
        self.map_grid_include_text.set(self.map_grid_include_selection[self.map_grid_includes.index(selected)]) # needed as OptionMenu menu item commands have been overridden
        self.map_grid_include = selected
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Select Map Grid Space
    def selectMapGridSpace(self, selected) :
        #print 'TODO: selectMapGridSpace', selected
        self.map_grid_space_text.set(self.map_grid_space_selection[self.map_grid_spaces.index(float(selected))]) # needed as OptionMenu menu item commands have been overridden
        self.map_grid_space = float(selected)
        if hasattr(self, 'view_climate_data_window') and self.view_climate_data_window.children and self.current_view_climate_data_window_type == 'map' :
            self.map_options_update_button.configure(state=tk.NORMAL)

    # Menu Method: Configure Climate Data Location
    def configureClimateDataLocation(self) :

        self.focus_set()
        
        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.validation_warning_pending = False
            return True

        # Create or update config window
        if hasattr(self, 'config_climate_data_location_window') :
            if self.config_climate_data_location_window.children :
                self.config_climate_data_location_window.focus_set()
            else :
                self.config_climate_data_location_window.destroy()
                self.createConfigureClimateDataLocationWindow()
        else :
            self.createConfigureClimateDataLocationWindow()        
        
    # Menu Method: Create Configure Climate Data Location Window
    def createConfigureClimateDataLocationWindow(self) :

        # Create the view window
        self.config_climate_data_location_window = tk.Toplevel(self)
        self.config_climate_data_location_window.title('Configure Climate Data Location')
        self.config_climate_data_location_window.transient(self)
        self.config_climate_data_location_window.minsize(width=300, height=20)
        self.config_climate_data_location_window.focus_set()

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # If current climate data local directory location doesn't exist then clear it
        if not path.exists(tool_option_values['climate_data_directory']) or not self.data_file_helper.climateDataIsPresent() :
            tool_option_values['climate_data_directory'] = ''

        # Create the General Location Options frame
        location_options_frame = tk.Frame(self.config_climate_data_location_window, padx=5, pady=5)

        # Default location for climate data files
        self.climate_data_source_options = { 'url' : 'Network URL', 'local' : 'Local Directory' }
        self.climate_data_source_text = tk.StringVar(value=self.climate_data_source_options[tool_option_values['climate_data_source']])
        climate_data_source_menu_selection = [self.climate_data_source_options['url'], self.climate_data_source_options['local']]
        self.climate_data_source_menu = tk.OptionMenu(location_options_frame, self.climate_data_source_text, *climate_data_source_menu_selection)
        self.climate_data_source_menu.config(highlightthickness=0, anchor=tk.W)
        select_climate_data_source = location_options_frame.register(self.selectClimateDataSource)
        for i, selection in enumerate(['url', 'local']) :
            self.climate_data_source_menu['menu'].entryconfigure(i, command=(select_climate_data_source, selection))

        # URL and proxy settings
        self.climate_data_url_text = tk.StringVar(value=tool_option_values['climate_data_url'])
        self.climate_data_proxy_active_int = tk.IntVar(value=int(tool_option_values['climate_data_proxy_active']))
        self.climate_data_proxy_active_checkbox = tk.Checkbutton(location_options_frame, text='Connect via proxy', variable=self.climate_data_proxy_active_int, padx=0, command=self.setClimateDataProxyActive)
        self.climate_data_proxy_url_text = tk.StringVar(value=tool_option_values['climate_data_proxy_url'])
        self.climate_data_proxy_username_text = tk.StringVar(value=tool_option_values['climate_data_proxy_username'])
        self.climate_data_proxy_password_text = tk.StringVar(value=tool_option_values['climate_data_proxy_password'])
        self.climate_data_url_entry = tk.Entry(location_options_frame, textvariable=self.climate_data_url_text, width=70, justify=tk.LEFT)
        validate_climate_data_url_entry = self.climate_data_url_entry.register(self.validateClimateDataUrlEntry)
        self.climate_data_url_entry.config(validate='all', validatecommand=(validate_climate_data_url_entry, '%P', '%V'))
        self.climate_data_proxy_url_entry = tk.Entry(location_options_frame, textvariable=self.climate_data_proxy_url_text, width=50, justify=tk.LEFT)
        self.climate_data_proxy_username_entry = tk.Entry(location_options_frame, textvariable=self.climate_data_proxy_username_text, width=30, justify=tk.LEFT)
        self.climate_data_proxy_password_entry = tk.Entry(location_options_frame, textvariable=self.climate_data_proxy_password_text, show='*', width=30, justify=tk.LEFT)

        # Local directory selection
        self.climate_data_directory_text = tk.StringVar(value=tool_option_values['climate_data_directory'])
        self.climate_data_directory_label = tk.Label(location_options_frame, textvariable=self.climate_data_directory_text, justify=tk.LEFT)

        # Location button: Save (url) or Select Directory (local)
        self.climate_data_location_button_text = tk.StringVar()
        self.climate_data_location_button = tk.Button(location_options_frame, textvariable=self.climate_data_location_button_text, command=self.setClimateDataLocation)

        # Place elements on grid
        self.climate_data_source_menu.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_location_button.grid(row=0, rowspan=4, column=3, padx=5, pady=5, sticky=tk.W+tk.E)
        self.climate_data_directory_label.grid(row=0, column=4, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_active_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_url_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_username_label = tk.Label(location_options_frame, text='Username:', justify=tk.LEFT)
        self.climate_data_proxy_username_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_username_entry.grid(row=2, column=2, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_password_label = tk.Label(location_options_frame, text='Password:', justify=tk.LEFT)
        self.climate_data_proxy_password_label.grid(row=3, column=1, padx=5, pady=5, sticky=tk.NW+tk.SE)
        self.climate_data_proxy_password_entry.grid(row=3, column=2, padx=5, pady=5, sticky=tk.NW+tk.SE)
        location_options_frame.columnconfigure(1, weight=1)
        location_options_frame.columnconfigure(2, weight=1000)

        # Remove elements not associated with current source
        if tool_option_values['climate_data_source'] == 'url' :
            self.climate_data_location_button_text.set('Save')
            if not tool_option_values['climate_data_proxy_active'] :
                self.climate_data_proxy_url_entry.grid_remove()
                self.climate_data_proxy_username_label.grid_remove()
                self.climate_data_proxy_username_entry.grid_remove()
                self.climate_data_proxy_password_label.grid_remove()
                self.climate_data_proxy_password_entry.grid_remove()
            self.climate_data_directory_label.grid_remove()
        else : # local
            self.climate_data_location_button_text.set('Select Directory')
            self.climate_data_url_entry.grid_remove()
            self.climate_data_proxy_active_checkbox.grid_remove()
            self.climate_data_proxy_url_entry.grid_remove()
            self.climate_data_proxy_username_label.grid_remove()
            self.climate_data_proxy_username_entry.grid_remove()
            self.climate_data_proxy_password_label.grid_remove()
            self.climate_data_proxy_password_entry.grid_remove()
        
        location_options_frame.grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=0, pady=0)

    # Menu Configure Method: Select Climate Data Source
    def selectClimateDataSource(self, code) :
        #print 'TODO: selectClimateDataSource'
        self.climate_data_source_text.set(self.climate_data_source_options[code]) # needed as OptionMenu menu item commands have been overridden
        
        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # On change, repopulate url elements from config
        if tool_option_values['climate_data_source'] != code and code == 'url' :
            self.climate_data_url_text.set(tool_option_values['climate_data_url'])
            self.climate_data_proxy_active_int.set(int(tool_option_values['climate_data_proxy_active']))
            self.climate_data_proxy_url_text.set(tool_option_values['climate_data_proxy_url'])
            self.climate_data_proxy_username_text.set(tool_option_values['climate_data_proxy_username'])
            self.climate_data_proxy_password_text.set(tool_option_values['climate_data_proxy_password'])

        # Change source and swap entries
        self.setToolOptions({ 'climate_data_source' : code })
        self.data_file_helper.setClimateDataSource(code)
        if code == 'url' :
            self.climate_data_location_button_text.set('Save')
            self.climate_data_url_entry.grid()
            self.climate_data_proxy_active_checkbox.grid()
            if tool_option_values['climate_data_proxy_active'] :
                self.climate_data_proxy_url_entry.grid()
                self.climate_data_proxy_username_label.grid()
                self.climate_data_proxy_username_entry.grid()
                self.climate_data_proxy_password_label.grid()
                self.climate_data_proxy_password_entry.grid()
            self.climate_data_directory_label.grid_remove()
            self.climate_data_url_text.set(tool_option_values['climate_data_url'])
        else : # local
            self.climate_data_location_button_text.set('Select Directory')
            self.climate_data_directory_label.grid()
            self.climate_data_url_entry.grid_remove()
            self.climate_data_proxy_active_checkbox.grid_remove()
            self.climate_data_proxy_url_entry.grid_remove()
            self.climate_data_proxy_username_label.grid_remove()
            self.climate_data_proxy_username_entry.grid_remove()
            self.climate_data_proxy_password_label.grid_remove()
            self.climate_data_proxy_password_entry.grid_remove()
            self.climate_data_directory_text.set(tool_option_values['climate_data_directory'])

    # Menu Configure Method: Set Climate Data Location
    def validateClimateDataUrlEntry(self, string_value, reason) : # eg. '%P', '%V'
        #print 'TODO: validateClimateDataUrlEntry', string_value, reason
        return True

    # Menu Configure Method: Set Climate Data Proxy Active
    def setClimateDataProxyActive(self) :
        #print 'TODO: setClimateDataProxyActive'

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # Set in config and helper
        self.setToolOptions({ 'climate_data_proxy_active' : bool(self.climate_data_proxy_active_int.get()) })
        self.data_file_helper.setClimateDataProxy(bool(self.climate_data_proxy_active_int.get()))

        # When active is selected, repopulate proxy elements from config then show them
        if self.climate_data_proxy_active_int.get() :
            self.climate_data_proxy_url_text.set(tool_option_values['climate_data_proxy_url'])
            self.climate_data_proxy_username_text.set(tool_option_values['climate_data_proxy_username'])
            self.climate_data_proxy_password_text.set(tool_option_values['climate_data_proxy_password'])
            self.climate_data_proxy_url_entry.grid()
            self.climate_data_proxy_username_label.grid()
            self.climate_data_proxy_username_entry.grid()
            self.climate_data_proxy_password_label.grid()
            self.climate_data_proxy_password_entry.grid()
        else : # hide them
            self.climate_data_proxy_url_entry.grid_remove()
            self.climate_data_proxy_username_label.grid_remove()
            self.climate_data_proxy_username_entry.grid_remove()
            self.climate_data_proxy_password_label.grid_remove()
            self.climate_data_proxy_password_entry.grid_remove()

    # Menu Configure Method: Set Climate Data Location
    def setClimateDataLocation(self) :
        #print 'TODO: setClimateDataLocation'

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # Action depends on data source
        if tool_option_values['climate_data_source'] == 'url' :
            self.data_file_helper.setClimateDataUrl(self.climate_data_url_text.get())
            if self.climate_data_proxy_active_int.get() :
                self.setToolOptions({ 'climate_data_url' : self.climate_data_url_text.get(), 'climate_data_proxy_active' : True,
                                      'climate_data_proxy_url' : self.climate_data_proxy_url_text.get(),
                                      'climate_data_proxy_username' : self.climate_data_proxy_username_text.get(),
                                      'climate_data_proxy_password' : self.climate_data_proxy_password_text.get() })
                self.data_file_helper.setClimateDataProxy(True, url=self.climate_data_proxy_url_text.get(), username=self.climate_data_proxy_username_text.get(), password=self.climate_data_proxy_password_text.get())
                showinfo('Climate Data URL and Proxy Saved', 'Climate Data URL and Proxy Settings Saved to Configuration File')
            else :
                self.setToolOptions({ 'climate_data_url' : self.climate_data_url_text.get(), 'climate_data_proxy_active' : False })
                self.data_file_helper.setClimateDataProxy(False)
                showinfo('Climate Data URL Saved', 'Climate Data URL Saved to Configuration File')
        else : # local
            self.selectClimateDataDirectory()

    # Menu Configure Method: Select Climate Data Directory
    def selectClimateDataDirectory(self) :
        #print 'TODO: selectClimateDataDirectory'

        # Use existing Climate Data Directory if it exists
        current_dir = self.climate_data_directory_text.get()
        if path.exists(current_dir) :
            initial_directory = current_dir
        elif MAC_VERSION and environ.has_key('HOME') and path.exists(environ['HOME']) :
            initial_directory = environ['HOME']
        elif environ.has_key('USERPROFILE') and path.exists(environ['USERPROFILE']) : # PC version
            initial_directory = environ['USERPROFILE']
        else :
            initial_directory = getcwd()

        # Open file selection dialog
        climate_data_directory_path = askdirectory(title='Select the directory containing the climate data', initialdir=initial_directory)

        if climate_data_directory_path : # Directory selected

            # Create directory if it doesn't already exist
            if not path.exists(climate_data_directory_path) :
                try :
                    climate_data_directory_path = self.data_file_helper.createDirectoryPath(climate_data_directory_path)
                except Exception, e :
                    directory_name = self.data_file_helper.splitPath(climate_data_directory_path)['name']
                    showerror('Directory Error', 'Error loading or creating directory \"'+directory_name+'\". Check file permissions.')
                    print >> sys.stderr, 'Error loading or creating directory:', e

            # Does it contain the climate data?
            climate_data_directory_path = path.normpath(str(climate_data_directory_path))
            previous_path = self.data_file_helper.getClimateDataDirectoryPath()
            self.data_file_helper.setClimateDataDirectory(climate_data_directory_path)
            if self.data_file_helper.climateDataIsPresent() :
                self.climate_data_directory_text.set(climate_data_directory_path)
                self.setToolOptions({ 'climate_data_directory' : climate_data_directory_path })
                # Reset focus to config window
                self.config_climate_data_location_window.focus_set()
            else :
                showwarning('Climate data not found', 'The expected climate data was not found in ' + climate_data_directory_path)
                self.data_file_helper.setClimateDataDirectory(previous_path)

    # Menu Method: Configure Default File Generation Directory
    def configureDefaultFileGenerationDirectory(self) :

        self.focus_set()
        
        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.validation_warning_pending = False
            return True

        # Create or update config window
        if hasattr(self, 'config_default_file_generation_directory_window') :
            if self.config_default_file_generation_directory_window.children :
                self.config_default_file_generation_directory_window.focus_set()
            else :
                self.config_default_file_generation_directory_window.destroy()
                self.createConfigureDefaultFileGenerationDirectoryWindow()
        else :
            self.createConfigureDefaultFileGenerationDirectoryWindow()        
        
    # Menu Method: Create Configure Default File Generation Directory Window
    def createConfigureDefaultFileGenerationDirectoryWindow(self) :

        # Create the Configure Default File Generation Directory window
        self.config_default_file_generation_directory_window = tk.Toplevel(self)
        self.config_default_file_generation_directory_window.title('Configure Default Output Directory')
        self.config_default_file_generation_directory_window.transient(self)
        self.config_default_file_generation_directory_window.minsize(width=370, height=20)
        self.config_default_file_generation_directory_window.focus_set()

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # When the current file generation directory location doesn't exist then clear it
        if not path.exists(tool_option_values['default_file_generation_directory']) :
            tool_option_values['default_file_generation_directory'] = ''

        # Only display the current file generation directory when it has been set (rather than last generation location used)
        if tool_option_values['default_file_generation_directory'] and tool_option_values['default_file_generation_directory_set'] :
            display_dir = tool_option_values['default_file_generation_directory']
        else :
            display_dir = ''

        # Create the General File Options frame
        file_options_frame = tk.Frame(self.config_default_file_generation_directory_window, padx=5, pady=5)

        # Default location for generated files
        self.default_file_generation_directory_location = tk.StringVar(value=display_dir)
        self.default_file_generation_directory_location_button = tk.Button(file_options_frame, text='Select Directory', command=self.selectDefaultFileGenerationDirectory)
        default_file_generation_directory_location_label = tk.Label(file_options_frame, textvariable=self.default_file_generation_directory_location, justify=tk.LEFT)
        self.default_file_generation_directory_location_button.grid(row=0, column=0, padx=4, pady=5, sticky=tk.W+tk.E)
        default_file_generation_directory_location_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NW+tk.SW)
        
        file_options_frame.grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=0, pady=0)

    # Menu Configure Method: Select Default File Generation Directory
    def selectDefaultFileGenerationDirectory(self) :
        #print 'TODO: selectDefaultFileGenerationDirectory'

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # Use existing Default File Generation Directory if it exists
        if path.exists(tool_option_values['default_file_generation_directory']) :
            initial_directory = tool_option_values['default_file_generation_directory']
        elif MAC_VERSION and environ.has_key('HOME') and path.exists(environ['HOME']) :
            initial_directory = environ['HOME']
        elif environ.has_key('USERPROFILE') and path.exists(environ['USERPROFILE']) : # PC version
            initial_directory = environ['USERPROFILE']
        else :
            initial_directory = getcwd()

        # Open file selection dialog
        default_file_generation_directory_path = askdirectory(title='Select the default directory for output files', initialdir=initial_directory)

        if default_file_generation_directory_path : # Directory selected

            # Create directory if it doesn't already exist
            if not path.exists(default_file_generation_directory_path) :
                try :
                    default_file_generation_directory_path = self.data_file_helper.createDirectoryPath(default_file_generation_directory_path)
                except Exception, e :
                    directory_name = self.data_file_helper.splitPath(default_file_generation_directory_path)['name']
                    showerror('Directory Error', 'Error loading or creating directory \"'+directory_name+'\". Check file permissions.')
                    print >> sys.stderr, 'Error loading or creating directory:', e

            # Set the directory
            default_file_generation_directory_path = path.normpath(str(default_file_generation_directory_path))
            self.data_file_helper.setFileGenerationDirectory(default_file_generation_directory_path)
            location_descr = 'File generation in \"' + self.data_file_helper.getFileGenerationDirectoryName() + '\"'
            self.generation_directory_label_text.set(location_descr)
            self.default_file_generation_directory_location.set(default_file_generation_directory_path)
            self.setToolOptions({ 'default_file_generation_directory' : default_file_generation_directory_path, 'default_file_generation_directory_set' : True })

            # Enable the generate button
            self.generate_button.configure(state=tk.NORMAL)

            # Reset focus to config window
            self.config_default_file_generation_directory_window.focus_set()

    ## Step 1: Data Type Methods ################################################################################################################################################

    # Step 1 Method: Select data type: the user selects an option
    def selectDataType(self, selected) :
        #print 'TODO: selectDataType', selected

        self.data_type_text.set(self.data_type_selection[self.data_type_keys.index(selected)]) # needed as OptionMenu menu item commands have been overridden

        if selected == 'map' :
            self.maximum_interval_steps = self.maximum_maps - 1
            self.view_label_text.set(self.generation_options['view']['map'])
            self.generate_label_text.set(self.generation_options['files']['map'])
            self.edit_menu.entryconfigure(self.edit_menu_indices['map_options'], state=tk.NORMAL)
        elif selected == 'series' :
            self.maximum_interval_steps = self.maximum_time_series_points - 1
            self.view_label_text.set(self.generation_options['view']['series'])
            self.generate_label_text.set(self.generation_options['files']['series'])
            self.edit_menu.entryconfigure(self.edit_menu_indices['map_options'], state=tk.DISABLED)
            if hasattr(self, 'edit_map_options_window') :
                self.edit_map_options_window.destroy()

        # Potentially restrict parameters and time units
        self.restrictParameters()
        self.restrictTimeUnit()

        # Limit data generation file type selections
        for i, data_file_type in enumerate(self.data_file_type_keys) :
            if data_file_type in self.data_file_types_for_data_type[selected] :
                self.data_file_type_menu['menu'].entryconfigure(i, state=tk.NORMAL)
            else :
                self.data_file_type_menu['menu'].entryconfigure(i, state=tk.DISABLED)

        # Ensure selected data generation file type is allowed
        selected_data_file_type = self.data_file_type_keys[self.data_file_type_selection.index(self.data_file_type_text.get())]
        if selected_data_file_type not in self.data_file_types_for_data_type[selected] :
            self.selectDataFileType(self.data_file_types_for_data_type[selected][0])

        # Update data action
        #self.data_action_menu['map'].grid_remove()
        #self.data_action_menu['series'].grid_remove()
        #self.data_action_menu[selected].grid()

        # Update Period (and Current Interval Steps)
        self.matchPeriodUntilWithFrom()

        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 1 Method: Select data action: the user selects an option
    def selectDataAction(self, selected) : #selectDataAction(self, data_type, selected) :
        #print 'TODO: selectDataAction', selected

        self.data_action_text.set(self.data_action_selection[self.data_action_keys.index(selected)]) # needed as OptionMenu menu item commands have been overridden
        #self.data_action_text[data_type].set(self.data_action_selection[data_type][self.data_action_keys.index(selected)]) # needed as OptionMenu menu item commands have been overridden

        # Set maximum interval steps
        if selected == 'view' :
            self.file_frame.grid_remove()
            self.view_frame.grid()
            self.utilise_delta_text.set(self.utilise_delta_pre_text['view'] + self.utilise_delta_post_text)
##            self.configure_menu.entryconfigure(self.configure_menu_indices['default_file_generation_directory'], state=tk.DISABLED)
##            if hasattr(self, 'config_default_file_generation_directory_window') :
##                self.config_default_file_generation_directory_window.destroy()
        elif selected == 'files' :
            self.view_frame.grid_remove()
            self.file_frame.grid()
            self.utilise_delta_text.set(self.utilise_delta_pre_text['files'] + self.utilise_delta_post_text)
##            self.configure_menu.entryconfigure(self.configure_menu_indices['default_file_generation_directory'], state=tk.NORMAL)

        # Update Period (and Current Interval Steps)
        self.matchPeriodUntilWithFrom()

        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    ## Step 2: Parameter Selection Methods ##################################################################################################################################

    # Step 2 Method: Select Parameter Group: the user opens options
    def selectParameterGroup(self, group_code) :

        self.parameter_group_text.set(self.parameter_group_code_map[group_code]) # needed as OptionMenu menu item commands have been overridden

        # Swap parameter selection menu
        self.current_parameter_group_field.grid_remove()
        self.parameter_via_group_menu[group_code].grid()
        self.current_parameter_group_field = self.parameter_via_group_menu[group_code]

        # Potentially restrict parameters and time units
        self.restrictParameters()
        self.restrictTimeUnit()

        # Include delta as percent?
        self.deltaAsPercentInclusion()

        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 2 Method: Select Parameter: the user opens options
    def selectParameter(self, group_code, parameter_code) :

        self.parameter_via_group_text[group_code].set(self.parameter_via_group_code_map[group_code][parameter_code]) # needed as OptionMenu menu item commands have been overridden

        # Potentially restrict time units
        self.restrictTimeUnit()

        # Include delta as percent?
        self.deltaAsPercentInclusion()

        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 2 Method: Restrict Parameters Via Data Type 
    def restrictParameters(self) :
        
        # Initialise allowed parameters
        allowed_parameters = {}
        for group_code in self.parameter_group_codes :
            allowed_parameters[group_code] = self.parameter_via_group_codes[group_code][:]

        # Resolve any restrictions based on data type
        data_type = self.data_type_text.get()
        if self.parameter_restricted_via_data_type.has_key(data_type) :
            for group_code in self.parameter_group_codes :
                if self.parameter_restricted_via_data_type[data_type].has_key(group_code) :
                    allowed_parameters[group_code] = self.parameter_restricted_via_data_type[data_type][group_code]

        # Enable/disable parameter selections appropriately
        allowed_groups = []
        for i, group_code in enumerate(self.parameter_group_codes) : 
            if allowed_parameters[group_code] :
                allowed_groups.append(group_code)
                self.parameter_group_menu['menu'].entryconfigure(i, state=tk.NORMAL)
                for j, parameter_code in enumerate(self.parameter_via_group_codes[group_code]) :
                    if len(self.parameter_via_group_codes[group_code]) > 1 :
                        if parameter_code in allowed_parameters[group_code] :
                            self.parameter_via_group_menu[group_code]['menu'].entryconfigure(j, state=tk.NORMAL)
                        else :
                            self.parameter_via_group_menu[group_code]['menu'].entryconfigure(j, state=tk.DISABLED)
            else :
                self.parameter_group_menu['menu'].entryconfigure(i, state=tk.DISABLED)

        # Select another parameter/group if the current selection is not allowed
        selected_group = self.parameter_group_selection_map[self.parameter_group_text.get()]
        if selected_group not in allowed_groups :
            self.selectParameterGroup(allowed_groups[0])
        else :
            selected_parameter = self.parameter_via_group_selection_map[selected_group][self.parameter_via_group_text[selected_group].get()]
            if selected_parameter not in allowed_parameters[selected_group] :
                self.selectParameter(selected_group, allowed_parameters[selected_group][0])

    # Step 2 Method: Restrict Time Unit Via Data Type and/or Parameter
    def restrictTimeUnit(self) :

        # Initialise allowed time units
        allowed_time_units = self.time_unit_selection[:]

        # Resolve any restrictions based on data type
        data_type = self.data_type_text.get()
        if self.time_unit_restricted_via_data_type.has_key(data_type) :
            allowed_time_units = self.time_unit_restricted_via_data_type[data_type][:]

        # Resolve any restrictions based on parameter
        group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        if self.time_unit_restricted_via_parameter.has_key(group_code) :
            parameter_code = self.parameter_via_group_selection_map[group_code][self.parameter_via_group_text[group_code].get()]
            if self.time_unit_restricted_via_parameter[group_code].has_key(parameter_code) :
                for time_unit in allowed_time_units[:] :
                    if time_unit not in self.time_unit_restricted_via_parameter[group_code][parameter_code] :
                        allowed_time_units.remove(time_unit)

        # Enable/disable time unit selections appropriately
        for i, selection in enumerate(self.time_unit_selection) :
            if selection in allowed_time_units :
                self.time_unit_menu['menu'].entryconfigure(i, state=tk.NORMAL)
            else :
                self.time_unit_menu['menu'].entryconfigure(i, state=tk.DISABLED)

        # Select another time unit if the current selection is not allowed
        if self.time_unit_text.get() not in allowed_time_units :
            self.selectTimeUnit(allowed_time_units[0])

    # Step 2 Method: Select Time Unit: the user selects an option
    def selectTimeUnit(self, selected, context=None) :
        #print 'TODO: selectTimeUnit', selected, context 

        if context == 'months' :
            self.time_unit_months_text.set(selected) # needed as OptionMenu menu item commands have been overridden
            self.selected_time_unit_month_indices = [self.month_names.index(selected)]
        elif context == 'seasons' :
            self.time_unit_seasons_text.set(selected) # needed as OptionMenu menu item commands have been overridden
            self.selected_time_unit_month_indices = self.time_unit_seasons_month_indices[selected]
        else :
            self.time_unit_text.set(selected) # needed as OptionMenu menu item commands have been overridden
            self.current_time_unit_field.grid_remove()
            if selected == 'Month' :
                self.selected_time_unit_month_indices = [self.month_names.index(self.time_unit_months_text.get())]
                self.time_unit_months_menu.grid()
                self.current_time_unit_field = self.time_unit_months_menu
            elif selected == 'Season' :
                self.selected_time_unit_month_indices = self.time_unit_seasons_month_indices[self.time_unit_seasons_text.get()]
                self.time_unit_seasons_menu.grid()
                self.current_time_unit_field = self.time_unit_seasons_menu
            elif selected == 'Annual' :
                self.selected_time_unit_month_indices = range(12)
                self.time_unit_other_text.set('JFMAMJJASOND')
                self.time_unit_other_label.grid()
                self.current_time_unit_field = self.time_unit_other_label
            elif selected == 'User-defined' :
                self.selected_time_unit_month_indices = self.current_user_defined_time_unit_month_indices
                self.time_unit_other_text.set(self.userDefinedTimeUnitString(self.current_user_defined_time_unit_month_indices))
                self.time_unit_other_label.grid()
                self.current_time_unit_field = self.time_unit_other_label
                self.setUserDefinedTimeUnit()
            elif selected == 'All Months' :
                self.selected_time_unit_month_indices = range(12)
                self.time_unit_other_text.set('')
                self.time_unit_other_label.grid()
                self.current_time_unit_field = self.time_unit_other_label

            if selected == 'All Months' :
                self.time_unit_is_all_months = True
            elif self.time_unit_is_all_months :
                self.time_unit_is_all_months = False

        # Modify period dates when months cross years if required
##        if self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD
##            maximum_from_value = self.period_ranges['AD']['max'] - self.interval_step_range['min'] - self.interval_size_range['min']/2
##        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
##            maximum_from_value = self.period_ranges['BP']['max'] - self.interval_size_range['min']/2
##            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                if self.current_valid_period_value['from'] > maximum_from_value - 1 :
##                    self.period_text['from'].set(str(maximum_from_value - 1))
##            else :
##                if self.current_valid_period_value['from'] == (maximum_from_value - 1) :
##                    self.period_text['from'].set(str(maximum_from_value))
##            self.updateIntervalStep()
##            self.updatePeriodSpinboxList('from')
##            self.matchPeriodUntilWithFrom()
##            self.matchIntervalSizeWithStep()
##            self.updateDeltaReferenceIntervals()

        #print self.selected_time_unit_month_indices
        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 2 Method: User Defined Time Unit String
    def userDefinedTimeUnitString(self, time_unit_month_indices) :
        sorted_indices = time_unit_month_indices[:]
        sorted_indices.sort()
        rearranged_indices = sorted_indices[:]
        move_tail_to_front = False
        for i, index in enumerate(sorted_indices) :
            if move_tail_to_front or (i > 0 and index > (sorted_indices[i-1] + 1)) :
                tail = rearranged_indices.pop()
                rearranged_indices.insert(0, tail)
                move_tail_to_front = True
        time_unit_string = ''
        for index in rearranged_indices :
            time_unit_string += self.month_shortnames[index]
        return time_unit_string

    # Step 2 Method: Set User Defined Time Unit
    def setUserDefinedTimeUnit(self) :
        if hasattr(self, 'user_defined_time_unit_window') :
            if self.user_defined_time_unit_window.children :
                self.user_defined_time_unit_window.focus_set()
            else :
                self.user_defined_time_unit_window.destroy()
                self.createUserDefinedTimeUnitWindow()
        else :
            self.createUserDefinedTimeUnitWindow()

    # Step 2 Method: Create User Defined Time Unit window
    def createUserDefinedTimeUnitWindow(self) :

        # Create the options window
        self.user_defined_time_unit_window = tk.Toplevel(self)
        self.user_defined_time_unit_window.title('User-defined Time Unit')
        self.user_defined_time_unit_window.transient(self)
        self.user_defined_time_unit_window.focus_set()

        # Selectable month list
        self.user_defined_time_units = []
        self.user_defined_time_units_checkboxes = []
        tk.Frame(self.user_defined_time_unit_window).grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=5, pady=2)
        tk.Label(self.user_defined_time_unit_window, text='Select any number of adjacent months:').grid(row=1, column=0, sticky=tk.NW+tk.SW, padx=5, pady=0)
        for i, month in enumerate(self.time_unit_months_selection) :
            self.user_defined_time_units.append(tk.IntVar())
            if i in self.current_user_defined_time_unit_month_indices :
                self.user_defined_time_units[i].set(1)
            self.user_defined_time_units_checkboxes.append(tk.Checkbutton(self.user_defined_time_unit_window, variable=self.user_defined_time_units[i], text=month, command=self.setUserDefinedTimeUnitValues))
            self.user_defined_time_units_checkboxes[i].grid(row=i+2, column=0, sticky=tk.NW+tk.SW, padx=5, pady=0)
        self.setUserDefinedTimeUnitValues()

        # Done and cancel buttons
        user_defined_time_unit_actions_frame = tk.Frame(self.user_defined_time_unit_window)
        self.user_defined_time_unit_done_button = tk.Button(user_defined_time_unit_actions_frame, text='Done', command=self.userDefinedTimeUnitDone)
        self.user_defined_time_unit_cancel_button = tk.Button(user_defined_time_unit_actions_frame, text='Cancel', command=self.userDefinedTimeUnitCancel)
        self.user_defined_time_unit_done_button.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.user_defined_time_unit_cancel_button.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        user_defined_time_unit_actions_frame.grid(row=i+3, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)

    # Step 2 Method: Set User Defined Time Unit Values
    def setUserDefinedTimeUnitValues(self) :
        checked = []
        for i, month in enumerate(self.time_unit_months_selection) :
            if self.user_defined_time_units[i].get() == 1 :
                checked.append(i)
        if checked :
            for i, month in enumerate(self.time_unit_months_selection) :
                if checked.count(i) or checked.count(i-1) or checked.count(i+1) or (i == 0 and checked.count(11)) or (i == 11 and checked.count(0)) :
                    self.user_defined_time_units_checkboxes[i].configure(state=tk.NORMAL)
                else :
                    self.user_defined_time_units_checkboxes[i].configure(state=tk.DISABLED)
        else :
            for i, month in enumerate(self.time_unit_months_selection) :
                self.user_defined_time_units_checkboxes[i].configure(state=tk.NORMAL)
        return checked
        
    # Step 2 Method: User Defined Time Unit Done
    def userDefinedTimeUnitDone(self) :

        # Update time unit fields
        self.current_user_defined_time_unit_month_indices = self.setUserDefinedTimeUnitValues()
        self.time_unit_other_text.set(self.userDefinedTimeUnitString(self.current_user_defined_time_unit_month_indices))
        self.selected_time_unit_month_indices = self.current_user_defined_time_unit_month_indices
        
        # Modify period dates when months cross years if required
##        if self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD
##            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                maximum_from_value = self.period_ranges['AD']['max'] - self.current_valid_interval_step_value - self.interval_size_range['min']/2 - 1
##                if self.current_valid_period_value['from'] > maximum_from_value :
##                    self.period_text['from'].set(str(self.current_valid_period_value['from'] - self.current_valid_interval_step_value))
##        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
##            maximum_from_value = self.period_ranges['BP']['max'] - self.interval_size_range['min']/2
##            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                if self.current_valid_period_value['from'] > maximum_from_value - 1 :
##                    self.period_text['from'].set(str(maximum_from_value - 1))
##            else :
##                if self.current_valid_period_value['from'] == (maximum_from_value - 1) :
##                    self.period_text['from'].set(str(maximum_from_value))
##            self.updateIntervalStep()
##            self.updatePeriodSpinboxList('from')
##            self.matchPeriodUntilWithFrom()
##            self.matchIntervalSizeWithStep()
##            self.updateDeltaReferenceIntervals()

        # Close options window
        self.user_defined_time_unit_window.destroy()

        # Update workflow status
        self.updateStepsCompleted()

    # Step 2 Method: User Defined Time Unit Cancel
    def userDefinedTimeUnitCancel(self) :
        self.user_defined_time_unit_window.destroy()

    ## Step 3: Region Methods ##############################################################################################################################################

    # Step 3 Method: Select Region: the user opens options
    def selectRegion(self, selected) :
        #print 'TODO: selectRegion', selected
        self.region_selection_text.set(self.region_code_map[selected]) # needed as OptionMenu menu item commands have been overridden
        self.current_region = selected
        if selected == 'user-defined' :
            self.region_mask = self.current_user_defined_region_mask
            self.view_edit_region_button_text.set('Select Region')
            self.viewEditRegion(button_pressed=False)
        else :
            self.view_edit_region_button_text.set('View Region')
            self.region_mask = self.data_file_helper.loadRegionMask(selected, time_dependent=self.region_is_time_dependent[selected])
            self.updateRegionWindow(button_pressed=False)

        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 3 Method: View Edit Region
    def viewEditRegion(self, button_pressed=True) :
        #print 'TODO: viewEditRegion', button_pressed

        if button_pressed :
            # Shift focus so as to trigger any pending validation warnings
            self.focus_set()
            
            # Exit if validation warning is pending
            if self.validation_warning_pending :
                self.validation_warning_pending = False
                return True

        # Create or update plot window
        if hasattr(self, 'view_edit_region_window') :
            if self.view_edit_region_window.children and not self.current_region == 'user-defined' :
                self.view_edit_region_window.focus_set()
                self.updateRegionWindow(button_pressed)
            else :
                self.view_edit_region_window.destroy()
                self.createRegionWindow()
        else :
            self.createRegionWindow()        
        
        # Update workflow status
        self.updateStepsCompleted()

        # Reset generation
        self.resetGeneration()

    # Step 3 Method: Create Region Window
    def createRegionWindow(self) :
        #print 'TODO: createRegionWindow'

        # Create the region window
        self.view_edit_region_window = tk.Toplevel(self)
        self.view_edit_region_window.title(self.view_edit_region_button_text.get())
        self.view_edit_region_window.transient(self)
        self.view_edit_region_window.focus_set()

        # Reset region mask to the current accepted mask
        if self.current_region == 'user-defined' :
            self.region_mask = self.current_user_defined_region_mask

        # Create region frame
        self.view_edit_region_frame = tk.Frame(self.view_edit_region_window, padx=0, pady=0)

        # Select the appropriate starting region mask when time dependent series
        mask_year = None
        if self.region_is_time_dependent[self.current_region] :
            mask_year = self.calculateTimeDependentRegionYear()

        # Create region figure
        self.createRegionFigure(time_dependent_year=mask_year)

        # Plot the region map
        self.view_edit_region_canvas = FigureCanvasTkAgg(self.view_edit_region_figure, master=self.view_edit_region_frame)
        self.view_edit_region_canvas.show()
        self.view_edit_region_canvas.get_tk_widget().grid(row=0, column=0) #.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Bind mouse selection events for user-defined region selection
        self.view_edit_region_canvas.mpl_connect('button_press_event', self.regionButtonPressEvent)
        self.view_edit_region_canvas.mpl_connect('button_release_event', self.regionButtonReleaseEvent)
        self.view_edit_region_canvas.mpl_connect('motion_notify_event', self.regionMotionNotifyEvent)
        self.view_edit_region_canvas.mpl_connect('axes_enter_event', self.regionAxesEnterEvent)
        self.view_edit_region_canvas.mpl_connect('axes_leave_event', self.regionAxesLeaveEvent)
        self.region_select_button_held = False
        self.region_select_top_left = [0, 0] # [0, 0] to [71, 143]

        # Add buttons and coordinates for selecting user-defined region
        self.user_defined_region_frame = tk.Frame(self.view_edit_region_frame)

        # Register validation and selection behaviour methods
        validate_user_defined_region_entry = self.user_defined_region_frame.register(self.validateUserDefinedRegionEntry)
        user_defined_region_spinbox_arrow_press = self.user_defined_region_frame.register(self.userDefinedRegionSpinboxArrowPress)

        # Create region entry fields
        self.user_defined_region_cursor_text = { 'latitude' : tk.StringVar(), 'longitude' : tk.StringVar() }
        self.user_defined_region_text = { 'latitude' : { 'from' : { 'degrees' : tk.StringVar(), 'direction' : tk.StringVar() }, 'to' : { 'degrees' : tk.StringVar(), 'direction' : tk.StringVar() } },
                                          'longitude' : { 'from' : { 'degrees' : tk.StringVar(), 'direction' : tk.StringVar() }, 'to' : { 'degrees' : tk.StringVar(), 'direction' : tk.StringVar() } } }
        self.previous_user_defined_region = self.copy_dict_mapping_values(self.user_defined_region_text)
        self.previous_user_defined_region_changed_via = { 'latitude' : { 'from' : { 'degrees' : 'forced', 'direction' : 'forced' }, 'to' : { 'degrees' : 'forced', 'direction' : 'forced' } },
                                                          'longitude' : { 'from' : { 'degrees' : 'forced', 'direction' : 'forced' }, 'to' : { 'degrees' : 'forced', 'direction' : 'forced' } } }
        self.user_defined_region_spinbox_values = { 'latitude' : { 'from' : { 'N' : np.arange(0,92.5,2.5).tolist(), 'S' : np.arange(87.5,-2.5,-2.5).tolist() },
                                                                   'to' : { 'N' : np.arange(0,90.0,2.5).tolist(), 'S' : np.arange(90,-2.5,-2.5).tolist() } },
                                                    'longitude' : { 'from' : { 'E' : np.arange(0,180.0,2.5).tolist(), 'W' : np.arange(180,-2.5,-2.5).tolist() },
                                                                    'to' : { 'E' : np.arange(0,182.5,2.5).tolist(), 'W' : np.arange(177.5,-2.5,-2.5).tolist() } } }
        self.user_defined_region_entry = { 'latitude' : { 'from' : {}, 'to' : {} }, 'longitude' : { 'from' : {}, 'to' : {} } }
        self.user_defined_region_entry['latitude']['from']['degrees'] = tk.Spinbox(self.user_defined_region_frame, textvariable=self.user_defined_region_text['latitude']['from']['degrees'], values=tuple(map(str, self.user_defined_region_spinbox_values['latitude']['from']['N'])), width=5, justify=tk.CENTER)
        self.user_defined_region_entry['latitude']['from']['degrees'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'latitude', 'from', 'degrees'))
        self.user_defined_region_entry['latitude']['from']['degrees'].config(command=(user_defined_region_spinbox_arrow_press, 'latitude', 'from'))
        self.user_defined_region_entry['latitude']['from']['direction'] = tk.Entry(self.user_defined_region_frame, textvariable=self.user_defined_region_text['latitude']['from']['direction'], width=2, justify=tk.CENTER)
        self.user_defined_region_entry['latitude']['from']['direction'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'latitude', 'from', 'direction'))
        self.user_defined_region_entry['latitude']['to']['degrees'] = tk.Spinbox(self.user_defined_region_frame, textvariable=self.user_defined_region_text['latitude']['to']['degrees'], values=tuple(map(str, self.user_defined_region_spinbox_values['latitude']['to']['S'])), width=5, justify=tk.CENTER)
        self.user_defined_region_entry['latitude']['to']['degrees'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'latitude', 'to', 'degrees'))
        self.user_defined_region_entry['latitude']['to']['degrees'].config(command=(user_defined_region_spinbox_arrow_press, 'latitude', 'to'))
        self.user_defined_region_entry['latitude']['to']['direction'] = tk.Entry(self.user_defined_region_frame, textvariable=self.user_defined_region_text['latitude']['to']['direction'], width=2, justify=tk.CENTER)
        self.user_defined_region_entry['latitude']['to']['direction'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'latitude', 'to', 'direction'))
        self.user_defined_region_entry['longitude']['from']['degrees'] = tk.Spinbox(self.user_defined_region_frame, textvariable=self.user_defined_region_text['longitude']['from']['degrees'], values=tuple(map(str, self.user_defined_region_spinbox_values['longitude']['from']['W'])), width=5, justify=tk.CENTER)
        self.user_defined_region_entry['longitude']['from']['degrees'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'longitude', 'from', 'degrees'))
        self.user_defined_region_entry['longitude']['from']['degrees'].config(command=(user_defined_region_spinbox_arrow_press, 'longitude', 'from'))
        self.user_defined_region_entry['longitude']['from']['direction'] = tk.Entry(self.user_defined_region_frame, textvariable=self.user_defined_region_text['longitude']['from']['direction'], width=2, justify=tk.CENTER)
        self.user_defined_region_entry['longitude']['from']['direction'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'longitude', 'from', 'direction'))
        self.user_defined_region_entry['longitude']['to']['degrees'] = tk.Spinbox(self.user_defined_region_frame, textvariable=self.user_defined_region_text['longitude']['to']['degrees'], values=tuple(map(str, self.user_defined_region_spinbox_values['longitude']['to']['W'])), width=5, justify=tk.CENTER)
        self.user_defined_region_entry['longitude']['to']['degrees'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'longitude', 'to', 'degrees'))
        self.user_defined_region_entry['longitude']['to']['degrees'].config(command=(user_defined_region_spinbox_arrow_press, 'longitude', 'to'))
        self.user_defined_region_entry['longitude']['to']['direction'] = tk.Entry(self.user_defined_region_frame, textvariable=self.user_defined_region_text['longitude']['to']['direction'], width=2, justify=tk.CENTER)
        self.user_defined_region_entry['longitude']['to']['direction'].config(validate='all', validatecommand=(validate_user_defined_region_entry, '%P', '%V', 'longitude', 'to', 'direction'))
        if self.current_region == 'user-defined' :
            self.updateUserDefinedRegionEntries()
        self.user_defined_region_from_entry_set = False

        # Create buttons
        self.user_defined_region_ok_button = tk.Button(self.user_defined_region_frame, text='Ok', state=tk.DISABLED, command=self.setUserDefinedRegion)
        if (self.current_user_defined_region_mask > 0).any() :
            self.user_defined_region_ok_button.configure(state=tk.NORMAL)
        cancel_button = tk.Button(self.user_defined_region_frame, text='Cancel', state=tk.NORMAL, command=self.cancelUserDefinedRegion)

        # Arrange fields on frame with labels
        tk.Label(self.user_defined_region_frame, text='Latitude:').grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['latitude']['from']['degrees'].grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text=u'\N{DEGREE SIGN}').grid(row=0, column=2, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['latitude']['from']['direction'].grid(row=0, column=3, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text='to').grid(row=0, column=4, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['latitude']['to']['degrees'].grid(row=0, column=5, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text=u'\N{DEGREE SIGN}').grid(row=0, column=6, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['latitude']['to']['direction'].grid(row=0, column=7, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, textvariable=self.user_defined_region_cursor_text['latitude']).grid(row=0, column=8, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text='').grid(row=0, column=9, sticky=tk.NW+tk.SW, padx=2.5, pady=5)
        tk.Label(self.user_defined_region_frame, text='Longitude:').grid(row=0, column=10, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['longitude']['from']['degrees'].grid(row=0, column=11, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text=u'\N{DEGREE SIGN}').grid(row=0, column=12, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['longitude']['from']['direction'].grid(row=0, column=13, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text='to').grid(row=0, column=14, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['longitude']['to']['degrees'].grid(row=0, column=15, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text=u'\N{DEGREE SIGN}').grid(row=0, column=16, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_entry['longitude']['to']['direction'].grid(row=0, column=17, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, textvariable=self.user_defined_region_cursor_text['longitude']).grid(row=0, column=18, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.user_defined_region_frame, text='').grid(row=0, column=19, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.user_defined_region_ok_button.grid(row=0, column=20, sticky=tk.W, padx=5, pady=2)
        cancel_button.grid(row=0, column=21, sticky=tk.W, padx=0, pady=2)
        self.user_defined_region_frame.grid(row=1, column=0, padx=0, pady=0)
        if self.current_region != 'user-defined' :
            self.user_defined_region_frame.grid_remove()

        # Add next and previous buttons and year for time dependent region masks
        self.time_dependent_region_frame = tk.Frame(self.view_edit_region_frame)
        self.time_dependent_region_previous_button = tk.Button(self.time_dependent_region_frame, text='Previous', state=tk.DISABLED, command=self.setPreviousTimeDependentRegion)
        self.time_dependent_region_next_button = tk.Button(self.time_dependent_region_frame, text='Next', state=tk.DISABLED, command=self.setNextTimeDependentRegion)
        self.time_dependent_region_year_text = tk.StringVar()
        self.time_dependent_region_previous_button.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(self.time_dependent_region_frame, textvariable=self.time_dependent_region_year_text).grid(row=0, column=1, sticky=tk.NW+tk.SW, padx=0, pady=5)
        tk.Label(self.time_dependent_region_frame, text='BP').grid(row=0, column=2, sticky=tk.NW+tk.SW, padx=0, pady=5)
        self.time_dependent_region_next_button.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        self.time_dependent_region_frame.grid(row=1, column=0, padx=0, pady=0)
        if self.region_is_time_dependent[self.current_region] :
            self.time_dependent_region_year_text.set(str(mask_year))
            self.updateTimeDependentPreviousNext(mask_year)
        else :
            self.time_dependent_region_frame.grid_remove()

        self.view_edit_region_frame.grid(row=0, column=0, padx=0, pady=0)

    # Step 3 Method: Validate User-defined Region Entry
    def validateUserDefinedRegionEntry(self, string_value, reason, axis, position, component) : # eg. '%P', '%V', 'latitude', 'from', 'degrees'
        #print 'TODO: validateUserDefinedRegionEntry', string_value, reason, axis, position, component

        # Record previous value
        if reason == 'forced' and self.previous_user_defined_region_changed_via[axis][position][component] == 'key' or reason == 'key' or reason == 'focusout' :
            self.previous_user_defined_region[axis][position][component] = self.user_defined_region_text[axis][position][component].get()
            self.previous_user_defined_region_changed_via[axis][position][component] = 'key'

        if reason == 'key' :
            if string_value :
                if component == 'degrees' :
                    allow_entry = False
                    direction = self.user_defined_region_text[axis][position]['direction'].get()
                    if self.isNonNegativetiveFloat(string_value) :
                        if direction :
                            allow_entry = (float(string_value) <= max(self.user_defined_region_spinbox_values[axis][position][direction]))
                        else :
                            if axis == 'latitude' :
                                allow_entry = (float(string_value) <= 90)
                            elif axis == 'longitude' :
                                allow_entry = (float(string_value) <= 180)
                    else :
                        allow_entry = (string_value == '.')
                    if allow_entry :
                        self.after_idle(lambda: self.updateUserDefinedRegionDisplay())
                        return True
                    else :
                        return False
                elif component == 'direction' :
                    if axis == 'latitude' :
                        if string_value.upper() == 'N' or string_value.upper() == 'S' :
                            self.after_idle(lambda: self.updateUserDefinedRegionDegrees(axis, position, string_value.upper()))
                            return True
                        else :
                            return False
                    elif axis == 'longitude' :
                        if string_value.upper() == 'E' or string_value.upper() == 'W' :
                            self.after_idle(lambda: self.updateUserDefinedRegionDegrees(axis, position, string_value.upper()))
                            return True
                        else :
                            return False
            else :
                self.after_idle(lambda: self.updateUserDefinedRegionDisplay(empty=True))
                return True

        elif reason == 'focusout' :
            if string_value and component == 'degrees' :
                self.after_idle(lambda: self.updateUserDefinedRegionDegrees(axis, position))
            return True

        else :
            return True

    # Step 3 Method: Update User-defined Region Degrees
    def updateUserDefinedRegionDegrees(self, axis, position, direction=None) : # eg. 'latitude', 'from', 'N'
        #print 'TODO: updateUserDefinedRegionDegrees', axis, position, direction

        # Update direction (upper case) and limit degrees when present
        if direction :

            # Set direction
            self.user_defined_region_text[axis][position]['direction'].set(direction)

            # Update degrees spinbox values
            degrees_string = self.user_defined_region_text[axis][position]['degrees'].get()
            self.user_defined_region_entry[axis][position]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][position][direction])))
            self.user_defined_region_text[axis][position]['degrees'].set(degrees_string)

            # Update degrees when appropriate
            if self.isNonNegativetiveFloat(degrees_string) :
                degrees = float(degrees_string)
                if degrees > max(self.user_defined_region_spinbox_values[axis][position][direction]) :
                    self.user_defined_region_text[axis][position]['degrees'].set(str(max(self.user_defined_region_spinbox_values[axis][position][direction])))

            # Update opposite position when not properly offset
            self.updateOppositeUserDefinedRegionEntries(axis, position, direction)

            # Update display
            self.updateUserDefinedRegionDisplay()

        else : # degrees aligned with nearest value (up/down) in spinbox value list
            simulate_button = { 'latitude' : { 'from' : 'buttonup', 'to' : 'buttondown' }, 'longitude' : { 'from' : 'buttondown', 'to' : 'buttonup' } }
            self.userDefinedRegionSpinboxArrowPress(axis, position, button=simulate_button[axis][position])
                
    # Step 3 Method: User-defined Region Spinbox Arrow Press
    def userDefinedRegionSpinboxArrowPress(self, axis, position, button=None) : # eg. 'latitude', 'from'

        # Identify button pressed
        simulated_button_press = bool(button)
        if not simulated_button_press :
            button = self.user_defined_region_entry[axis][position]['degrees'].identify(self.winfo_pointerx()-self.user_defined_region_entry[axis][position]['degrees'].winfo_rootx(), self.winfo_pointery()-self.user_defined_region_entry[axis][position]['degrees'].winfo_rooty())
        #print 'TODO: userDefinedRegionSpinboxArrowPress', axis, position, button

        if button == 'entry' or button == '' : # happens if user moves mouse quickly after button press
            current_value_list = np.genfromtxt(StringIO(self.user_defined_region_entry[axis][position]['degrees']['values'])).tolist()
            if self.isNonNegativetiveFloat(self.previous_user_defined_region[axis][position]['degrees']) :
                previous_value = float(self.previous_user_defined_region[axis][position]['degrees'])
            else :
                previous_value = current_value_list[0]
            if self.isNonNegativetiveFloat(self.user_defined_region_text[axis][position]['degrees'].get()) :
                current_value = float(self.user_defined_region_text[axis][position]['degrees'].get())
            else :
                current_value = current_value_list[0]
            if current_value_list.index(current_value) > current_value_list.index(previous_value) :
                button = 'buttonup'
            elif current_value_list.index(current_value) < current_value_list.index(previous_value) :
                button = 'buttondown'
            elif current_value_list.index(current_value) == 0 :
                button = 'buttondown'
            else :
                button = 'buttonup'

        # Get the current direction
        direction = self.user_defined_region_text[axis][position]['direction'].get()

        # Resolve opposites and offset and button directions
        opposite = { 'from' : 'to', 'to' : 'from', 'N' : 'S', 'S' : 'N', 'E' : 'W', 'W' : 'E' }
        offset_direction = { 'latitude' : { 'from' : 'N', 'to' : 'S' }, 'longitude' : { 'from' : 'W', 'to' : 'E' } }
        button_axis_direction = { 'buttonup' : { 'latitude' : 'N', 'longitude' : 'E' }, 'buttondown' : { 'latitude' : 'S', 'longitude' : 'W' } }

        # When it was blank start at 0 or offset position
        if self.previous_user_defined_region[axis][position]['degrees'] == '' :
            if self.user_defined_region_text[axis][opposite[position]]['degrees'].get() == '' :
                self.user_defined_region_text[axis][position]['degrees'].set('0.0')
            else : # opposite position set
                opposite_position_degrees = float(self.user_defined_region_text[axis][opposite[position]]['degrees'].get())
                opposite_position_direction = self.user_defined_region_text[axis][opposite[position]]['direction'].get()
                if opposite_position_degrees == 0.0 or opposite_position_direction == offset_direction[axis][position] :
                    direction = offset_direction[axis][position]
                    self.user_defined_region_text[axis][position]['direction'].set(direction)
                    self.user_defined_region_entry[axis][position]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][position][offset_direction[axis][position]])))
                    self.user_defined_region_text[axis][position]['degrees'].set(str(opposite_position_degrees + 2.5))
                else :
                    self.user_defined_region_text[axis][position]['degrees'].set('0.0')                

        # When '0.0' or direction empty determine direction given button press
        update_direction = False
        if ( (self.user_defined_region_text[axis][position]['degrees'].get() == '0.0' and self.previous_user_defined_region_changed_via[axis][position]['degrees'] != 'key') or not direction ) :
            update_direction = True
            direction = button_axis_direction[button][axis]
            if not simulated_button_press :
                self.user_defined_region_text[axis][position]['direction'].set(direction)

        # Keyed entry aligned with nearest value (up/down) in spinbox value list
        if self.previous_user_defined_region_changed_via[axis][position]['degrees'] == 'key' :
            last_unforced_value = self.previous_user_defined_region[axis][position]['degrees']
            if self.isNonNegativetiveFloat(last_unforced_value) :
                #print 'using', last_unforced_value, 'rather than', self.user_defined_region_text[axis][position]['degrees'].get()
                last_unforced_value = float(last_unforced_value)
                if last_unforced_value in self.user_defined_region_spinbox_values[axis][position][direction] : # use value
                    self.user_defined_region_text[axis][position]['degrees'].set(str(last_unforced_value))
                else : # find nearest
                    found_index = (np.array(self.user_defined_region_spinbox_values[axis][position][direction]) > last_unforced_value)
                    if found_index[0] : # invert
                        found_index = (found_index == False)
                    if found_index.any() :
                        if button == 'buttonup' :
                            index = found_index.tolist().index(True)
                        elif button == 'buttondown' :
                            index = found_index.tolist().index(True) - 1
                        self.user_defined_region_text[axis][position]['degrees'].set(str(self.user_defined_region_spinbox_values[axis][position][direction][index]))
                    else :
                        self.user_defined_region_text[axis][position]['degrees'].set(str(max(self.user_defined_region_spinbox_values[axis][position][direction])))
            else :
                self.user_defined_region_text[axis][position]['degrees'].set('0.0')

        # When direction change or '0.0' update spinbox
        if update_direction or self.user_defined_region_text[axis][position]['degrees'].get() == '0.0' :
            current_degrees = self.user_defined_region_text[axis][position]['degrees'].get()
            self.user_defined_region_entry[axis][position]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][position][direction])))
            if current_degrees == '0.0' and self.previous_user_defined_region_changed_via[axis][position]['degrees'] != 'key' and self.previous_user_defined_region[axis][position]['degrees'] == '0.0' :
                self.user_defined_region_text[axis][position]['degrees'].set('2.5')
            else :
                self.user_defined_region_text[axis][position]['degrees'].set(current_degrees)

        # Wrap around longitude
        button_axis_direction = { 'buttonup' : { 'latitude' : 'N', 'longitude' : 'E' }, 'buttondown' : { 'latitude' : 'S', 'longitude' : 'W' } }
        if axis == 'longitude' and direction == button_axis_direction[button]['longitude'] and self.previous_user_defined_region[axis][position]['degrees'] == str(max(self.user_defined_region_spinbox_values[axis][position][direction])) :
            self.user_defined_region_entry[axis][position]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][position][opposite[direction]])))
            self.user_defined_region_text[axis][position]['degrees'].set(str(max(self.user_defined_region_spinbox_values[axis][position][opposite[direction]])))
            self.user_defined_region_text[axis][position]['direction'].set(opposite[direction])

        # Update previous
        self.previous_user_defined_region[axis][position]['degrees'] = self.user_defined_region_text[axis][position]['degrees'].get()
        self.previous_user_defined_region[axis][position]['direction'] = self.user_defined_region_text[axis][position]['direction'].get()
        self.previous_user_defined_region_changed_via[axis][position]['degrees'] = 'forced'
        self.previous_user_defined_region_changed_via[axis][position]['direction'] = 'forced'

        # Update opposite position when not properly offset
        self.updateOppositeUserDefinedRegionEntries(axis, position, direction)

        # Update display
        self.updateUserDefinedRegionDisplay()

    # Step 3 Method: Update User-defined Region Degrees
    def updateOppositeUserDefinedRegionEntries(self, axis, position, direction=None) : # eg. 'latitude', 'from', 'N'
        #print 'TODO: updateOppositeUserDefinedRegionEntries', axis, position, direction

        # Get direction when not defined
        if not direction :
            direction = self.user_defined_region_text[axis][position]['direction'].get()

        # Resolve opposites and offset directions
        opposite = { 'from' : 'to', 'to' : 'from', 'N' : 'S', 'S' : 'N', 'E' : 'W', 'W' : 'E' }
        offset_direction = { 'latitude' : { 'from' : 'N', 'to' : 'S' }, 'longitude' : { 'from' : 'W', 'to' : 'E' } }

        # Update opposite position when not properly offset
        if self.isNonNegativetiveFloat(self.user_defined_region_text[axis][position]['degrees'].get()) and self.isNonNegativetiveFloat(self.user_defined_region_text[axis][opposite[position]]['degrees'].get()) :
            degrees = float(self.user_defined_region_text[axis][position]['degrees'].get())
            opposite_position_degrees = float(self.user_defined_region_text[axis][opposite[position]]['degrees'].get())
            opposite_position_direction = self.user_defined_region_text[axis][opposite[position]]['direction'].get()
            updated_opposite = False
            if axis == 'latitude' : # always ensure offset 
                if direction == offset_direction[axis][position] :
                    if opposite_position_direction == offset_direction[axis][position] and degrees <= opposite_position_degrees :
                        if degrees > 0.0 :
                            self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees - 2.5))
                        else : # change direction of opposite
                            self.user_defined_region_text[axis][opposite[position]]['direction'].set(opposite[opposite_position_direction])
                            self.user_defined_region_entry[axis][opposite[position]]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][opposite[position]][opposite[opposite_position_direction]])))
                            self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees + 2.5))
                        updated_opposite = True
                    elif opposite_position_direction == opposite[offset_direction[axis][position]] and degrees == 0.0 and opposite_position_degrees == 0.0 :
                        self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees + 2.5))
                        updated_opposite = True
                elif opposite_position_direction == offset_direction[axis][position] or degrees >= opposite_position_degrees :
                    self.user_defined_region_text[axis][opposite[position]]['direction'].set(direction)
                    self.user_defined_region_entry[axis][opposite[position]]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][opposite[position]][direction])))
                    self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees + 2.5))
                    updated_opposite = True
            elif axis == 'longitude' : # offset only when equal
                if degrees == opposite_position_degrees :
                    if degrees > 0.0 and direction == opposite_position_direction :
                        if direction == offset_direction[axis][position] :
                            self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees - 2.5))
                        else :
                            self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees + 2.5))
                        updated_opposite = True
                    elif degrees == 0.0 :
                        if opposite_position_direction != offset_direction[axis][opposite[position]] :
                            self.user_defined_region_text[axis][opposite[position]]['direction'].set(offset_direction[axis][opposite[position]])
                            self.user_defined_region_entry[axis][opposite[position]]['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values[axis][opposite[position]][offset_direction[axis][opposite[position]]])))
                        self.user_defined_region_text[axis][opposite[position]]['degrees'].set(str(degrees + 2.5))
                        updated_opposite = True
            if updated_opposite : # Update previous for opposite position  
                self.previous_user_defined_region[axis][opposite[position]]['degrees'] = self.user_defined_region_text[axis][opposite[position]]['degrees'].get()
                self.previous_user_defined_region[axis][opposite[position]]['direction'] = self.user_defined_region_text[axis][opposite[position]]['direction'].get()
                self.previous_user_defined_region_changed_via[axis][opposite[position]]['degrees'] = 'forced'
                self.previous_user_defined_region_changed_via[axis][opposite[position]]['direction'] = 'forced'

    # Step 3 Method: Create Region Figure
    def createRegionFigure(self, update=False, user_defined_update=False, time_dependent_update=False, time_dependent_year=None) :

        # Setup the latitude and longitude variables
        lats = np.arange(90, -92.5, -2.5)
        lons = np.arange(self.region_bounding_box[self.current_region]['centre']-180, self.region_bounding_box[self.current_region]['centre']+182.5, 2.5)
        lons, lats = np.meshgrid(lons,lats)

        # Select the region mask when time dependent series
        if self.region_is_time_dependent[self.current_region] and time_dependent_year != None :
            region_mask = self.region_mask[time_dependent_year]
        else :
            region_mask = self.region_mask

        if user_defined_update or time_dependent_update :
            plot_data = region_mask + (region_mask < 1)*0.3
        else :

            # Shift the region_mask if required
            shifted_region_mask = region_mask
            if self.region_bounding_box[self.current_region]['centre'] == 180 :
                shifted_region_mask = np.zeros((72, 144))
                shifted_region_mask[:,0:72] = region_mask[:,72:144]
                shifted_region_mask[:,72:144] = region_mask[:,0:72]

            # Basemap resolution: c (crude), l (low), i (intermediate), h (high), f (full)
            if self.current_region in ['user-defined', 'globe', 'land', 'ocean', 'land-0-21KBP', 'ocean-0-21KBP', 'northern-hemisphere', 'southern-hemisphere', 'equatorial-pacific', 'n3', 'n3-4', 'n4', 'rola'] :
                basemap_resolution = 'c'
            elif self.current_region in ['japan', 'middle-east', 'alaska'] :
                basemap_resolution = 'i'
            else :
                basemap_resolution = 'l'

            # Set/calculate dimensions and margins
            maximum_width = 15.0
            maximum_height = 9.0
            margin = 0.2
            region_box = self.region_bounding_box[self.current_region]
            if self.current_region in ['antarctica'] :
                plot_width_to_height_ratio = 1.0
            else :
                plot_width_to_height_ratio = 1.0*(region_box['lon'][1] - region_box['lon'][0])/(region_box['lat'][1] - region_box['lat'][0])
            if plot_width_to_height_ratio >= (maximum_width/maximum_height) :
                width = maximum_width
                height = (width - 2*margin)/plot_width_to_height_ratio + 2*margin
            else :
                height = maximum_height
                width = (height - 2*margin)*plot_width_to_height_ratio + 2*margin

            # Setup plot
            map_projection = 'cyl'
            bounding_lat = None
            if self.current_region == 'antarctica' :
                map_projection = 'spaeqd'
                bounding_lat = -60
            if update :
                self.view_edit_region_figure.set_size_inches(width, height, forward=True)
            else :
                self.view_edit_region_figure = Figure(figsize=(width, height), frameon=False, linewidth=10, dpi=100, tight_layout=True)
                self.view_edit_region_plot_axes = self.view_edit_region_figure.add_subplot(111)
            self.view_edit_region_figure.subplots_adjust(left=(margin/width), right=(1.0-margin/width), bottom=(margin/height), top=(1.0-margin/height))
            self.region_basemap = Basemap(ax=self.view_edit_region_plot_axes,
                                          lon_0=self.region_bounding_box[self.current_region]['centre'],
                                          llcrnrlat=self.region_bounding_box[self.current_region]['lat'][0],
                                          urcrnrlat=self.region_bounding_box[self.current_region]['lat'][1],
                                          llcrnrlon=self.region_bounding_box[self.current_region]['lon'][0],
                                          urcrnrlon=self.region_bounding_box[self.current_region]['lon'][1],
                                          resolution=basemap_resolution,
                                          projection=map_projection,
                                          boundinglat=bounding_lat)
            plot_data = shifted_region_mask + (shifted_region_mask < 1)*0.3

        # Plot the map
        self.region_basemap.pcolor(lons, lats, plot_data, shading='flat', cmap=plt.cm.gray, latlon=True, vmin=0, vmax=1)
        self.region_basemap.drawcoastlines()

    # Step 3 Method: Set User-defined Region
    def setUserDefinedRegion(self) :
        self.current_user_defined_region_mask = self.region_mask
        self.view_edit_region_window.destroy()

    # Step 3 Method: Cancel User-defined Region
    def cancelUserDefinedRegion(self) :
        self.region_mask = self.current_user_defined_region_mask
        self.view_edit_region_window.destroy()

    # Step 3 Method: Update Region Window
    def updateRegionWindow(self, button_pressed) :
        #print 'TODO: updateRegionWindow', button_pressed

        # Handle updates when button not pressed
        update = False
        if not button_pressed : # only update if present
            if hasattr(self, 'view_edit_region_window') :
                if self.view_edit_region_window.children :
                    update = True
        else :
            update = True

        # Exit if update not required
        if not update :
            return True

        # Select the appropriate starting region mask when time dependent series
        mask_year = None
        if self.region_is_time_dependent[self.current_region] :
            mask_year = self.calculateTimeDependentRegionYear()

        # Re-plot the region map
        self.updateRegionMap(time_dependent_year=mask_year)

        # Buttons and coordinates?
        if self.current_region == 'user-defined' :
            self.user_defined_region_frame.grid()
        else :
            self.user_defined_region_frame.grid_remove()
        if self.region_is_time_dependent[self.current_region] :
            self.time_dependent_region_year_text.set(str(mask_year))
            self.updateTimeDependentPreviousNext(mask_year)
            self.time_dependent_region_frame.grid()
        else :
            self.time_dependent_region_frame.grid_remove()

    # Step 3 Method: Update Region Map
    def updateRegionMap(self, user_defined_update=False, time_dependent_update=False, time_dependent_year=None) :

        # Re-plot the region map
        self.view_edit_region_plot_axes.clear()
        self.createRegionFigure(update=True, user_defined_update=user_defined_update, time_dependent_update=time_dependent_update, time_dependent_year=time_dependent_year)
        if user_defined_update or time_dependent_update:
            self.view_edit_region_canvas.draw()
        else :
            self.view_edit_region_window.title(self.view_edit_region_button_text.get())
            self.view_edit_region_canvas.get_tk_widget().grid_remove()
            self.view_edit_region_canvas = FigureCanvasTkAgg(self.view_edit_region_figure, master=self.view_edit_region_frame)
            self.view_edit_region_canvas.show()
            self.view_edit_region_canvas.get_tk_widget().grid(row=0, column=0)

        if self.current_region == 'user-defined' :
            if (self.region_mask > 0).any() :
                self.user_defined_region_ok_button.configure(state=tk.NORMAL)
            else :
                self.user_defined_region_ok_button.configure(state=tk.DISABLED)
        elif self.region_is_time_dependent[self.current_region] :
            self.updateTimeDependentPreviousNext(time_dependent_year)

    # Step 3 Method: Update Region Mask
    def updateRegionMask(self, top_left, bottom_right) :
        #print 'updateRegionMask: top_left', top_left, 'bottom_right', bottom_right
        self.region_mask = self.region_mask*0
        if bottom_right[1] >= top_left[1] :
            self.region_mask[top_left[0]:bottom_right[0]+1, top_left[1]:bottom_right[1]+1] = 1
        else : # longitude wraps around
            self.region_mask[top_left[0]:bottom_right[0]+1, top_left[1]:] = 1
            self.region_mask[top_left[0]:bottom_right[0]+1, :bottom_right[1]+1] = 1

    # Step 3 Method: Update User-defined Region Display
    def updateUserDefinedRegionDisplay(self, empty=False) :
        #print 'TODO: updateUserDefinedRegionDisplay'

        # Check that user-defined entries are complete and valid
        entries_complete_and_valid = False
        lat_from_dir = self.user_defined_region_text['latitude']['from']['direction'].get()
        lat_to_dir = self.user_defined_region_text['latitude']['to']['direction'].get()
        lon_from_dir = self.user_defined_region_text['longitude']['from']['direction'].get()
        lon_to_dir = self.user_defined_region_text['longitude']['to']['direction'].get()
        if not empty and lat_from_dir and lat_to_dir and lon_from_dir and lon_to_dir :
            lat_from_deg = self.user_defined_region_text['latitude']['from']['degrees'].get()
            lat_to_deg = self.user_defined_region_text['latitude']['to']['degrees'].get()
            lon_from_deg = self.user_defined_region_text['longitude']['from']['degrees'].get()
            lon_to_deg = self.user_defined_region_text['longitude']['to']['degrees'].get()
            if self.isNonNegativetiveFloat(lat_from_deg) and self.isNonNegativetiveFloat(lat_to_deg) and self.isNonNegativetiveFloat(lon_from_deg) and self.isNonNegativetiveFloat(lon_to_deg) :
                if ( float(lat_from_deg) in self.user_defined_region_spinbox_values['latitude']['from'][lat_from_dir] and
                     float(lat_to_deg) in self.user_defined_region_spinbox_values['latitude']['to'][lat_to_dir] and
                     float(lon_from_deg) in self.user_defined_region_spinbox_values['longitude']['from'][lon_from_dir] and
                     float(lon_to_deg) in self.user_defined_region_spinbox_values['longitude']['to'][lon_to_dir] ) :
                    direction_multiplier = { 'latitude' : { 'N' : 1, 'S' : -1 }, 'longitude' : { 'E' : 1, 'W' : -1 } }
                    lat_from_deg = float(lat_from_deg) * direction_multiplier['latitude'][lat_from_dir]
                    lat_to_deg = float(lat_to_deg) * direction_multiplier['latitude'][lat_to_dir]
                    lon_from_deg = float(lon_from_deg) * direction_multiplier['longitude'][lon_from_dir]
                    lon_to_deg = float(lon_to_deg) * direction_multiplier['longitude'][lon_to_dir]
                    if lat_from_deg > lat_to_deg and lon_from_deg != lon_to_deg :
                        entries_complete_and_valid = True

                        # Resolve and update region mask
                        from_coord = [np.arange(90, -90, -2.5).tolist().index(lat_from_deg), np.arange(-180, 180, 2.5).tolist().index(lon_from_deg)]
                        to_coord = [np.arange(90, -90, -2.5).tolist().index(lat_to_deg+2.5), np.arange(-180, 180, 2.5).tolist().index(lon_to_deg-2.5)]
                        self.updateRegionMask(from_coord, to_coord)

        # Clear region mask when not complete and valid
        if not entries_complete_and_valid :
            self.region_mask = self.region_mask*0

        # Update map
        self.updateRegionMap(user_defined_update=True)

    # Step 3 Method: Region Button Press Event
    def regionButtonPressEvent(self, event) :
        #print 'TODO: regionButtonPressEvent', event.xdata, event.ydata
        self.region_select_button_held = True
        if self.current_region == 'user-defined' and event.xdata and event.ydata :
            row = (np.arange(90, -90, -2.5) < event.ydata).tolist().count(False) - 1
            col = (np.arange(-180, 180, 2.5) > event.xdata).tolist().count(False) - 1
            self.region_select_top_left = [row, col] # [0, 0] to [71, 143]
            self.updateRegionMask(self.region_select_top_left, self.region_select_top_left)
            self.updateRegionMap(user_defined_update=True)
            self.updateUserDefinedRegionEntries(update='from', clear='to')

    # Step 3 Method: Region Button Release Event
    def regionButtonReleaseEvent(self, event) :
        #print 'TODO: regionButtonReleaseEvent', event.xdata, event.ydata
        if self.current_region == 'user-defined' and self.region_select_button_held and event.xdata and event.ydata :
            row = (np.arange(90, -90, -2.5) < event.ydata).tolist().count(False) - 1
            col = (np.arange(-180, 180, 2.5) > event.xdata).tolist().count(False) - 1
            bottom_right = self.region_select_top_left[:]
            if row > bottom_right[0] :
                bottom_right[0] = row
            if col > bottom_right[1] :
                bottom_right[1] = col
            self.updateRegionMask(self.region_select_top_left, bottom_right)
            self.updateRegionMap(user_defined_update=True)
        if self.current_region == 'user-defined' :
            self.updateUserDefinedRegionEntries(update='all')
        self.region_select_button_held = False

    # Step 3 Method: Region Motion Notify Event
    def regionMotionNotifyEvent(self, event) :
        if self.current_region == 'user-defined' :
            if event.xdata and event.ydata :
                row = (np.arange(90, -90, -2.5) < event.ydata).tolist().count(False) - 1
                col = (np.arange(-180, 180, 2.5) > event.xdata).tolist().count(False) - 1
                if self.region_select_button_held :
                    if not self.user_defined_region_from_entry_set :
                        self.region_select_top_left = [row, col]
                    bottom_right = self.region_select_top_left[:]
                    if row > bottom_right[0] :
                        bottom_right[0] = row
                    if col > bottom_right[1] :
                        bottom_right[1] = col
                    self.updateRegionMask(self.region_select_top_left, bottom_right)
                    self.updateRegionMap(user_defined_update=True)
                    self.updateUserDefinedRegionEntries(update='to')

    # Step 3 Method: Update User-defined Region Entries
    def updateUserDefinedRegionEntries(self, update='all', clear='none') :
        #print 'TODO: updateUserDefinedRegionEntries'
        if (self.region_mask > 0).any() :
            if update in ['all', 'from'] or (update == 'to' and not self.user_defined_region_from_entry_set) :
                lat_from = np.arange(90, -90, -2.5)[self.region_mask.sum(1).nonzero()[0].min()]
                if lat_from >= 0 :
                    lat_from_degrees = str(round(lat_from, 1))
                    lat_from_direction = 'N'
                else : 
                    lat_from_degrees = str(round(-1*lat_from, 1))
                    lat_from_direction = 'S'
                lon_indices = self.region_mask.sum(0).nonzero()[0].tolist()
                if len(lon_indices) < 144 and lon_indices.count(0) and lon_indices.count(143) :
                    lon_from = np.arange(-180, 180, 2.5)[lon_indices[(np.array(lon_indices) != np.insert(np.array(lon_indices[:-1])+1,0,0)).nonzero()[0][0]]]
                else :
                    lon_from = np.arange(-180, 180, 2.5)[min(lon_indices)]
                if lon_from >= 0 :
                    lon_from_degrees = str(round(lon_from, 1))
                    lon_from_direction = 'E'
                else : 
                    lon_from_degrees = str(round(-1*lon_from, 1))
                    lon_from_direction = 'W'
                if update == 'all' :
                    self.user_defined_region_entry['latitude']['from']['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values['latitude']['from'][lat_from_direction])))
                    self.user_defined_region_entry['longitude']['from']['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values['longitude']['from'][lon_from_direction])))
                self.user_defined_region_text['latitude']['from']['degrees'].set(lat_from_degrees)
                self.user_defined_region_text['latitude']['from']['direction'].set(lat_from_direction)
                self.user_defined_region_text['longitude']['from']['degrees'].set(lon_from_degrees)
                self.user_defined_region_text['longitude']['from']['direction'].set(lon_from_direction)
                self.user_defined_region_from_entry_set = True
            if update in ['all', 'to'] :
                lat_to = np.arange(87.5, -92.5, -2.5)[self.region_mask.sum(1).nonzero()[0].max()]
                if lat_to >= 0 :
                    lat_to_degrees = str(round(lat_to, 1))
                    lat_to_direction = 'N'
                else : 
                    lat_to_degrees = str(round(-1*lat_to, 1))
                    lat_to_direction = 'S'
                lon_indices = self.region_mask.sum(0).nonzero()[0].tolist()
                if len(lon_indices) < 144 and lon_indices.count(0) and lon_indices.count(143) :
                    lon_to = np.arange(-177.5, 182.5, 2.5)[lon_indices[(np.array(lon_indices) != np.append(np.array(lon_indices[1:])-1,143)).nonzero()[0][0]]]
                else :
                    lon_to = np.arange(-177.5, 182.5, 2.5)[max(lon_indices)]
                if lon_to >= 0 :
                    lon_to_degrees = str(round(lon_to, 1))
                    lon_to_direction = 'E'
                else : 
                    lon_to_degrees = str(round(-1*lon_to, 1))
                    lon_to_direction = 'W'
                if update == 'all' :
                    self.user_defined_region_entry['latitude']['to']['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values['latitude']['to'][lat_to_direction])))
                    self.user_defined_region_entry['longitude']['to']['degrees'].config(values=tuple(map(str, self.user_defined_region_spinbox_values['longitude']['to'][lon_to_direction])))
                self.user_defined_region_text['latitude']['to']['degrees'].set(lat_to_degrees)
                self.user_defined_region_text['latitude']['to']['direction'].set(lat_to_direction)
                self.user_defined_region_text['longitude']['to']['degrees'].set(lon_to_degrees)
                self.user_defined_region_text['longitude']['to']['direction'].set(lon_to_direction)
            if update == 'all' :
                self.previous_user_defined_region = self.copy_dict_mapping_values(self.user_defined_region_text)
        else :
            clear = 'all'
        if clear in ['all', 'from'] :
            self.user_defined_region_text['latitude']['from']['degrees'].set('')
            self.user_defined_region_text['latitude']['from']['direction'].set('')
            self.user_defined_region_text['longitude']['from']['degrees'].set('')
            self.user_defined_region_text['longitude']['from']['direction'].set('')
        if clear in ['all', 'to'] :
            self.user_defined_region_text['latitude']['to']['degrees'].set('')
            self.user_defined_region_text['latitude']['to']['direction'].set('')
            self.user_defined_region_text['longitude']['to']['degrees'].set('')
            self.user_defined_region_text['longitude']['to']['direction'].set('')
        if clear in ['all', 'from', 'to'] :    
            self.previous_user_defined_region = self.copy_dict_mapping_values(self.user_defined_region_text)

    # Step 3 Method: Region Axes Enter Event
    def regionAxesEnterEvent(self, event) :
        if self.current_region == 'user-defined' :
            self.view_edit_region_canvas.get_tk_widget().configure(cursor='tcross')

    # Step 3 Method: Region Axes Leave Event
    def regionAxesLeaveEvent(self, event) :
        self.view_edit_region_canvas.get_tk_widget().configure(cursor='arrow')

    # Step 3 Method: Update Time-dependent Region Previous Next
    def updateTimeDependentPreviousNext(self, mask_year) :
        if mask_year < 21000 : #(mask_year + self.calculateTimeDependentRegionYearStep()) <= 21000 :
            self.time_dependent_region_previous_button.configure(state=tk.NORMAL)
        else :
            self.time_dependent_region_previous_button.configure(state=tk.DISABLED)
        if mask_year > 0 : #(mask_year - self.calculateTimeDependentRegionYearStep()) >= 0 :
            self.time_dependent_region_next_button.configure(state=tk.NORMAL)
        else :
            self.time_dependent_region_next_button.configure(state=tk.DISABLED)

    # Step 3 Method: Calculate Time-dependent Region Year
    def calculateTimeDependentRegionYear(self) :
        period_bp_from = int(self.period_text['from'].get())
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD
            period_bp_from = 1950 - period_bp_from
        return self.data_file_helper.nearestTimeDependentRegionMaskYear(period_bp_from)

    # Step 3 Method: Calculate Time-dependent Region Year Step
    def calculateTimeDependentRegionYearStep(self) :
        if self.current_valid_interval_step_value > 100 :
            return int(round(self.current_valid_interval_step_value/100.0,0)*100)
        else :
            return 100

    # Step 3 Method: Set Previous Time-dependent Region
    def setPreviousTimeDependentRegion(self) :
        #print 'TODO: setPreviousTimeDependentRegion'
        previous_year = int(self.time_dependent_region_year_text.get()) + self.calculateTimeDependentRegionYearStep()
        if previous_year > 21000 :
            previous_year = 21000
        self.time_dependent_region_year_text.set(str(previous_year))
        self.updateRegionMap(time_dependent_update=True, time_dependent_year=previous_year)

    # Step 3 Method: Set Next Time-dependent Region
    def setNextTimeDependentRegion(self) :
        #print 'TODO: setNextTimeDependentRegion'
        next_year = int(self.time_dependent_region_year_text.get()) - self.calculateTimeDependentRegionYearStep()
        if next_year < 0 :
            next_year = 0
        self.time_dependent_region_year_text.set(str(next_year))
        self.updateRegionMap(time_dependent_update=True, time_dependent_year=next_year)

    ## Step 4: Period Methods ##############################################################################################################################################

    # Step 4 Method: Select Period Postfix: the user opens options
    def validatePeriod(self, string_value, reason, context) :
        #print 'TODO: validatePeriod', string_value, reason, context 

        # Anticipate warning/error conditions not satisfied
        warning_pending = False

        # Reset generation
        if reason == 'key' :
            self.resetGeneration()

        # Record previous value
        if reason == 'forced' or reason == 'key' :
            self.previous_period_text_value[context] = self.period_text[context].get()
            self.previous_period_changed_via[context] = reason

        # Conditions for showing the warning/error
        show_warnings_if_any = False
        if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too

            show_warnings_if_any = True

            # Handle case when focus has moved to a (option) menu
            if self.validation_warning_pending :
                self.validation_warning_pending = False
            elif self.force_shift_focus :
                self.force_shift_focus = False
                return True

        # Resolve postfix key
        if self.period_postfix_text[context].get() == self.period_postfix_keys[0] : # BP
            postfix_key = 'BP'
        elif self.period_postfix_text[context].get() == self.period_postfix_keys[1] : # AD
            postfix_key = 'AD'

        # Ensure minimum and maximum period constraints are met
        if self.isNonNegativeInteger(string_value) :
            minimum_value = self.period_ranges[postfix_key]['min']
            if postfix_key == 'BP' :
##                if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                    maximum_value = self.period_ranges[postfix_key]['max'] - self.interval_size_range['min']/2 - 1
##                else :
##                    maximum_value = self.period_ranges[postfix_key]['max'] - self.interval_size_range['min']/2
                maximum_value = self.period_ranges['BP']['max-entry']
            else : # AD
                maximum_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 + int(not bool(self.interval_size_range['min']%2))
            min_interval_step = min(self.current_interval_step_values)
            if context == 'from' and postfix_key == 'AD' :
                maximum_value = maximum_value - min_interval_step
            if context == 'until' and postfix_key == 'BP' :
                maximum_value = maximum_value - min_interval_step
            if int(string_value) < minimum_value or int(string_value) > maximum_value :
                if context == 'until' and postfix_key == 'AD' :
                    warning_pending = True
                else :
                    warning_pending = context
                if show_warnings_if_any :
                    self.currently_showing_warning_message = True
                    if postfix_key == 'BP' :
                        warning = 'Period ' + context + ' value must be between ' + str(maximum_value) + ' BP and ' + str(minimum_value) + ' BP'
                    elif postfix_key == 'AD' :
                        warning = 'Period ' + context + ' value must be between ' + str(minimum_value) + ' AD and ' + str(maximum_value) + ' AD'
                    showwarning('Period value out of range', warning)
                    self.currently_showing_warning_message = False
                    if int(string_value) < minimum_value :
                        self.after_idle(lambda: self.period_text[context].set(str(minimum_value)))
                        self.after_idle(lambda: self.updateIntervalStep())
                        if context == 'from' :
                            self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                        self.after_idle(lambda: self.matchIntervalSizeWithStep())
                        self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                    elif int(string_value) > maximum_value :
                        self.after_idle(lambda: self.period_text[context].set(str(maximum_value)))
                        self.after_idle(lambda: self.updateIntervalStep())
                        if context == 'from' :
                            self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                        self.after_idle(lambda: self.matchIntervalSizeWithStep())
                        self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                    return True
            elif (reason == 'focusout' or reason == 'forced') : # set current valid value
                self.current_valid_period_value[context] = int(string_value)
        elif not string_value :
            if show_warnings_if_any : # replace with last valid value rather than warn
                self.after_idle(lambda: self.period_text[context].set(str(self.current_valid_period_value[context])))

        # Get current from and until values
        if context == 'from' :
            from_string_value = string_value
            until_string_value = self.period_text['until'].get()
        elif context == 'until' :
            from_string_value = self.period_text['from'].get()
            until_string_value = string_value

        # Ensure from <= until period is satisfied
        if self.isNonNegativeInteger(from_string_value) and self.isNonNegativeInteger(until_string_value) :

            # Convert period years to AD
            if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
                period_from_ad = 1950 - int(from_string_value)
            else : # AD
                period_from_ad = int(from_string_value)
            if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
                period_until_ad = 1950 - int(until_string_value)
            else : # AD
                period_until_ad = int(until_string_value)

            # Alter until value or warn user
            if period_from_ad > period_until_ad :
                if context == 'from' and show_warnings_if_any :
                    self.after_idle(lambda: self.updateIntervalStep())
                    self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                    self.after_idle(lambda: self.matchPeriodUntilWithFrom(until_before_from=True))
                    self.after_idle(lambda: self.matchIntervalSizeWithStep())
                    self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                elif context == 'until' :
                    if self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD
                        warning_pending = True
                    else :
                        warning_pending = context
                    if show_warnings_if_any :
                        self.currently_showing_warning_message = True
                        showwarning('Period until is before from', 'Period until must no greater than period from')
                        self.currently_showing_warning_message = False
                        return True
            elif reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too
                self.after_idle(lambda: self.updateIntervalStep())
                if context == 'from' :
                    self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                self.after_idle(lambda: self.matchIntervalSizeWithStep())
                self.after_idle(lambda: self.updateDeltaReferenceIntervals())

        if reason == 'key' :
            self.validation_warning_pending = warning_pending
            if string_value :
                # Limit data entry
                return self.isNonNegativeInteger(string_value)
            else :
                return True

        elif reason == 'focusin' :
            if self.force_shift_focus :
                self.focus_set()
                return True
            self.validation_warning_pending = warning_pending
            return True

        else :
            return True

    # Step 4 Method: Match Period Until With From
    def matchPeriodUntilWithFrom(self, until_before_from=False) :
        #print 'TODO: matchPeriodUntilWithFrom', until_before_from, self.period_postfix_text['from'].get()

        # Resolve postfix key
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP (=> from also BP)
            postfix_key = 'BP'
        elif self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # AD
            postfix_key = 'AD'

        # Get data type and action
        data_type = self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())]
        data_action = self.data_action_keys[self.data_action_selection.index(self.data_action_text.get())]

        # Get period and interval values and convert to AD if required
        from_value = int(self.period_text['from'].get())
        until_value = int(self.period_text['until'].get())
        #self.updateIntervalStep()
        interval_step = self.current_valid_interval_step_value
##        if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##            period_ranges_ad = { 'min' : self.period_ranges['AD']['min'], 'max' : (self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - 1) }
##        else :
        period_ranges_ad = { 'min' : self.period_ranges['AD']['min'], 'max' : (self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 + int(not bool(self.interval_size_range['min']%2))) }
        period_ranges = period_ranges_ad
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            from_value = 1950 - from_value
            #period_ranges = { 'min' : (1950 - self.period_ranges['BP']['max'] + self.interval_size_range['min']/2), 'max' : (1950 - self.period_ranges['BP']['min']) }
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            until_value = 1950 - until_value
##            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                period_ranges = { 'min' : (1950 - self.period_ranges['BP']['max'] + self.interval_size_range['min']/2 + 1), 'max' : (1950 - self.period_ranges['BP']['min']) }
##            else :
##                period_ranges = { 'min' : (1950 - self.period_ranges['BP']['max'] + self.interval_size_range['min']/2), 'max' : (1950 - self.period_ranges['BP']['min']) }
            period_ranges = { 'min' : (1950 - self.period_ranges['BP']['max-entry']), 'max' : (1950 - self.period_ranges['BP']['min']) }

        # Does a BP until range need to be extended or changed into AD?
        step_after_from_value = from_value + interval_step # - 1
        if (self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and step_after_from_value > period_ranges['max']) or self.period_postfix_text['from'].get() == self.period_postfix_keys[1] :
            self.period_postfix_text['until'].set(self.period_postfix_keys[1]) # change to AD
            period_ranges = period_ranges_ad

        # Gather possible values for period until
        possible_values = []
        if data_action == 'view' : # limit possible values via maximum interval steps
            if data_type == 'map' and self.utilise_delta.get() and self.deltaReferenceIsWithinPeriod() :
                maximum_steps = self.maximum_interval_steps + 1
            else :
                maximum_steps = self.maximum_interval_steps
            for steps in range(1, maximum_steps+1) :
                next_step_value = from_value + interval_step*steps
                if next_step_value <= period_ranges['max'] :
                    possible_values.append(next_step_value)
        elif data_action == 'files' : # allow all possible values within range
            steps = 1
            next_step_value = from_value + interval_step
            while next_step_value <= period_ranges['max'] :
                possible_values.append(next_step_value)
                steps += 1
                next_step_value = from_value + interval_step*steps
        #print 'possible_values:', possible_values[:5], '...', possible_values[len(possible_values)-5:], until_value

        # Will a close value be found within the possible values?
        closest_value_present = False
        if possible_values :
            closest_value_present = (until_value >= possible_values[0] and until_value <= possible_values[:].pop())

        if closest_value_present : # Look for the closest value greater than the until value
            #lower_value = from_value
            upper_value = possible_values[0]
            gone_past = False
            for value in possible_values :
##                if until_value >= value :
##                    lower_value = value
##                elif not gone_past :
                if value >= until_value and not gone_past :
                    upper_value = value
                    gone_past = True
##            if abs(lower_value - until_value) < abs(upper_value - until_value) :
##                until_value = lower_value
##            else :
            until_value = upper_value
            self.current_interval_steps = possible_values.index(until_value) + 1
        elif data_type == 'map' and data_action == 'view' and self.current_interval_steps <= self.maximum_interval_steps: # maintain current interval steps if possible
            possible_steps = 1
            for steps in range(1, self.current_interval_steps+1) :
                next_step_value = from_value + interval_step*steps
                if next_step_value <= period_ranges['max'] :
                    until_value = next_step_value
                    possible_steps = steps
            if possible_steps < self.current_interval_steps :
                self.current_interval_steps = possible_steps
        else : # (self.previous_period_changed_via['until'] == 'key') and (until_value < possible_values[0] or until_value > possible_values[:].pop()) :
            if until_value < possible_values[0] :
                until_value = possible_values[0]
                self.current_interval_steps = 1
            elif until_value > possible_values[:].pop() :
                until_value = possible_values[:].pop()
                self.current_interval_steps = len(possible_values)

        # Update Current Interval Steps
        self.updateCurrentIntervalSteps()

        # Convert to BP if required
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # AD
            if until_value < period_ranges_ad['min'] or until_value > period_ranges_ad['max'] or (self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and until_value <= 1950) :
                self.period_postfix_text['until'].set(self.period_postfix_keys[0]) # change to BP
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            #if until_value in possible_values :
            #    possible_values = possible_values[possible_values.index(until_value):]
            #print 'revised:', possible_values
            converted_possible_values = []
            for value in possible_values :
                if value <= 1950 :
                    converted_possible_values.append(-1*value + 1950)
            possible_values = converted_possible_values
            #print 'converted:', possible_values
            until_value = -1*until_value + 1950
            #print 'converted until_value:', until_value

        # Update spinbox list
        self.updatePeriodSpinboxList('until', value=until_value, values=possible_values)

    # Step 4 Method: Update Period Spinbox List
    def updatePeriodSpinboxList(self, context, value=None, values=None) :
        #print 'TODO: updatePeriodSpinboxList', context, self.period_text['from'].get(), self.current_valid_period_value[context]
        if value != None and values != None :
            self.current_period_values[context] = values
            self.period_entry[context].config(values=tuple(map(str, values)))
            self.period_text[context].set(str(value))
        elif context == 'from' :
            current_value = self.current_valid_period_value['from'] # = { 'from' : 1950, 'until' : 1989 }
            interval_step = self.current_valid_interval_step_value
            if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
##                if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                    maximum_from_value = self.period_ranges['BP']['max'] - self.interval_size_range['min']/2 - 1
##                else :
##                    maximum_from_value = self.period_ranges['BP']['max'] - self.interval_size_range['min']/2
                maximum_from_value = self.period_ranges['BP']['max-entry']
#                values = range((self.period_ranges['BP']['max'] - (self.period_ranges['BP']['max'] - current_value) % interval_step), self.period_ranges['BP']['min']-1, -1*interval_step)
                values = range((maximum_from_value - (maximum_from_value - current_value) % interval_step), self.period_ranges['BP']['min']-1, -1*interval_step)
            elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD
##                if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                    maximum_from_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - interval_step - 1
##                else :
                maximum_from_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 + int(not bool(self.interval_size_range['min']%2)) - interval_step
                values = range((self.period_ranges['AD']['min'] + (current_value - self.period_ranges['AD']['min']) % interval_step), maximum_from_value+1, interval_step)
            #print 'max:', maximum_from_value, 'from values:', values
            self.period_entry[context].config(values=tuple(map(str, values)))
            self.period_text[context].set(str(current_value))
            self.current_period_values[context] = values[:]

    # Step 4 Method: Select Period Postfix: the user opens options
    def periodSpinboxArrowPress(self, context) :
        #print 'TODO: periodSpinboxArrowPress', context, self.period_text[context].get(), self.previous_period_text_value[context]
        #print self.period_entry[context]['values']

        # Identify button pressed
        button = self.period_entry[context].identify(self.winfo_pointerx()-self.period_entry[context].winfo_rootx(), self.winfo_pointery()-self.period_entry[context].winfo_rooty())

        # Shift focus if warning pending
        if self.validation_warning_pending :
            self.focus_set()

        # Reset generation
        self.resetGeneration()

        # Resolve postfix key
        if self.period_postfix_text[context].get() == self.period_postfix_keys[0] : # BP
            postfix_key = 'BP'
        elif self.period_postfix_text[context].get() == self.period_postfix_keys[1] : # AD
            postfix_key = 'AD'

        # Move beyond the maximum spinbox value if possible
        if button == 'buttonup' and self.previous_period_text_value[context] == self.period_text[context].get() :
            if self.isNonNegativeInteger(self.period_text[context].get()) :

                # Get current, maximum and incremented period values
##                if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                    maximum_ad_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - 1
##                else :
                maximum_ad_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 + int(not bool(self.interval_size_range['min']%2))
                if context == 'from' :
                    maximum_ad_value = maximum_ad_value - self.current_valid_interval_step_value
                current_ad_value = int(self.period_text[context].get())
                if postfix_key == 'BP' :
                    current_ad_value = 1950 - current_ad_value
                incremented_ad_value = current_ad_value + self.current_valid_interval_step_value

                # Decrease interval step or decrease interval size and update period if possible 
                if context == 'from' and incremented_ad_value > maximum_ad_value :
                    current_interval_step_index = self.current_interval_step_values.index(self.current_valid_interval_step_value)
                    current_interval_size_index = self.current_interval_size_values.index(self.current_valid_interval_size_value)
                    new_interval_step_index = None
                    if current_interval_step_index > 0 :
                        for step_index in range(current_interval_step_index) :
##                            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                                maximum_ad_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - self.current_interval_step_values[step_index] - 1
##                            else :
                            maximum_ad_value = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 + int(not bool(self.interval_size_range['min']%2)) - self.current_interval_step_values[step_index]
                            if (current_ad_value + self.current_interval_step_values[step_index]) <= maximum_ad_value :
                                new_interval_step_index = step_index
                                incremented_ad_value = current_ad_value + self.current_interval_step_values[step_index]
                        if new_interval_step_index != None :
                            self.interval_step_text.set(str(self.current_interval_step_values[new_interval_step_index]))
                    if new_interval_step_index == None and current_interval_size_index > 0 :
                        self.interval_size_text.set(str(self.current_interval_size_values[0]))
                        incremented_ad_value = maximum_ad_value

                # Update period
                if incremented_ad_value <= maximum_ad_value :
                    if postfix_key == 'BP' :
                        if incremented_ad_value <= 1950 : # remain BP
                            self.period_text[context].set(str(incremented_ad_value-1950))
                        elif incremented_ad_value > 1950 : # move into AD
                            self.period_postfix_text[context].set(self.period_postfix_keys[1])
                            self.period_text[context].set(str(incremented_ad_value))
                    elif postfix_key == 'AD' :
                        self.period_text[context].set(str(incremented_ad_value))

                # Update spinbox list
                self.updatePeriodSpinboxList(context)
                
        # Find nearest value (up/down) if not in spinbox value list
        if self.previous_period_changed_via[context] == 'key' :
            last_unforced_value = self.period_text[context].get()
        elif self.previous_period_changed_via[context] == 'forced' :
            last_unforced_value = self.previous_period_text_value[context]
        if self.isNonNegativeInteger(last_unforced_value) :
            if int(last_unforced_value) not in self.current_period_values[context] :
                #print int(last_unforced_value), 'not in', self.current_period_values[context]
                if self.current_period_values[context] :

                    # Deal with lists of AD values
                    if postfix_key == 'BP' : # convert to AD
                        previous_period_ad_value = 1950 - int(last_unforced_value)
                        current_period_ad_values = []
                        for bp_value in self.current_period_values[context] :
                            current_period_ad_values.append(1950 - bp_value)
                    elif postfix_key == 'AD' :
                        previous_period_ad_value = int(last_unforced_value)
                        current_period_ad_values = self.current_period_values[context][:]

                    # Choose the appropriate value from the period value list
                    if previous_period_ad_value < current_period_ad_values[0] :
                        self.period_text[context].set(str(self.current_period_values[context][0]))
                    elif previous_period_ad_value > current_period_ad_values[:].pop() :
                        self.period_text[context].set(str(self.current_period_values[context][:].pop()))
                    else : # find
                        if len(current_period_ad_values) >= 2 :
                            for i in range(len(current_period_ad_values)-1) :
                                if current_period_ad_values[i] < previous_period_ad_value < current_period_ad_values[i+1] :
                                    if button == 'buttonup' :
                                        self.period_text[context].set(str(self.current_period_values[context][i+1]))
                                        #print 'up set to', self.current_period_values[context][i+1]
                                    elif button == 'buttondown' :
                                        self.period_text[context].set(str(self.current_period_values[context][i]))
                                        #print 'down set to', self.current_period_values[context][i]
                        else :
                            self.period_text[context].set(str(self.current_period_values[context][0]))
            elif not self.previous_period_text_value[context] :
                self.period_text[context].set(last_unforced_value)
                self.current_valid_period_value[context] = int(last_unforced_value)
        elif self.period_text[context].get() != '' and self.current_period_values[context] :
            self.period_text[context].set(str(self.current_period_values[context][0]))
            
        self.updateIntervalStep()
        if context == 'from' :
            self.updatePeriodSpinboxList('from')
        self.matchPeriodUntilWithFrom()
        self.matchIntervalSizeWithStep()
        self.updateDeltaReferenceIntervals()

        # Update previous value
        self.previous_period_text_value[context] = self.period_text[context].get()

    # Step 4 Method: Select Period Postfix: the user opens options
    def selectPeriodPostfix(self, context, selected) :
        #print 'TODO: selectPeriodPostfix', context, selected

        # Set period post-fix (required since OptionMenu menu item commands have been overridden)
        self.period_postfix_text[context].set(selected)

        # Reset generation
        self.resetGeneration()

        if context == 'from' :

            # Only allow AD on period until if AD on period from
            if selected == self.period_postfix_keys[0] :
                self.period_postfix_menu['until']['menu'].entryconfigure(0, state=tk.NORMAL)
            elif selected == self.period_postfix_keys[1] :
                self.period_postfix_menu['until']['menu'].entryconfigure(0, state=tk.DISABLED)
            #self.matchPeriodUntilWithFrom()

        # Validate period
        self.validatePeriod(self.period_text[context].get(), 'focusout', context)

    # Step 4 Method: Validate Interval Step
    def validateIntervalStep(self, string_value, reason) :
        #print 'TODO: validateIntervalStep', string_value, reason

        # Anticipate warning/error conditions not satisfied
        warning_pending = False

        # Reset generation
        if reason == 'key' :
            self.resetGeneration()

        # Record previous value
        if reason == 'forced' or reason == 'key' :
            self.previous_interval_step_text_value = self.interval_step_text.get()

        # Conditions for showing the warning/error
        show_warnings_if_any = False
        if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too

            show_warnings_if_any = True

            # Handle case when focus has moved to a (option) menu
            if self.validation_warning_pending :
                self.validation_warning_pending = False
            elif self.force_shift_focus :
                self.force_shift_focus = False
                return True

        # Ensure minimum and maximum step constraints are met
        if self.isNonNegativeInteger(string_value) :
##            if self.deltaWithObservedReferenceDataSelected() :
##                minimum_value = self.delta_reference_observed_data_interval_size
##            else :
##                minimum_value = self.interval_step_range['min']
            minimum_value = self.interval_step_range['min']
            maximum_value = self.calculateCurrentMaximumStepInterval()
            if int(string_value) < minimum_value or int(string_value) > maximum_value :
                warning_pending = True
                if show_warnings_if_any :
                    if int(string_value) < minimum_value :
                        warning = 'The minimum step interval is ' + str(minimum_value) + ' years'
##                        if self.deltaWithObservedReferenceDataSelected() :
##                            warning += ' since delta is relative to the observed data interval'
                    elif maximum_value == self.interval_step_range['max'] :
                        warning = 'The maximum step interval is ' + str(maximum_value) + ' years'
                    else : # calculated value
                        warning = 'The step interval can be no greater than ' + str(maximum_value) + ' years given the current period from setting'
                    self.currently_showing_warning_message = True
                    showwarning('Step interval value out of current range', warning )
                    self.currently_showing_warning_message = False
                    if int(string_value) < minimum_value :
                        self.after_idle(lambda: self.interval_step_text.set(str(minimum_value)))
                    elif int(string_value) > maximum_value :
                        self.after_idle(lambda: self.interval_step_text.set(str(maximum_value)))
                    self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                    self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                    self.after_idle(lambda: self.matchIntervalSizeWithStep())
                    self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                    return True
            elif (reason == 'focusout' or reason == 'forced') : # set current valid value
                self.current_valid_interval_step_value = int(string_value)
                if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too
                    self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                    self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                    self.after_idle(lambda: self.matchIntervalSizeWithStep())
                    self.after_idle(lambda: self.updateDeltaReferenceIntervals())
        elif not string_value :
            if show_warnings_if_any : # replace with last valid value rather than warn
                self.after_idle(lambda: self.interval_step_text.set(str(self.current_valid_interval_step_value)))
        
        if reason == 'key' :
            self.validation_warning_pending = warning_pending
            if string_value :
                # Limit data entry
                return self.isNonNegativeInteger(string_value)
            else :
                return True

        elif reason == 'focusin' :
            if self.force_shift_focus :
                self.focus_set()
                return True
            self.validation_warning_pending = warning_pending
            return True

        else :
            return True

    # Step 4 Method: Calculate Current Maximum Step Interval
    def calculateCurrentMaximumStepInterval(self) :

        # Get from value (as AD)
        from_value = self.current_valid_period_value['from']
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            from_value = 1950 - from_value

        #print 'TODO: calculateCurrentMaximumStepInterval, period from:', from_value

        # Calculate maximum step using from value (assuming at least one step)
##        if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##            maximum_interval_step = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - from_value - 1
##        else :
        maximum_interval_step = self.period_ranges['AD']['max'] - self.interval_size_range['min']/2 - from_value + int(not bool(self.interval_size_range['min']%2))
        if maximum_interval_step < self.interval_step_range['min'] :
            maximum_interval_step = self.interval_step_range['min']
        elif maximum_interval_step > self.interval_step_range['max'] :
            maximum_interval_step = self.interval_step_range['max']

##        # Allow interval step to remain as big as maximum interval size (esp. when no steps)
##        maximum_interval_size = self.calculateCurrentMaximumIntervalSize(consider_interval_step=False)
##        #print ' maximum_interval_size:', maximum_interval_size
##        if maximum_interval_step < maximum_interval_size :
##            maximum_interval_step = maximum_interval_size
##
        #print ' returning', maximum_interval_step
        return maximum_interval_step

    # Step 4 Method: Update Interval Step
    def updateIntervalStep(self) :
        #print 'TODO: updateIntervalStep IN', self.current_valid_interval_step_value
        current_value = self.current_valid_interval_step_value
        maximum_interval = self.calculateCurrentMaximumStepInterval()
        step_values = []
        for value in self.interval_step_values :
            if value < maximum_interval : #and (not self.deltaWithObservedReferenceDataSelected() or value >= self.delta_reference_observed_data_interval_size) :
                step_values.append(value)
        step_values.append(maximum_interval)
        #print ' step_values', step_values, 'current', current_value
        if current_value > maximum_interval :
            current_value = step_values[:].pop()
            self.interval_step_text.set(str(current_value))
            self.current_valid_interval_step_value = current_value
        if step_values != self.current_interval_step_values :
            self.interval_step_entry.config(values=tuple(map(str, step_values)))
            if current_value not in step_values and current_value == self.current_interval_step_values[:].pop() :
                self.interval_step_text.set(str(step_values[:].pop()))
            else :
                self.interval_step_text.set(str(current_value))
            self.current_interval_step_values = step_values

    # Step 4 Method: Interval Step Spinbox Arrow Press
    def intervalStepSpinboxArrowPress(self) :
        #print 'TODO: intervalStepSpinboxArrowPress'
        #print self.interval_step_entry.winfo_children()

        # Identify button pressed
        button = self.interval_step_entry.identify(self.winfo_pointerx()-self.interval_step_entry.winfo_rootx(), self.winfo_pointery()-self.interval_step_entry.winfo_rooty())

        # Shift focus if warning pending
        if self.validation_warning_pending :
            self.focus_set()

        # Reset generation
        self.resetGeneration()

        # Find nearest value (up/down) if not in spinbox value list
        if self.isNonNegativeInteger(self.previous_interval_step_text_value) :
            if int(self.previous_interval_step_text_value) not in self.current_interval_step_values :
                #print int(self.previous_interval_step_text_value), 'not in', self.current_interval_step_values
                if self.current_interval_step_values :
                    if int(self.previous_interval_step_text_value) < self.current_interval_step_values[0] :
                        self.interval_step_text.set(str(self.current_interval_step_values[0]))
                    elif int(self.previous_interval_step_text_value) > self.current_interval_step_values[:].pop() :
                        self.interval_step_text.set(str(self.current_interval_step_values[:].pop()))
                    else : # find
                        if len(self.current_interval_step_values) >= 2 :
                            for i in range(len(self.current_interval_step_values)-1) :
                                if self.current_interval_step_values[i] < int(self.previous_interval_step_text_value) < self.current_interval_step_values[i+1] :
                                    if button == 'buttonup' :
                                        self.interval_step_text.set(str(self.current_interval_step_values[i+1]))
                                        #print 'up set to', self.current_interval_step_values[i+1]
                                    elif button == 'buttondown' :
                                        self.interval_step_text.set(str(self.current_interval_step_values[i]))
                                        #print 'down set to', self.current_interval_step_values[i]
                        else :
                            self.interval_step_text.set(str(self.current_interval_step_values[0]))
        elif self.current_interval_step_values :
            self.interval_step_text.set(str(self.current_interval_step_values[0]))

        self.updateIntervalStep()
        self.updatePeriodSpinboxList('from')
        self.matchPeriodUntilWithFrom()
        self.matchIntervalSizeWithStep()
        self.updateDeltaReferenceIntervals()

    # Step 4 Method: Delta Reference Is Within Period?
    def deltaReferenceIsWithinPeriod(self) :
        delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
        if delta_reference_period_code in ['previous', 'next'] :
            return True
        else :
            delta_reference_year = self.delta_reference_value[delta_reference_period_code]['year']
            delta_reference_postfix = self.delta_reference_value[delta_reference_period_code]['postfix']
            from_year = int(self.period_text['from'].get())
            from_postfix = self.period_postfix_text['from'].get()
            until_year = int(self.period_text['until'].get())
            until_postfix = self.period_postfix_text['until'].get()
            if ((delta_reference_year == from_year and delta_reference_postfix == from_postfix) or
                (delta_reference_year == until_year and delta_reference_postfix == until_postfix)) :
                return True
            else :
                return False

    # Step 4 Method: Update Current Interval Steps
    def updateCurrentIntervalSteps(self) :
        #print 'TODO: updateCurrentIntervalSteps'
        data_type = self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())]
        data_action = self.data_action_keys[self.data_action_selection.index(self.data_action_text.get())]
        if data_type == 'map' and self.utilise_delta.get() :
            if self.deltaReferenceIsWithinPeriod() :
                current_steps = self.current_interval_steps - 1
            else :
                current_steps = self.current_interval_steps
        else :
            current_steps = self.current_interval_steps
        current_display_string = 'Generates ' + str(current_steps + 1) + ' '
        if data_action == 'view' and current_steps == self.maximum_interval_steps :
            current_display_string += '(maximum) '
        if data_type == 'map' :
            if data_action == 'view' :
                current_display_string += 'grid map plot'
            elif data_action == 'files' :
                current_display_string += 'gridded data file'
        elif data_type == 'series' :
            current_display_string += 'time series value'
        if current_steps > 1 :
            current_display_string += 's'

        # Resolve from and until intervals (initially converting to AD values)
        from_value = int(self.period_text['from'].get())
        from_postfix_key = self.period_postfix_text['from'].get()
        until_value = int(self.period_text['until'].get())
        until_postfix_key = self.period_postfix_text['until'].get()
        if from_postfix_key == 'BP' :
            from_value = 1950 - from_value   
        if until_postfix_key == 'BP' :
            until_value = 1950 - until_value
        interval_step = self.current_valid_interval_step_value
        interval_size = self.current_valid_interval_size_value
        if data_type == 'map' and self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
            delta_reference_value = self.delta_reference_value[delta_reference_period_code]['year']
            if self.delta_reference_value[delta_reference_period_code]['postfix'] == 'BP' :
                delta_reference_value = 1950 - delta_reference_value
            if delta_reference_value == from_value : # from second interval
                from_value += interval_step
            elif delta_reference_value == until_value : # until second last interval
                until_value -= interval_step
        from_value_interval = { 'start' : (from_value - interval_size/2), 'end' : (from_value + interval_size/2 - int(not bool(interval_size%2))) }
        if from_postfix_key == 'BP' and from_value_interval['start'] > 1950 :
            from_interval_string = str(from_value_interval['start']) + '-' + str(from_value_interval['end']) + 'AD'
        elif from_postfix_key == 'BP' and from_value_interval['end'] > 1950 :
            from_interval_string = str(1950 - from_value_interval['start']) + 'BP-' + str(from_value_interval['end']) + 'AD'
        elif from_postfix_key == 'BP' :
            from_interval_string = str(1950 - from_value_interval['start']) + '-' + str(1950 - from_value_interval['end']) + 'BP'
        elif from_postfix_key == 'AD' and from_value_interval['end'] < 1 :
            from_interval_string = str(1950 - from_value_interval['start']) + '-' + str(1950 - from_value_interval['end']) + 'BP'
        elif from_postfix_key == 'AD' and from_value_interval['start'] < 1 :
            from_interval_string = str(1950 - from_value_interval['start']) + 'BP-' + str(from_value_interval['end']) + 'AD'
        elif from_postfix_key == 'AD' :
            from_interval_string = str(from_value_interval['start']) + '-' + str(from_value_interval['end']) + 'AD'
        until_value_interval = { 'start' : (until_value - interval_size/2), 'end' : (until_value + interval_size/2 - int(not bool(interval_size%2))) }
        if until_postfix_key == 'BP' and until_value_interval['start'] > 1950 :
            until_interval_string = str(until_value_interval['start']) + '-' + str(until_value_interval['end']) + 'AD'
        elif until_postfix_key == 'BP' and until_value_interval['end'] > 1950 :
            until_interval_string = str(1950 - until_value_interval['start']) + 'BP-' + str(until_value_interval['end']) + 'AD'
        elif until_postfix_key == 'BP' :
            until_interval_string = str(1950 - until_value_interval['start']) + '-' + str(1950 - until_value_interval['end']) + 'BP'
        elif until_postfix_key == 'AD' and until_value_interval['end'] < 1 :
            until_interval_string = str(1950 - until_value_interval['start']) + '-' + str(1950 - until_value_interval['end']) + 'BP'
        elif until_postfix_key == 'AD' and until_value_interval['start'] < 1 :
            until_interval_string = str(1950 - until_value_interval['start']) + 'BP-' + str(until_value_interval['end']) + 'AD'
        elif until_postfix_key == 'AD' :
            until_interval_string = str(until_value_interval['start']) + '-' + str(until_value_interval['end']) + 'AD'
        current_display_string += ' for intervals from ' + from_interval_string + ' until ' + until_interval_string

        self.current_interval_steps_text.set(current_display_string)

    # Step 4 Method: Validate Interval Size
    def validateIntervalSize(self, string_value, reason) :
        #print 'TODO: validateIntervalSize', string_value, reason

        # Anticipate warning/error conditions not satisfied
        warning_pending = False

        # Reset generation
        if reason == 'key' :
            self.resetGeneration()

        # Record previous value
        if reason == 'forced' or reason == 'key' :
            self.previous_interval_size_text_value = self.interval_size_text.get()

        # Conditions for showing the warning/error
        show_warnings_if_any = False
        if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too

            show_warnings_if_any = True

            # Handle case when focus has moved to a (option) menu
            if self.validation_warning_pending :
                self.validation_warning_pending = False
            elif self.force_shift_focus :
                self.force_shift_focus = False
                return True

        # Ensure minimum and maximum step constraints are met
        if self.isNonNegativeInteger(string_value) :
            minimum_value = self.interval_size_range['min']
            maximum_value = self.calculateCurrentMaximumIntervalSize()
            if int(string_value) < minimum_value or int(string_value) > maximum_value :
                warning_pending = True
                if show_warnings_if_any :
                    if int(string_value) < minimum_value :
                        warning = 'The minimum interval size is ' + str(minimum_value) + ' years'
                    elif maximum_value == self.interval_size_range['max'] :
                        warning = 'The maximum interval size is ' + str(maximum_value) + ' years'
##                    elif maximum_value == self.current_valid_interval_step_value :
##                        warning = 'The interval size can not be greater than the interval step: ' + str(maximum_value)
                    else : # restricted via period from
                        warning = 'The interval size can not be greater than ' + str(maximum_value) + ' given the current period'
                    self.currently_showing_warning_message = True
                    showwarning('Interval size out of current range', warning )
                    self.currently_showing_warning_message = False
                    if int(string_value) < minimum_value :
                        self.after_idle(lambda: self.interval_size_text.set(str(minimum_value)))
                        self.after_idle(lambda: self.updateIntervalStep())
                        self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                        self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                    elif int(string_value) > maximum_value :
                        self.after_idle(lambda: self.interval_size_text.set(str(maximum_value)))
                        self.after_idle(lambda: self.updateIntervalStep())
                        self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                        self.after_idle(lambda: self.updateDeltaReferenceIntervals())
                    return True
            elif (reason == 'focusout' or reason == 'forced') : # set current valid value
                self.current_valid_interval_size_value = int(string_value)
                if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too
                    self.after_idle(lambda: self.updateIntervalStep())
                    self.after_idle(lambda: self.updatePeriodSpinboxList('from'))
                    self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                    self.after_idle(lambda: self.updateDeltaReferenceIntervals())
        elif not string_value :
            if show_warnings_if_any : # replace with last valid value rather than warn
                self.after_idle(lambda: self.interval_size_text.set(str(self.current_valid_interval_size_value)))
        
        if reason == 'key' :
            self.validation_warning_pending = warning_pending
            if string_value :
                # Limit data entry
                return self.isNonNegativeInteger(string_value)
            else :
                return True

        elif reason == 'focusin' :
            if self.force_shift_focus :
                self.focus_set()
                return True
            self.validation_warning_pending = warning_pending
            return True

        else :
            return True

    # Step 4 Method: Interval Size Spinbox Arrow Press
    def intervalSizeSpinboxArrowPress(self) :
        #print 'TODO: intervalSizeSpinboxArrowPress'

        # Identify button pressed
        button = self.interval_size_entry.identify(self.winfo_pointerx()-self.interval_size_entry.winfo_rootx(), self.winfo_pointery()-self.interval_size_entry.winfo_rooty())

        # Shift focus if warning pending
        if self.validation_warning_pending :
            self.focus_set()

        # Reset generation
        self.resetGeneration()

        # Find nearest value (up/down) if not in spinbox value list
        if self.isNonNegativeInteger(self.previous_interval_size_text_value) :
            if int(self.previous_interval_size_text_value) not in self.current_interval_size_values :
                #print int(self.previous_interval_size_text_value), 'not in', self.current_interval_size_values
                if self.current_interval_size_values :
                    if int(self.previous_interval_size_text_value) < self.current_interval_size_values[0] :
                        self.interval_size_text.set(str(self.current_interval_size_values[0]))
                    elif int(self.previous_interval_size_text_value) > self.current_interval_size_values[:].pop() :
                        self.interval_size_text.set(str(self.current_interval_size_values[:].pop()))
                    else : # find
                        if len(self.current_interval_size_values) >= 2 :
                            for i in range(len(self.current_interval_size_values)-1) :
                                if self.current_interval_size_values[i] < int(self.previous_interval_size_text_value) < self.current_interval_size_values[i+1] :
                                    if button == 'buttonup' :
                                        self.interval_size_text.set(str(self.current_interval_size_values[i+1]))
                                        #print 'up set to', self.current_interval_size_values[i+1]
                                    elif button == 'buttondown' :
                                        self.interval_size_text.set(str(self.current_interval_size_values[i]))
                                        #print 'down set to', self.current_interval_size_values[i]
                        else :
                            self.interval_size_text.set(str(self.current_interval_size_values[0]))
        elif self.current_interval_size_values :
            self.interval_size_text.set(str(self.current_interval_size_values[0]))

        self.updateIntervalStep()
        self.matchPeriodUntilWithFrom()
        self.updateDeltaReferenceIntervals()

    # Step 4 Method: Calculate Current Maximum Interval Size
    def calculateCurrentMaximumIntervalSize(self) : #, consider_interval_step=True) :
        if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) : # months cross year boundaries
            #maximum_ad_period = self.period_ranges['AD']['max'] - 1
            maximum_bp_period = self.period_ranges['BP']['max'] - 1
        else :
            maximum_bp_period = self.period_ranges['BP']['max']
        maximum_ad_period = self.period_ranges['AD']['max']
        limited_via_period = None
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            limited_via_period = (maximum_bp_period - self.current_valid_period_value['from'])*2 + 1
        elif self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # AD
            limited_via_period = ((maximum_ad_period - self.current_valid_period_value['until']) + 1)*2
        maximum_value = self.interval_size_range['max']
        if limited_via_period != None :
            #print 'interval size limited to:', limited_via_period
            if limited_via_period < self.interval_size_range['min'] :
                maximum_value = self.interval_size_range['min']
            elif limited_via_period > self.interval_size_range['max'] :
                maximum_value = self.interval_size_range['max']
            else :
                maximum_value = limited_via_period
##        if self.current_valid_interval_step_value < maximum_value :
##            return self.current_valid_interval_step_value
##        else :
        return maximum_value

    # Step 4 Method: Match Interval Size With Step
    def matchIntervalSizeWithStep(self) :
        #print 'TODO: matchIntervalSizeWithStep'
        current_value = self.current_valid_interval_size_value
        maximum_value = self.calculateCurrentMaximumIntervalSize() 
        size_values = []
        for value in self.interval_size_values :
            if value < maximum_value :
                size_values.append(value)
        if maximum_value in self.interval_size_values : #or maximum_value == self.current_valid_interval_step_value :
            size_values.append(maximum_value)
        #print 'max:', maximum_value,'size_values:', size_values
        if current_value > maximum_value :
            current_value = size_values[:].pop()
            self.interval_size_text.set(str(current_value))
            self.current_valid_interval_size_value = current_value
        if size_values != self.current_interval_size_values :
            self.interval_size_entry.config(values=tuple(map(str, size_values)))
            self.interval_size_text.set(str(current_value))
            self.current_interval_size_values = size_values

##    # Step 4 Method: Update Interval Size
##    def updateIntervalSize(self) :
##        if self.deltaWithObservedReferenceDataSelected() :
##            self.interval_size_text.set(str(self.delta_reference_observed_data_interval_size))
##            self.interval_size_entry.config(state=tk.DISABLED)
##        else :
##            self.interval_size_entry.config(state=tk.NORMAL)
            
    ## Step 5: Delta Methods ##############################################################################################################################################

    # Step 5 Method: Delta Selection: the user selects/deselects delta
    def deltaSelection(self) :
        
        # Place focus on checkbox
        self.delta_checkbox.focus_set()

        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.utilise_delta.set(int(not bool(self.utilise_delta.get())))
            self.validation_warning_pending = False
            return True

        # Enable/disable reference interval selection
        if self.utilise_delta.get() :
            self.delta_reference_interval_menu.config(state=tk.NORMAL)
            self.utilise_bias_correction.set(0)
            self.bias_correction_checkbox.configure(state=tk.DISABLED)
            self.bias_correction_label.configure(state=tk.DISABLED)
        else :
            self.delta_reference_interval_menu.config(state=tk.DISABLED)
            self.selectDeltaReferenceInterval(self.delta_reference_period_codes[0])
            self.utilise_bias_correction.set(int(self.enabled_bias_correction_set))
            self.bias_correction_checkbox.configure(state=tk.NORMAL)
            self.bias_correction_label.configure(state=tk.NORMAL)

        # Include delta as percent?
        self.deltaAsPercentInclusion()

        # Match period until with from
        self.matchPeriodUntilWithFrom()

    # Step 5 Method: Delta as percent Selection: the user selects/deselects delta as percent
    def deltaAsPercentSelection(self) :
        
        # Place focus on checkbox
        self.delta_as_percent_checkbox.focus_set()

        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.delta_as_percent.set(int(not bool(self.delta_as_percent.get())))
            self.validation_warning_pending = False
            return True

    # Step 5 Method: Delta as percent inclusion: determines if delta as percent option should be visible
    def deltaAsPercentInclusion(self) :
        
        # Resolve selected parameter/group codes
        parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

        # Include?
        if self.utilise_delta.get() and parameter_code in self.delta_as_percent_parameters[parameter_group_code] :
            self.delta_as_percent_checkbox.grid()
            self.delta_as_percent.set(int(self.delta_as_percent_parameters_defaults[parameter_group_code][parameter_code]))
        else :
            self.delta_as_percent_checkbox.grid_remove()
            self.delta_as_percent.set(int(False))

    # Step 5 Method: Select Delta Reference Interval
    def selectDeltaReferenceInterval(self, code) :
        self.delta_reference_interval_text.set(self.delta_reference_interval_selection[self.delta_reference_period_codes.index(code)]) # needed as OptionMenu menu item commands have been overridden

        # Reset generation
        self.resetGeneration()

        # Show/hide user-defined reference
        if code == 'user-defined' :
            self.delta_user_defined_reference_frame.grid()
        else :
            self.delta_user_defined_reference_frame.grid_remove()

        # Match period until with from
        self.matchPeriodUntilWithFrom()

    # Step 5 Method: Update Delta Reference Intervals
    def updateDeltaReferenceIntervals(self) :
        #print 'TODO: updateDeltaReferenceIntervals'

        # Current selection code
        current_selection_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]

        # Resolve postfix keys
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            from_postfix_key = 'BP'
        elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] : # AD (=> until also AD)
            from_postfix_key = 'AD'
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP (=> from also BP)
            until_postfix_key = 'BP'
        elif self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # AD
            until_postfix_key = 'AD'

        # Get period and interval values and convert to AD
        from_value = int(self.period_text['from'].get())
        if from_postfix_key == 'BP' :
            from_value = 1950 - from_value
        until_value = int(self.period_text['until'].get())
        if until_postfix_key == 'BP' :
            until_value = 1950 - until_value
        interval_step = self.current_valid_interval_step_value
        interval_size = self.current_valid_interval_size_value

        # Resolve delta reference previous interval
        previous_value = from_value # - interval_step
        #previous_value_interval = { 'from' : (previous_value - interval_size/2), 'until' : (previous_value + interval_size/2 - int(not bool(interval_size%2))) }
        if previous_value < 1 :
            from_postfix_key = 'BP'
        if from_postfix_key == 'BP' :
            previous_value = 1950 - previous_value
            #previous_value_interval = { 'from' : (1950 - previous_value_interval['from']), 'until' : (1950 - previous_value_interval['until']) }
        self.delta_reference_value['previous']['year'] = previous_value
        self.delta_reference_value['previous']['postfix'] = from_postfix_key
        #self.delta_reference_interval_post_text['previous'] = str(previous_value_interval['from']) + '-' + str(previous_value_interval['until']) +  from_postfix_key
        self.delta_reference_interval_pre_text['previous'] = str(previous_value) + ' ' + from_postfix_key
        previous_entry = self.delta_reference_interval_pre_text['previous'] + self.delta_reference_interval_post_text['previous']
        self.delta_reference_interval_selection[self.delta_reference_period_codes.index('previous')] = previous_entry
        self.delta_reference_interval_menu['menu'].entryconfigure(self.delta_reference_period_codes.index('previous'), label=previous_entry)

        # Resolve delta reference next interval
        next_value = until_value # + interval_step
        #next_value_interval = { 'from' : (next_value - interval_size/2), 'until' : (next_value + interval_size/2 - int(not bool(interval_size%2))) }
        #if next_value_interval['until'] > 1950 :
        #    until_postfix_key = 'AD'
        if until_postfix_key == 'BP' :
            next_value = 1950 - next_value
            #next_value_interval = { 'from' : (1950 - next_value_interval['from']), 'until' : (1950 - next_value_interval['until']) }
        self.delta_reference_value['next']['year'] = next_value
        self.delta_reference_value['next']['postfix'] = until_postfix_key
        #self.delta_reference_interval_post_text['next'] = str(next_value_interval['from']) + '-' + str(next_value_interval['until']) +  until_postfix_key
        self.delta_reference_interval_pre_text['next'] = str(next_value) + ' ' + until_postfix_key
        next_entry = self.delta_reference_interval_pre_text['next'] + self.delta_reference_interval_post_text['next']
        self.delta_reference_interval_selection[self.delta_reference_period_codes.index('next')] = next_entry
        self.delta_reference_interval_menu['menu'].entryconfigure(self.delta_reference_period_codes.index('next'), label=next_entry)

        # Resolve delta reference present-day interval
        present_day_value = self.period_ranges['AD']['max'] - interval_size/2 + int(not bool(interval_size%2))
        self.delta_reference_value['present-day'] = { 'year' : present_day_value, 'postfix' : 'AD' }
        self.delta_reference_interval_pre_text['present-day'] = str(present_day_value) + ' AD'
        present_day_entry = self.delta_reference_interval_pre_text['present-day'] + self.delta_reference_interval_post_text['present-day']
        self.delta_reference_interval_selection[self.delta_reference_period_codes.index('present-day')] = present_day_entry
        self.delta_reference_interval_menu['menu'].entryconfigure(self.delta_reference_period_codes.index('present-day'), label=present_day_entry)
        
        # Resolve delta reference oldest-record interval
        # oldest_record_value = self.period_ranges['BP']['max'] - interval_size/2
        oldest_record_value = self.period_ranges['BP']['max-entry']
        self.delta_reference_value['oldest-record'] = { 'year' : oldest_record_value, 'postfix' : 'BP' }
        self.delta_reference_interval_pre_text['oldest-record'] = str(oldest_record_value) + ' BP'
        oldest_record_entry = self.delta_reference_interval_pre_text['oldest-record'] + self.delta_reference_interval_post_text['oldest-record']
        self.delta_reference_interval_selection[self.delta_reference_period_codes.index('oldest-record')] = oldest_record_entry
        self.delta_reference_interval_menu['menu'].entryconfigure(self.delta_reference_period_codes.index('oldest-record'), label=oldest_record_entry)

        # Set reference interval
        self.delta_reference_interval_text.set(self.delta_reference_interval_selection[self.delta_reference_period_codes.index(current_selection_code)])

        # Resolve user-defined value
        if current_selection_code == 'user-defined' :
            # Update user-defined value and spinbox via validation
            self.validateDeltaUserDefinedReference(self.delta_user_defined_reference_text['year'].get(), 'update')
        else : # Set to one step before the period from unless out of range
            user_defined_value = from_value - interval_step
            user_defined_postfix_key = from_postfix_key
            if user_defined_value < self.period_ranges['AD']['min'] :
                user_defined_postfix_key = 'BP'
            if user_defined_postfix_key == 'BP' :
                user_defined_value = 1950 - user_defined_value
##                if user_defined_value > self.period_ranges['BP']['max-entry'] :
##                    user_defined_value = self.period_ranges['BP']['max-entry']
            self.delta_reference_value['user-defined']['year'] = next_value
            self.delta_reference_value['user-defined']['postfix'] = until_postfix_key
            self.delta_user_defined_reference_text['year'].set(str(user_defined_value))
            self.delta_user_defined_reference_text['postfix'].set(user_defined_postfix_key)
            self.validateDeltaUserDefinedReference(str(user_defined_value), 'update')

    # Step 5 Method: Validate Delta User-Defined Reference
    def validateDeltaUserDefinedReference(self, string_value, reason) :
        #print 'TODO: validateDeltaUserDefinedReference', string_value, reason

        # Anticipate warning/error conditions not satisfied
        warning_pending = False

        # Reset generation
        if reason == 'key' :
            self.resetGeneration()

        # Record previous value
        if reason == 'forced' or reason == 'key' :
            self.previous_delta_user_defined_reference_text_value = self.delta_user_defined_reference_text['year'].get()
            self.previous_delta_user_defined_reference_changed_via = reason

        # Conditions for showing the warning/error
        show_warnings_if_any = False
        if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too

            show_warnings_if_any = True

            # Handle case when focus has moved to a (option) menu
            if self.validation_warning_pending :
                self.validation_warning_pending = False
            elif self.force_shift_focus :
                self.force_shift_focus = False
                return True

        # Resolve postfix key
        if self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[0] : # BP
            postfix_key = 'BP'
        elif self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[1] : # AD
            postfix_key = 'AD'

        # Ensure minimum and maximum period constraints are met
        if self.isNonNegativeInteger(string_value) :
            minimum_value = self.period_ranges[postfix_key]['min']
            if postfix_key == 'BP' :
##                if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                    maximum_value = self.period_ranges[postfix_key]['max'] - self.current_valid_interval_size_value/2 - 1
##                else :
##                    maximum_value = self.period_ranges[postfix_key]['max'] - self.current_valid_interval_size_value/2
                maximum_value = self.period_ranges['BP']['max-entry']
            else : # AD
                maximum_value = self.period_ranges[postfix_key]['max'] - self.current_valid_interval_size_value/2 + int(not bool(self.current_valid_interval_size_value%2))
            if int(string_value) < minimum_value or int(string_value) > maximum_value :
                warning_pending = 'delta-user-defined-reference'
                if show_warnings_if_any :
                    self.currently_showing_warning_message = True
                    if postfix_key == 'BP' :
                        warning = 'User-defined reference year must be between ' + str(maximum_value) + ' BP and ' + str(minimum_value) + ' BP'
                    elif postfix_key == 'AD' :
                        warning = 'User-defined reference year must be between ' + str(minimum_value) + ' AD and ' + str(maximum_value) + ' AD'
                    showwarning('User-defined reference year out of range', warning)
                    self.currently_showing_warning_message = False
                    if int(string_value) < minimum_value :
                        self.after_idle(lambda: self.delta_user_defined_reference_text['year'].set(str(minimum_value)))
                        self.after_idle(lambda: self.updateDeltaUserDefinedReferenceSpinboxList())
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                    elif int(string_value) > maximum_value :
                        self.after_idle(lambda: self.delta_user_defined_reference_text['year'].set(str(maximum_value)))
                        self.after_idle(lambda: self.updateDeltaUserDefinedReferenceSpinboxList())
                        self.after_idle(lambda: self.matchPeriodUntilWithFrom())
                    return True
                if reason == 'update' :
                    if int(string_value) < minimum_value :
                        self.after_idle(lambda: self.delta_user_defined_reference_text['year'].set(str(minimum_value)))
                        self.delta_reference_value['user-defined']['year'] = minimum_value
                    elif int(string_value) > maximum_value :
                        self.after_idle(lambda: self.delta_user_defined_reference_text['year'].set(str(maximum_value)))
                        self.delta_reference_value['user-defined']['year'] = maximum_value
            elif (reason == 'focusout' or reason == 'forced') : # set current valid value
                self.delta_reference_value['user-defined']['year'] = int(string_value)
                self.current_valid_delta_user_defined_reference_value = int(string_value)
        elif not string_value :
            if show_warnings_if_any : # replace with last valid value rather than warn
                self.after_idle(lambda: self.delta_user_defined_reference_text['year'].set(str(self.current_valid_delta_user_defined_reference_value)))

        if reason == 'focusout' and self.focus_get() and not self.currently_showing_warning_message : # warning messages remove focus too
            self.after_idle(lambda: self.updateDeltaUserDefinedReferenceSpinboxList())
            self.after_idle(lambda: self.matchPeriodUntilWithFrom())
        elif reason == 'update' :
            self.after_idle(lambda: self.updateDeltaUserDefinedReferenceSpinboxList())
            self.after_idle(lambda: self.matchPeriodUntilWithFrom())

        if reason == 'key' :
            self.validation_warning_pending = warning_pending
            if string_value :
                # Limit data entry
                return self.isNonNegativeInteger(string_value)
            else :
                return True

        elif reason == 'focusin' :
            if self.force_shift_focus :
                self.focus_set()
                return True
            self.validation_warning_pending = warning_pending
            return True

        else :
            return True

    # Step 5 Method: Update Delta User-Defined Reference Spinbox List
    def updateDeltaUserDefinedReferenceSpinboxList(self) :
        #print 'TODO: updateDeltaUserDefinedReferenceSpinboxList'
        current_value = self.current_valid_delta_user_defined_reference_value
        interval_step = self.current_valid_interval_step_value
        if self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[0] : # BP
##            if len(self.selected_time_unit_month_indices) < 12 and self.selected_time_unit_month_indices.count(0) and self.selected_time_unit_month_indices.count(11) :
##                maximum_value = self.period_ranges['BP']['max'] - self.current_valid_interval_size_value/2 - 1
##            else :
##                maximum_value = self.period_ranges['BP']['max'] - self.current_valid_interval_size_value/2
            maximum_value = self.period_ranges['BP']['max-entry']
            values = range((maximum_value - (maximum_value - current_value) % interval_step), self.period_ranges['BP']['min']-1, -1*interval_step)
        elif self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[1] : # AD
            maximum_value = self.period_ranges['AD']['max'] - self.current_valid_interval_size_value/2 + int(not bool(self.current_valid_interval_size_value%2))
            values = range((self.period_ranges['AD']['min'] + (current_value - self.period_ranges['AD']['min']) % interval_step), maximum_value+1, interval_step)
        #print 'max:', maximum_from_value, 'from values:', values
        self.delta_user_defined_reference_entry.config(values=tuple(map(str, values)))
        self.delta_user_defined_reference_text['year'].set(str(current_value))
        self.current_delta_user_defined_reference_values = values[:]
        #print values[:5], '...', values[(len(values)-5):]

    # Step 5 Method: Delta User-Defined Reference Spinbox Arrow Press
    def deltaUserDefinedReferenceSpinboxArrowPress(self) :
        #print 'TODO: deltaUserDefinedReferenceSpinboxArrowPress'

        # Identify button pressed
        button = self.delta_user_defined_reference_entry.identify(self.winfo_pointerx()-self.delta_user_defined_reference_entry.winfo_rootx(), self.winfo_pointery()-self.delta_user_defined_reference_entry.winfo_rooty())

        # Shift focus if warning pending
        if self.validation_warning_pending :
            self.focus_set()

        # Reset generation
        self.resetGeneration()

        # Resolve postfix key
        if self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[0] : # BP
            postfix_key = 'BP'
        elif self.delta_user_defined_reference_text['postfix'].get() == self.period_postfix_keys[1] : # AD
            postfix_key = 'AD'

        # Move beyond the maximum spinbox value if possible
        if button == 'buttonup' and self.previous_delta_user_defined_reference_text_value == self.delta_user_defined_reference_text['year'].get() :
            if self.isNonNegativeInteger(self.delta_user_defined_reference_text['year'].get()) :

                # Get current, maximum and incremented period values
                maximum_ad_value = self.period_ranges['AD']['max'] - self.current_valid_interval_size_value/2 + int(not bool(self.interval_size_range['min']%2))
                current_ad_value = int(self.delta_user_defined_reference_text['year'].get())
                if postfix_key == 'BP' :
                    current_ad_value = 1950 - current_ad_value
                incremented_ad_value = current_ad_value + self.current_valid_interval_step_value

                # Update period
                if incremented_ad_value <= maximum_ad_value :
                    if postfix_key == 'BP' :
                        if incremented_ad_value <= 1950 : # remain BP
                            self.delta_user_defined_reference_text['year'].set(str(incremented_ad_value-1950))
                        elif incremented_ad_value > 1950 : # move into AD
                            self.delta_user_defined_reference_text['postfix'].set(self.period_postfix_keys[1])
                            self.delta_user_defined_reference_text['year'].set(str(incremented_ad_value))
                    elif postfix_key == 'AD' :
                        self.delta_user_defined_reference_text['year'].set(str(incremented_ad_value))

        # Find nearest value (up/down) if not in spinbox value list
        if self.previous_delta_user_defined_reference_changed_via == 'key' :
            last_unforced_value = self.delta_user_defined_reference_text['year'].get()
        elif self.previous_delta_user_defined_reference_changed_via == 'forced' :
            last_unforced_value = self.previous_delta_user_defined_reference_text_value
        if self.isNonNegativeInteger(last_unforced_value) :
            if int(last_unforced_value) not in self.current_delta_user_defined_reference_values :
                #print int(last_unforced_value), 'not in', self.current_delta_user_defined_reference_values
                if self.current_delta_user_defined_reference_values :

                    # Deal with lists of AD values
                    if postfix_key == 'BP' : # convert to AD
                        previous_period_ad_value = 1950 - int(last_unforced_value)
                        current_period_ad_values = []
                        for bp_value in self.current_delta_user_defined_reference_values :
                            current_period_ad_values.append(1950 - bp_value)
                    elif postfix_key == 'AD' :
                        previous_period_ad_value = int(last_unforced_value)
                        current_period_ad_values = self.current_delta_user_defined_reference_values[:]

                    # Choose the appropriate value from the period value list
                    if previous_period_ad_value < current_period_ad_values[0] :
                        self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[0]))
                    elif previous_period_ad_value > current_period_ad_values[:].pop() :
                        self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[:].pop()))
                    else : # find
                        if len(current_period_ad_values) >= 2 :
                            for i in range(len(current_period_ad_values)-1) :
                                if current_period_ad_values[i] < previous_period_ad_value < current_period_ad_values[i+1] :
                                    if button == 'buttonup' :
                                        self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[i+1]))
                                        #print 'up set to', self.current_period_values[context][i+1]
                                    elif button == 'buttondown' :
                                        self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[i]))
                                        #print 'down set to', self.current_period_values[context][i]
                        else :
                            self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[0]))
            elif not self.previous_delta_user_defined_reference_text_value :
                self.delta_user_defined_reference_text['year'].set(last_unforced_value)
                self.delta_reference_value['user-defined']['year'] = int(last_unforced_value)
                self.current_valid_delta_user_defined_reference_value = int(last_unforced_value)
        elif not self.delta_user_defined_reference_text['year'].get() and self.current_delta_user_defined_reference_values :
            self.delta_user_defined_reference_text['year'].set(str(self.current_delta_user_defined_reference_values[0]))

        self.updateDeltaUserDefinedReferenceSpinboxList()

        # Match period until with from
        self.matchPeriodUntilWithFrom()

    # Step 5 Method: Select Delta User-Defined Reference Postfix
    def selectDeltaUserDefinedReferencePostfix(self, selected) :
        #print 'TODO: selectDeltaUserDefinedReferencePostfix', selected

        # Set post-fix (required since OptionMenu menu item commands have been overridden)
        self.delta_user_defined_reference_text['postfix'].set(selected)
        self.delta_reference_value['user-defined']['postfix'] = selected

        # Reset generation
        self.resetGeneration()

        # Validate year
        self.validateDeltaUserDefinedReference(self.delta_user_defined_reference_text['year'].get(), 'focusout')

        # Match period until with from
        self.matchPeriodUntilWithFrom()

    ## Step 6: Bias Correction Methods ##############################################################################################################################################

    # Step 6 Method: Bias Correction Selection: the user selects/deselects Bias Correction
    def biasCorrectionSelection(self) :
        
        # Place focus on checkbox
        self.bias_correction_checkbox.focus_set()

        # Reset generation
        self.resetGeneration()

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.utilise_bias_correction.set(int(not bool(self.utilise_bias_correction.get())))
            self.validation_warning_pending = False
            return True

        # Maintain selection when enabled
        self.enabled_bias_correction_set = bool(self.utilise_bias_correction.get())

    ## Step 7: Generation Methods ##############################################################################################################################################

    # Step 7 Method: View Plot
    def viewPlot(self) :
        #print 'TODO: viewPlot'

        # Place focus on view button
        self.view_button.focus_set()

        # Check that the details are complete
        if self.detailsIncomplete() :
            return True

        # Remove edit colours window
        if hasattr(self, 'edit_map_options_window') :
            self.after_idle(lambda: self.edit_map_options_window.destroy())

        # Generate grids or series?
        generate_grids = (self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())] == 'map')

        # Disable view button, add generation status bar, and change label text
        self.view_button.configure(state=tk.DISABLED)
        self.update_idletasks()
        self.generation_status_bar['value'] = 0
        self.generation_status_bar['maximum'] = (self.current_interval_steps + 1) * self.current_valid_interval_size_value * len(self.selected_time_unit_month_indices)
        if generate_grids :
            if self.use_contoured_grid_maps :
                self.generation_status_bar['maximum'] += 2 * (self.current_interval_steps + 1) * self.generation_status_times['view']['contours']
            self.generation_status_bar['maximum'] += (self.current_interval_steps + int(not self.utilise_delta.get())) * self.generation_status_times['view']['map']
            if self.region_is_time_dependent[self.current_region] :
                self.generation_status_bar['maximum'] += (self.current_interval_steps + int(not self.utilise_delta.get())) * self.generation_status_times['view']['time-dependent']
##            self.generation_status_bar['maximum'] += (self.current_interval_steps + int(not self.utilise_delta.get())) * self.generation_status_times['view']['masks']
        else :
            self.generation_status_bar['maximum'] += self.generation_status_times['view']['series'] * (1 + int(self.time_unit_is_all_months)*11)
        self.generation_status_bar.grid()
        self.update_idletasks()
        self.view_label_text.set('')
        self.update_idletasks()
        self.view_label_text.set(self.generation_status_options['view']['data'])
        self.update_idletasks()
            
        # Resolve selected parameter/group codes
        parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

        # Is the parameter data gridded?
        parameter_data_is_gridded = self.data_file_helper.parameterDataIsGridded(parameter_group_code, parameter_code)

        # Get period and interval values and convert to AD if required
        period_ad_from = int(self.period_text['from'].get())
        period_ad_until = int(self.period_text['until'].get())
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            period_ad_from = 1950 - period_ad_from
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            period_ad_until = 1950 - period_ad_until

        # Get delta reference data when required
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
            delta_ref_period_ad = self.delta_reference_value[delta_reference_period_code]['year']
            if self.delta_reference_value[delta_reference_period_code]['postfix'] == self.period_postfix_keys[0] : # BP
                delta_ref_period_ad = 1950 - delta_ref_period_ad
            if generate_grids :
                if delta_reference_period_code is 'previous' or delta_ref_period_ad == period_ad_from :
                    period_ad_from += self.current_valid_interval_step_value
                elif delta_reference_period_code is 'next' or delta_ref_period_ad == period_ad_until :
                    period_ad_until -= self.current_valid_interval_step_value
        else :
            delta_ref_period_ad = None

        # Change label text
        self.update_idletasks()
        self.view_label_text.set('')
        self.update_idletasks()
        self.view_label_text.set(self.generation_status_options['view']['plot'])
        self.update_idletasks()

        # Gather parameter data from the climate data files
        data_extraction_ok = False
        try :
            parameter_data = self.data_file_helper.generateParameterData(parameter_group_code=parameter_group_code,
                                                                         parameter_code=parameter_code,
                                                                         period_ad_from=period_ad_from,
                                                                         period_ad_until=period_ad_until,
                                                                         delta_ref_period_ad=delta_ref_period_ad,
                                                                         delta_as_percent=bool(self.delta_as_percent.get()),
                                                                         interval_step=self.current_valid_interval_step_value,
                                                                         interval_size=self.current_valid_interval_size_value,
                                                                         month_indices=self.selected_time_unit_month_indices,
                                                                         region_mask=self.region_mask,
                                                                         generate_grids=generate_grids,
                                                                         all_months=self.time_unit_is_all_months,
                                                                         correct_bias=self.utilise_bias_correction.get())
            data_extraction_ok = True
        except Exception, e :
            showerror('Data extraction error', str(e))
            print >> sys.stderr, 'Data extraction error:', e

        if data_extraction_ok :

            # Plot data
            if generate_grids :
                region_masks = []
                global_masks = []
                contoured_region_masks = []
                contoured_parameter_data = []
                for i, interval_from in enumerate(range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value)) :
                    if self.region_is_time_dependent[self.current_region] :
                        region_masks.append(self.region_mask[self.data_file_helper.nearestTimeDependentRegionMaskYear(1950 - interval_from)])
                    else :
                        region_masks.append(self.region_mask)
                    if self.region_bounding_box[self.current_region]['centre'] == 180 or self.userDefinedGridMaskRequiresShift() :
                        region_masks[i] = self.shiftGridMask180Degrees(region_masks[i])
                    global_masks.append(np.ones_like(region_masks[i]))
                    if self.use_contoured_grid_maps :
                        contoured_region_masks.append(self.transformGridMaskForContours(region_masks[i]))
                        self.generation_status_bar['value'] += self.generation_status_times['view']['contours']
                        self.update_idletasks()
                if self.region_bounding_box[self.current_region]['centre'] == 180 or self.userDefinedGridMaskRequiresShift() :
                    parameter_data = self.shiftDataGrids180Degrees(parameter_data)
                if self.use_contoured_grid_maps :
                    contoured_parameter_data = self.transformDataGridsForContours(parameter_data)
                self.grid_plot_parameter_data = parameter_data
                self.grid_plot_contoured_parameter_data = contoured_parameter_data
                self.grid_plot_region_masks = region_masks
                self.grid_plot_contoured_region_masks = contoured_region_masks
                self.grid_plot_statistics = { 'region' : self.data_file_helper.calculateGridRegionStatistics(self.grid_plot_parameter_data, self.grid_plot_region_masks),
                                              'global' : self.data_file_helper.calculateGridRegionStatistics(self.grid_plot_parameter_data, global_masks),
                                              'years_ad' : range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value) }
                if self.use_contoured_grid_maps :
                    self.viewGridPlots(contoured_parameter_data, contoured_region_masks)
                else :
                    self.viewGridPlots(parameter_data, region_masks)
            else : # series plot
                self.series_plot_parameter_data = parameter_data
                self.viewSeriesPlot(parameter_data)

            # Update the current tool generation log entry
            self.updateToolGenerationLogEntry(statistics_generated=(parameter_data_is_gridded and not generate_grids))

        # Remove generation status bar, reinstate label text and re-enable button
        self.update_idletasks()
        self.generation_status_bar.grid_remove() # only when exception
        self.update_idletasks()
        self.view_label_text.set('')
        self.update_idletasks()
        self.view_label_text.set(self.generation_options['view'][self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())]])
        self.view_button.configure(state=tk.NORMAL)

    # Step 7 Method: Details Incomplete
    def detailsIncomplete(self) :

        # Exit if validation warning is pending
        if self.validation_warning_pending :
            self.validation_warning_pending = False
            return True

        # Ensure periods already match with interval
        current_period_until = self.period_text['until'].get()
        self.updateIntervalStep()
        self.matchPeriodUntilWithFrom()
        self.updateDeltaReferenceIntervals()
        if self.period_text['until'].get() != current_period_until : # it didn't match
            return True

        # Ensure user-defined time unit is complete when used
        if self.time_unit_text.get() == 'User-defined' :
            if not self.selected_time_unit_month_indices :
                self.setUserDefinedTimeUnit()
                return True

        # Ensure user-defined region is defined when selected
        if self.current_region == 'user-defined' :
            if not self.region_mask.any() :
                self.viewEditRegion(button_pressed=False)
                return True

        # Automatically bring option for setting climate data location if it does not exist already
        if not self.data_file_helper.climateDataIsPresent() :
            self.configureClimateDataLocation()
            return True

        # Details complete
        return False

    # Step 7 Method: Shift Grid Mask 180 Degrees
    def shiftGridMask180Degrees(self, grid_mask) :
        return self.shiftDataGrids180Degrees([grid_mask])[0]

    # Step 7 Method: Shift Data Grids 180 Degrees
    def shiftDataGrids180Degrees(self, data_grids) :
        shifted_data_grids = []
        for i, data_grid in enumerate(data_grids) :
            rows = data_grid.shape[0]
            cols = data_grid.shape[1]
            shifted_data_grid = np.zeros((rows, cols))
            shifted_data_grid[:,0:(cols/2)] = data_grid[:,(cols/2):cols]
            shifted_data_grid[:,(cols/2):cols] = data_grid[:,0:(cols/2)]
            shifted_data_grids.append(shifted_data_grid)
        return shifted_data_grids

    # Step 7 Method: User-defined Grid Mask Requires Shift?
    def userDefinedGridMaskRequiresShift(self) :
        if self.current_region == 'user-defined' :
            longitudes_present = (self.region_mask.sum(0) > 0.)*1
            if longitudes_present.any() and (longitudes_present[:2].sum() != 0 or longitudes_present[-2:].sum() != 0) :
                cols = longitudes_present.shape[0]
                shifted_longitudes_present = np.empty(144, dtype=int)
                shifted_longitudes_present[0:(cols/2)] = longitudes_present[(cols/2):cols]
                shifted_longitudes_present[(cols/2):cols] = longitudes_present[0:(cols/2)]
                if ( shifted_longitudes_present[:2].sum() == 0 and shifted_longitudes_present[-2:].sum() == 0 and
                     shifted_longitudes_present.nonzero()[0].shape[0] == shifted_longitudes_present[shifted_longitudes_present.nonzero()].sum() ) :
                    return True
        return False

    # Step 7 Method: Transform Grid Mask For Contours
    def transformGridMaskForContours(self, grid_mask) :
        rows = grid_mask.shape[0]
        cols = grid_mask.shape[1]
        contour_grid_mask = np.zeros((rows+1,cols+1))
        contour_grid_mask[0,:] = grid_mask[0,:].any()
        contour_grid_mask[rows,:] = grid_mask[(rows-1),:].any()
        for r in np.arange(1, rows) :
            for c in np.arange(1, cols) :
                contour_grid_mask[r,c] = grid_mask[r-1:r+1,c-1:c+1].any()
        for r in np.arange(1, rows) :
            contour_grid_mask[r,0] = np.append(grid_mask[r-1:r+1,0], grid_mask[r-1:r+1,(cols-1)]).any()
            contour_grid_mask[r,cols] = contour_grid_mask[r,0]
        return contour_grid_mask

    # Step 7 Method: Transform Data Grids For Contours
    def transformDataGridsForContours(self, data_grids) :
        contour_data_grids = []
        for i, data_grid in enumerate(data_grids) :
            rows = data_grid.shape[0]
            cols = data_grid.shape[1]
            contour_data_grid = np.zeros((rows+1,cols+1))
            contour_data_grid[0,:] = data_grid[0,:].mean()
            contour_data_grid[rows,:] = data_grid[(rows-1),:].mean()
            for r in np.arange(1, rows) :
                for c in np.arange(1, cols) :
                    contour_data_grid[r,c] = data_grid[r-1:r+1,c-1:c+1].mean()
            for r in np.arange(1, rows) :
                contour_data_grid[r,0] = np.append(data_grid[r-1:r+1,0], data_grid[r-1:r+1,(cols-1)]).mean()
                contour_data_grid[r,cols] = contour_data_grid[r,0]
            contour_data_grids.append(contour_data_grid)
            self.generation_status_bar['value'] += self.generation_status_times['view']['contours']
            self.update_idletasks()
        return contour_data_grids

    # Step 7 Method: Open Generation Status Window
    def openGenerationStatusWindow(self) :
        
        self.focus_set()
        
        # Create or update status window
        if hasattr(self, 'generation_status_window') :
            if self.generation_status_window.children :
                self.generation_status_window.focus_set()
            else :
                self.generation_status_window.destroy()
                self.createGenerationStatusWindow()
        else :
            self.createGenerationStatusWindow()        
 
    # Step 7 Method: Create Generation Status Window
    def createGenerationStatusWindow(self) :

        # Create the generation status window
        self.generation_status_window = tk.Toplevel(self)
        self.generation_status_window.title('Generation Status')
        self.generation_status_window.transient(self)
        self.generation_status_window.focus_set()

        # Status text
        self.data_file_helper.setGenerationStatus('Generating data for interval:')        
        self.generation_status_text = tk.StringVar(value=self.data_file_helper.getGenerationStatus())
        tk.Label(self.generation_status_window, textvariable=self.generation_status_text, padx=0).grid(row=0, column=0, sticky=tk.NW+tk.SW, padx=0, pady=0)

    # Step 7 Method: View Grid Plots (Window only)
    def viewGridPlots(self, parameter_data, region_masks) :
        #print 'TODO: viewGridPlots'

        # Remove existing climate data window
        if hasattr(self, 'view_climate_data_window') :
            self.view_climate_data_window.destroy()

        # Create the view plot window
        self.view_climate_data_window = tk.Toplevel(self)
        self.view_climate_data_window.title('View Map Grid Plots')
        self.view_climate_data_window.transient(self)
        self.view_climate_data_window.focus_set()
        self.current_view_climate_data_window_type = 'map'

        # Create grid plot contents
        self.ignore_grid_plot_config_events = 0
        self.createGridPlots(parameter_data, region_masks)

        # Bind window to resize/configure events
        self.view_climate_data_window.bind('<Configure>', self.__configureViewGridPlotWindow)

    # Step 7 Method: Configure View Grid Plot Window (Event)
    def __configureViewGridPlotWindow(self, event) :
        #print 'resizeViewClimateDataWindow', 'event', event.width, event.height, 'window', self.view_climate_data_window.winfo_width(), self.view_climate_data_window.winfo_height(), '(req)', self.view_climate_data_window.winfo_reqwidth(), self.view_climate_data_window.winfo_reqheight(), 'figure', self.view_climate_data_figure.get_size_inches()
        #print 'canvas', self.view_climate_data_canvas.get_tk_widget().winfo_width(), self.view_climate_data_canvas.get_tk_widget().winfo_height(), '(req)', self.view_climate_data_canvas.get_tk_widget().winfo_reqwidth(), self.view_climate_data_canvas.get_tk_widget().winfo_reqheight()

        # Ignore config event?
        if self.ignore_grid_plot_config_events :
            #print 'ignoring:', self.ignore_grid_plot_config_events
            self.ignore_grid_plot_config_events -= 1
            return True

        if (event.width == self.view_climate_data_window.winfo_width() and event.height == self.view_climate_data_window.winfo_height() and
            (event.width != self.view_climate_data_window.winfo_reqwidth() or event.height != self.view_climate_data_window.winfo_reqheight())) :

            #print 'resizing'

            # Resize canvas (and figure)
            padding = 12 # difference when set
            if event.width != self.view_climate_data_window.winfo_reqwidth() :
                self.view_climate_data_canvas.get_tk_widget().configure(width=event.width-padding)
            if event.height != self.view_climate_data_window.winfo_reqheight() :
                buttons_required_height = padding + self.view_climate_data_window.winfo_reqheight() - self.view_climate_data_canvas.get_tk_widget().winfo_reqheight()
                self.view_climate_data_canvas.get_tk_widget().configure(height=event.height-buttons_required_height)
            
            # Set/calculate dimensions and margins
            maximum_width = self.view_climate_data_figure.get_figwidth()
            maximum_height = self.view_climate_data_figure.get_figheight()
            margin = 0.225*max(maximum_width/15.0, (maximum_width/15.0 + maximum_height/9.0)/2)
            title_margin = 0.495*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
            label_margin = 0.335*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
            colourbar_margin = 0.585*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
            colourbar_total_height = 1.125*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
            plot_width_to_height_ratio = self.current_plot_width_to_height_ratio
    
            # Determine best row x column configuration
            max_rows = 20
            max_cols = 20
            max_plot_width = 0
            best_config = None
            best_uses = None
            number_of_plots = len(self.view_climate_data_figure.get_axes()) - 1
            for rows in np.arange(1, min(number_of_plots+1, max_rows+1)) :
                cols = number_of_plots/rows + int(bool(number_of_plots%rows))
                if cols <= max_cols :
                    plot_width = (maximum_width - (cols + 1)*margin)/cols
                    plot_height = (maximum_height - title_margin - (rows - 1)*label_margin - colourbar_total_height)/rows
                    using = 'maximum_width'
                    if plot_width > plot_height*plot_width_to_height_ratio :
                        plot_width = plot_width_to_height_ratio*plot_height
                        using = 'maximum_height'
                    if plot_width > max_plot_width :
                        max_plot_width = plot_width
                        best_config = [int(rows), int(cols)]
                        best_uses = using
            max_plot_height = max_plot_width/plot_width_to_height_ratio

            # Set colorbar width relative to row:col configuration
            config_ratio = 1.0*best_config[0]/best_config[1]
            colourbar_width = maximum_width*(0.70+np.log2(config_ratio)*0.1) # 0.75
            colourbar_height = 0.015*colourbar_width

            # Update or adjust figure
            if best_config != self.current_plot_best_config :
                self.view_climate_data_window.unbind('<Configure>')
                self.view_climate_data_frame.grid_remove()
                self.after_idle(lambda: self.updateGridPlots())
                self.after_idle(lambda: self.view_climate_data_window.bind('<Configure>', self.__configureViewGridPlotWindow))
            else :
                # Adjust spacing and colorbar axis
                width = self.view_climate_data_figure.get_figwidth()
                height = self.view_climate_data_figure.get_figheight()
                self.view_climate_data_figure.subplots_adjust(left=(margin/width), right=(1.0-margin/width),
                                                              bottom=(colourbar_total_height/height), top=(1.0-title_margin/height),
                                                              wspace=(margin/max_plot_width), hspace=(label_margin/max_plot_height))
                self.view_climate_data_figure.get_axes()[-1].set_position([((1-colourbar_width/width)/2.0), (colourbar_margin/height), (colourbar_width/width), (colourbar_height/height)])

                # Update font sizes
                font_scale = (maximum_width/15.0 + maximum_height/9.0)/2
                self.current_figure_title.set_fontsize(14*font_scale)
                font_size = 12*font_scale
                for axes in self.view_climate_data_figure.get_axes() :
                    axes.get_xaxis().get_label().set_fontsize(font_size)
                for ticklabel in self.view_climate_data_figure.get_axes()[-1].get_xaxis().get_majorticklabels() :
                    ticklabel.set_fontsize(font_size)

    # Step 7 Method: Update Grid Plots (plot contents)
    def updateGridPlots(self, update=[]) :
        #print 'TODO: updateGridPlots', update

        # Remove current plot frame
        self.view_climate_data_frame.grid_remove()
        self.view_climate_data_figure.clear()

        # Create contoured data and masks if necessary
        if 'contoured' in update :
            if self.use_contoured_grid_maps :
                if not (self.grid_plot_contoured_parameter_data and self.grid_plot_contoured_region_masks) :
                    self.grid_plot_contoured_parameter_data = self.transformDataGridsForContours(self.grid_plot_parameter_data)
                    self.grid_plot_contoured_region_masks = []
                    for region_mask in self.grid_plot_region_masks :
                        self.grid_plot_contoured_region_masks.append(self.transformGridMaskForContours(region_mask))

        # Create grid plots
        figure_width = self.view_climate_data_figure.get_figwidth() - 0.12
        figure_height = self.view_climate_data_figure.get_figheight() - 0.12
        self.ignore_grid_plot_config_events = 2
        if self.use_contoured_grid_maps :
            self.createGridPlots(self.grid_plot_contoured_parameter_data, self.grid_plot_contoured_region_masks, figure_width=figure_width, figure_height=figure_height)
        else :
            self.createGridPlots(self.grid_plot_parameter_data, self.grid_plot_region_masks, figure_width=figure_width, figure_height=figure_height)

    # Step 7 Method: Create Grid Plots (plot contents)
    def createGridPlots(self, parameter_data, region_masks, figure_width=None, figure_height=None) :
        #print 'TODO: createGridPlots', figure_width, figure_height

        # Resolve selected parameter/group codes
        parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

        # Select fixed colour scheme via parameter codes and delta settings
        if self.utilise_delta.get() :
            if self.delta_as_percent.get() and self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code].has_key('%delta') :
                fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['%delta']
            else :
                fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['delta']
        else :
            fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['value']

        # Calculate colour scheme boundary values
        colour_scheme_boundaries = self.calculateColourSchemeBoundaries()

        # Adjust boundaries when zero boundary is set and permitted
        if self.map_colour_zero_boundary :
            if self.mapZeroBoundaryPermitted(precheck=True) :
                colour_scheme_boundaries_zero_index, colour_scheme_boundaries = self.adjustColourSchemeZeroBoundaries(colour_scheme_boundaries)
                if self.map_colour_palette in self.extended_colour_palettes :
                    self.updateExtendedColourMaps(self.map_colour_palette)
            else :
                self.map_colour_zero_boundary = False
                if self.map_colour_palette in self.extended_colour_palettes :
                    self.map_colour_palette = self.colour_palettes[0]

        # Resolve minimum and maximum data values and colour scheme interval from colour scheme boundaries
        data_min = colour_scheme_boundaries[0]
        data_max = colour_scheme_boundaries[-1]
        scheme_interval = colour_scheme_boundaries[1] - colour_scheme_boundaries[0]

        # Enforce near minimum and near maximum values on data
        near_data_min = data_min + 0.0001*scheme_interval
        near_data_max = data_max - 0.0001*scheme_interval
        for i, data_grid in enumerate(parameter_data) :
            parameter_data[i] = parameter_data[i]*(parameter_data[i] >= near_data_min) + (parameter_data[i] < near_data_min)*near_data_min
            parameter_data[i] = parameter_data[i]*(parameter_data[i] <= near_data_max) + (parameter_data[i] > near_data_max)*near_data_max
        
        # Construct main title
        title_prefix = ''
        if self.time_unit_text.get() == 'Month' :
            title_prefix = self.time_unit_months_text.get() + ' '
        elif self.time_unit_text.get() == 'Annual' and self.parameter_via_group_text[parameter_group_code].get().count('Annual') == 0 :
            title_prefix = 'Annual '
        if self.current_region in ['land', 'land-0-21KBP'] :
            title_prefix += 'Land '
        elif self.current_region in ['ocean', 'ocean-0-21KBP'] :
            title_prefix += 'Ocean '
        else :
            title_prefix += self.region_code_map[self.current_region] + ' '
        if self.current_region in ['n3', 'n3-4', 'n4', 'rola'] :
            title_prefix += 'Region '
        title_postfix = ''
        if self.time_unit_text.get() == 'Season' :
            title_postfix = ' for Season: ' + self.time_unit_seasons_text.get()
        elif self.time_unit_text.get() == 'User-defined' :
            title_postfix = ' for Months: ' + self.time_unit_other_text.get()
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]  
            delta_reference_text = str(self.delta_reference_value[delta_reference_period_code]['year']) + ' ' + self.delta_reference_value[delta_reference_period_code]['postfix']
            main_title = 'Change in ' + title_prefix + self.parameter_via_group_text[parameter_group_code].get() + ' Relative to ' + delta_reference_text + title_postfix
            if self.delta_as_percent.get() :
                main_title = '% ' + main_title
        else :
            main_title = title_prefix + self.parameter_via_group_text[parameter_group_code].get() + title_postfix
        self.current_plot_title = main_title

        # Get period and interval values to form grid plot titles
        period_ad_from = int(self.period_text['from'].get())
        period_ad_until = int(self.period_text['until'].get())
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            period_ad_from = 1950 - period_ad_from
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            period_ad_until = 1950 - period_ad_until
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
            delta_ref_period_ad = self.delta_reference_value[delta_reference_period_code]['year']
            if self.delta_reference_value[delta_reference_period_code]['postfix'] == self.period_postfix_keys[0] : # BP
                delta_ref_period_ad = 1950 - delta_ref_period_ad
            if delta_reference_period_code is 'previous' or delta_ref_period_ad == period_ad_from :
                period_ad_from += self.current_valid_interval_step_value
            elif delta_reference_period_code is 'next' or delta_ref_period_ad == period_ad_until :
                period_ad_until -= self.current_valid_interval_step_value
        period_intervals = []

        grid_plot_titles = []
        for ad_year in range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value) :
            if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # both BP
                grid_plot_titles.append(str(1950 - ad_year) + ' BP')
            elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # both AD
                grid_plot_titles.append(str(ad_year) + ' AD')
            elif self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # from BP until AD
                if ad_year <= 1950 :
                    grid_plot_titles.append(str(1950 - ad_year) + ' BP')
                else :
                    grid_plot_titles.append(str(ad_year) + ' AD')

        # Determine parameter colour palette # TODO: resolve any extended colour palettes
        colour_palette = self.map_colour_palette
##        if colour_palette == 'auto' :
##            if self.utilise_delta.get() :
##                colour_palette = self.parameter_default_colour_palette[parameter_group_code][parameter_code]['delta']
##            else :
##                colour_palette = self.parameter_default_colour_palette[parameter_group_code][parameter_code]['value']

        # Resolve region box for user-defined region if required
        region_box = self.region_bounding_box[self.current_region].copy()
        if self.current_region == 'user-defined' and self.region_mask.any() :
            region_box['lon'] = region_box['lon'][:]
            if self.userDefinedGridMaskRequiresShift() :
                region_mask = self.shiftGridMask180Degrees(self.region_mask)
                region_box['centre'] = 180
                region_box['lon'] = [0,360]
                if region_mask.nonzero()[1].min() >= 2 :
                    region_box['lon'][0] = np.arange(0, 362.5, 2.5)[region_mask.nonzero()[1].min() - 2]
                if region_mask.nonzero()[1].max() <= 141 :
                    region_box['lon'][1] = np.arange(0, 362.5, 2.5)[region_mask.nonzero()[1].max() + 3]
            else :
                region_mask = self.region_mask.copy()
                if region_mask.nonzero()[1].min() >= 2 :
                    region_box['lon'][0] = np.arange(-180, 182.5, 2.5)[region_mask.nonzero()[1].min() - 2]
                if region_mask.nonzero()[1].max() <= 141 :
                    region_box['lon'][1] = np.arange(-180, 182.5, 2.5)[region_mask.nonzero()[1].max() + 3]
            region_box['lat'] = region_box['lat'][:]
            if region_mask.nonzero()[0].min() >= 2 :
                region_box['lat'][1] = np.arange(90, -92.5, -2.5)[region_mask.nonzero()[0].min() - 2]
            if region_mask.nonzero()[0].max() <= 69 :
                region_box['lat'][0] = np.arange(90, -92.5, -2.5)[region_mask.nonzero()[0].max() + 3]

        # Basemap resolution: c (crude), l (low), i (intermediate), h (high), f (full)
        if self.current_region in ['globe', 'land', 'ocean', 'northern-hemisphere', 'southern-hemisphere', 'equatorial-pacific', 'n3', 'n3-4', 'n4', 'rola'] :
            basemap_resolution = 'c'
        elif self.current_region in ['japan', 'middle-east', 'alaska'] :
            basemap_resolution = 'i'
        elif self.current_region == 'user-defined':
            box_area = (region_box['lat'][1]-region_box['lat'][0])/2.5*(region_box['lon'][1]-region_box['lon'][0])/2.5
            if box_area > 1000 :
                basemap_resolution = 'c'
            elif box_area > 200 :
                basemap_resolution = 'l'
            else :
                basemap_resolution = 'i'
        else :
            basemap_resolution = 'l'

        # Setup the latitude and longitude variables
        latititudes = np.arange(90, -92.5, -2.5)
        longitudes = np.arange(region_box['centre']-180, region_box['centre']+182.5, 2.5)
        lons, lats = np.meshgrid(longitudes, latititudes)

        # Setup plots
        map_projection = 'cyl'
        bounding_lat = None
        if self.current_region == 'antarctica' :
            map_projection = 'spaeqd'
            bounding_lat = -60

        # Set/calculate dimensions and margins
        if figure_width :
            maximum_width = figure_width
        else :
            maximum_width = 15.0
        if figure_height :
            maximum_height = figure_height
        else :
            maximum_height = 9.0
        margin = 0.225*max(maximum_width/15.0, (maximum_width/15.0 + maximum_height/9.0)/2)
        title_margin = 0.495*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
        label_margin = 0.335*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
        colourbar_margin = 0.585*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
        colourbar_total_height = 1.125*max(maximum_height/9.0, (maximum_width/15.0 + maximum_height/9.0)/2)
        if self.current_region in ['antarctica'] :
            plot_width_to_height_ratio = 1.0
        else :
            plot_width_to_height_ratio = 1.0*(region_box['lon'][1] - region_box['lon'][0])/(region_box['lat'][1] - region_box['lat'][0])
        self.current_plot_width_to_height_ratio = plot_width_to_height_ratio

        # Determine best row x column configuration
        max_rows = 20
        max_cols = 20
        max_plot_width = 0
        best_config = None
        best_uses = None
        for rows in np.arange(1, min(len(parameter_data)+1, max_rows+1)) :
            cols = len(parameter_data)/rows + int(bool(len(parameter_data)%rows))
            if cols <= max_cols :
                plot_width = (maximum_width - (cols + 1)*margin)/cols
                plot_height = (maximum_height - title_margin - (rows - 1)*label_margin - colourbar_total_height)/rows
                using = 'maximum_width'
                if plot_width > plot_height*plot_width_to_height_ratio :
                    plot_width = plot_width_to_height_ratio*plot_height
                    using = 'maximum_height'
                if plot_width > max_plot_width :
                    max_plot_width = plot_width
                    best_config = [int(rows), int(cols)]
                    best_uses = using
        max_plot_height = max_plot_width/plot_width_to_height_ratio
        self.current_plot_best_config = best_config

        # Set colorbar width relative to row:col configuration
        config_ratio = 1.0*best_config[0]/best_config[1]
        colourbar_width = maximum_width*(0.70+np.log2(config_ratio)*0.1) # 0.75
        colourbar_height = 0.015*colourbar_width

        # Calculate width and height of best configuration
        if figure_width and figure_height :
            width = figure_width
            height = figure_height
        else :
            if best_uses == 'maximum_width' :
                width = maximum_width
                height = title_margin + max_plot_height*best_config[0] + label_margin*(best_config[0] - 1) + colourbar_total_height
            elif best_uses == 'maximum_height' :
                width = margin*(best_config[1] + 1) + max_plot_width*best_config[1]
                height = maximum_height
            if width < colourbar_width*1.1 :
                width = colourbar_width*1.1

        # Set font sizes relative to figure size
        font_scale = (width/15.0+height/9.0)/2
        title_font_size = 14*font_scale
        font_size = 12*font_scale

        # Create plots
        self.view_climate_data_frame = tk.Frame(self.view_climate_data_window, padx=0, pady=0)
        self.view_climate_data_figure = Figure(frameon=False, linewidth=0, dpi=100, figsize=(width, height))
        self.current_figure_title = self.view_climate_data_figure.suptitle(main_title, fontsize=title_font_size) #, y=0.97)
        self.view_climate_data_plot_axes = []
        self.climate_data_basemaps = []

        # Set linewidths
        if self.map_colour_boundary_lines :
            regular_boundary_linewidth = rcParams['lines.linewidth']*0.5
            zero_boundary_linewidth = rcParams['lines.linewidth']*1.5
            linewidths = np.ones_like(colour_scheme_boundaries)*regular_boundary_linewidth
            if self.map_colour_zero_boundary :
                linewidths[colour_scheme_boundaries_zero_index] = zero_boundary_linewidth
                self.colour_scheme_boundaries = colour_scheme_boundaries
                self.colour_scheme_boundaries_zero_index = colour_scheme_boundaries_zero_index

        for i, data in enumerate(parameter_data) :

            # Plot data on a base map
            self.view_climate_data_plot_axes.append(self.view_climate_data_figure.add_subplot(best_config[0], best_config[1], i+1))
            self.view_climate_data_plot_axes[i].set_xlabel(grid_plot_titles[i], fontsize=font_size) #set_title
            region_basemap = Basemap(ax=self.view_climate_data_plot_axes[i],
                                     lon_0=region_box['centre'],
                                     llcrnrlat=region_box['lat'][0],
                                     urcrnrlat=region_box['lat'][1],
                                     llcrnrlon=region_box['lon'][0],
                                     urcrnrlon=region_box['lon'][1],
                                     resolution=basemap_resolution,
                                     projection=map_projection,
                                     boundinglat=bounding_lat)
            self.climate_data_basemaps.append(region_basemap)
            self.climate_data_basemaps[i].drawmapboundary(fill_color='0.3')
            if self.use_contoured_grid_maps :
                masked_data = np.ma.masked_array(data, mask=((region_masks[i] - 1)*-1))
                im = self.climate_data_basemaps[i].contourf(lons, lats, masked_data, colour_scheme_boundaries, shading='flat', cmap=self.colourmaps[self.reverse_map_colour_palette][self.map_colour_palette], latlon=True, vmin=data_min, vmax=data_max)
                if self.map_colour_boundary_lines :
                    self.climate_data_basemaps[i].contour(lons, lats, masked_data, colour_scheme_boundaries, linewidths=linewidths, colors='k', linestyles='solid', latlon=True, vmin=data_min, vmax=data_max)
            else :
                masked_data = np.ma.masked_array(data, mask=((region_masks[i] - 1)*-1))
                im = self.climate_data_basemaps[i].pcolor(lons, lats, masked_data, shading='flat', cmap=self.colourmaps[self.reverse_map_colour_palette][self.map_colour_palette], latlon=True, vmin=data_min, vmax=data_max, snap=True)
                if self.map_colour_boundary_lines :
                    colour_indexes = np.zeros_like(masked_data)
                    for boundary_value in colour_scheme_boundaries[1:-1] :
                        colour_indexes += (masked_data >= boundary_value)
                    if self.map_colour_zero_boundary :
                        isZeroBoundary = lambda a, b: (np.array([a,b]) >= colour_scheme_boundaries_zero_index).any() and (np.array([a,b]) < colour_scheme_boundaries_zero_index).any()
                    else :
                        isZeroBoundary = lambda a, b: False
                    boundary_lines = []
                    boundary_linewidth = { False : regular_boundary_linewidth, True : zero_boundary_linewidth }
                    for iy, lat in enumerate(latititudes[:-1]) :
                        for jx, lon in enumerate(longitudes[:-1]) :
                            if jx < 143 and colour_indexes[iy,jx] != colour_indexes[iy,jx+1] :
                                if map_projection == 'cyl' :
                                    if isZeroBoundary(colour_indexes[iy,jx], colour_indexes[iy,jx+1]) :
                                        self.view_climate_data_plot_axes[i].plot([lon+2.5, lon+2.5], [lat, lat-2.5], 'k-', linewidth=zero_boundary_linewidth)
                                    else :
                                        boundary_lines.append([(lon+2.5,lat),(lon+2.5,lat-2.5)])
                                else :
                                    self.climate_data_basemaps[i].plot([lon+2.5, lon+2.5], [lat, lat-2.5], 'k-', latlon=True, linewidth=boundary_linewidth[isZeroBoundary(colour_indexes[iy,jx], colour_indexes[iy,jx+1])])
                            if iy < 71 and colour_indexes[iy,jx] != colour_indexes[iy+1,jx] :
                                if map_projection == 'cyl' :
                                    if isZeroBoundary(colour_indexes[iy,jx], colour_indexes[iy+1,jx]) :
                                        self.view_climate_data_plot_axes[i].plot([lon, lon+2.5], [lat-2.5, lat-2.5], 'k-', linewidth=zero_boundary_linewidth)
                                    else :
                                        boundary_lines.append([(lon,lat-2.5),(lon+2.5,lat-2.5)])
                                else :
                                    self.climate_data_basemaps[i].plot([lon, lon+2.5], [lat-2.5, lat-2.5], 'k-', latlon=True, linewidth=boundary_linewidth[isZeroBoundary(colour_indexes[iy,jx], colour_indexes[iy+1,jx])])
                    if map_projection == 'cyl' :
                        self.view_climate_data_plot_axes[i].add_collection(LineCollection(boundary_lines, colors='k', linewidths=regular_boundary_linewidth))
            if self.show_grid_map_land_boundaries :
                self.climate_data_basemaps[i].drawcoastlines()

            # Grid lines and ticks
            if self.show_map_grid_lines :
                region_longitudes = longitudes[((longitudes >= region_box['lon'][0])*(longitudes <= region_box['lon'][1])).nonzero()]
                region_latititudes = latititudes[((latititudes >= region_box['lat'][0])*(latititudes <= region_box['lat'][1])).nonzero()]
                if self.map_grid_space :
                    map_grid_space = self.map_grid_space
                else :
                    map_grid_space = region_box['grid']                
                self.view_climate_data_plot_axes[i].set_xticks(region_longitudes[((region_longitudes % map_grid_space) == 0. ).nonzero()])
                self.view_climate_data_plot_axes[i].set_yticks(region_latititudes[((region_latititudes % map_grid_space) == 0. ).nonzero()])
                self.view_climate_data_plot_axes[i].set_xticklabels([])
                self.view_climate_data_plot_axes[i].set_yticklabels([])
                if self.map_grid_include == 'lines' :
                    self.view_climate_data_plot_axes[i].grid(b=True, which='major', axis='both')

            # Update status bar
            self.generation_status_bar['value'] += self.generation_status_times['view']['map']
            if self.region_is_time_dependent[self.current_region] :
                self.generation_status_bar['value'] += self.generation_status_times['view']['time-dependent']
            self.update_idletasks()
        
        # Adjust spacing and make an axis for the colorbar on the bottom
        self.view_climate_data_figure.subplots_adjust(left=(margin/width), right=(1.0-margin/width),
                                                      bottom=(colourbar_total_height/height), top=(1.0-title_margin/height),
                                                      wspace=(margin/max_plot_width), hspace=(label_margin/max_plot_height))
        cax = self.view_climate_data_figure.add_axes([((1-colourbar_width/width)/2.0), (colourbar_margin/height), (colourbar_width/width), (colourbar_height/height)])
        if self.map_colour_scheme == '90%_range' :
            cb_label_boundaries = colour_scheme_boundaries[1:-1]
        else : # fixed_range
            cb_label_boundaries = colour_scheme_boundaries[:]
            if fixed_range_colour_scheme['first_boundary'] != None and fixed_range_colour_scheme['min'] == None :
                cb_label_boundaries = cb_label_boundaries[1:]
            if fixed_range_colour_scheme['last_boundary'] != None and fixed_range_colour_scheme['max'] == None :
                cb_label_boundaries = cb_label_boundaries[:-1]
        cb = self.view_climate_data_figure.colorbar(im, cax=cax, orientation='horizontal', boundaries=colour_scheme_boundaries, ticks=cb_label_boundaries, drawedges=self.map_colour_boundary_lines)#, shrink=0.75)
        cax.xaxis.set_ticks_position('none')
        if self.map_colour_boundary_lines :
            cb.dividers.set_linewidths(linewidths[1:-1])
            if self.map_colour_zero_boundary and colour_scheme_boundaries_zero_index in [0,11] :
                cax.set_xlim(left=-0.002)
                zero_boundary_x_value = { 0 : 0, 11 : 1 }
                vl = cax.axvline(zero_boundary_x_value[colour_scheme_boundaries_zero_index], color='k', linewidth=zero_boundary_linewidth)
        self.cax = cax
        self.cb = cb
        if self.delta_as_percent.get() :
            cb.set_label('%')
        else :
            cb.set_label(self.parameter_unit_string[parameter_group_code][parameter_code])
        cax.get_xaxis().get_label().set_fontsize(font_size)
        for ticklabel in cax.get_xaxis().get_majorticklabels() :
            ticklabel.set_fontsize(font_size)

        # Plot the region map
        self.view_climate_data_canvas = FigureCanvasTkAgg(self.view_climate_data_figure, master=self.view_climate_data_frame)
        self.view_climate_data_canvas.show()
        self.view_climate_data_canvas.get_tk_widget().grid(row=0, column=0) #.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.view_climate_data_frame.grid(row=0, column=0, padx=0, pady=0)

        # Add toolbar
        toolbar = NavigationToolbar2TkAgg(self.view_climate_data_canvas, self.view_climate_data_frame) #self.view_climate_data_window)
        toolbar.update()
        toolbar.grid(row=1, column=0, padx=0, pady=0)
        toolbar.grid_remove()
        tool_option_values = self.getToolOptions()
        if not(self.current_figure_save_directory and path.exists(self.current_figure_save_directory)) and (tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory'])) :
            rcParams['savefig.directory'] = tool_option_values['default_file_generation_directory']
        self.current_figure_toolbar = toolbar
        button_frame = tk.Frame(self.view_climate_data_frame, padx=0, pady=0)
        self.grid_plot_zoom_text = tk.StringVar(value='Zoom')
        tk.Button(button_frame, text='Options', anchor=tk.CENTER, command=self.editMapOptions).grid(row=0, column=0, padx=0, pady=0)
        tk.Button(button_frame, textvariable=self.grid_plot_zoom_text, anchor=tk.CENTER, command=self.zoomFigureViaToolbar).grid(row=0, column=1, padx=5, pady=0)
        tk.Button(button_frame, text='Statistics', anchor=tk.CENTER, command=self.viewGridPlotStatistics).grid(row=0, column=2, padx=0, pady=0)
        tk.Button(button_frame, text='Save', anchor=tk.CENTER, command=self.saveFigureViaToolbar).grid(row=0, column=3, padx=5, pady=0)
        tk.Button(button_frame, text='Close', anchor=tk.CENTER, command=self.closeFigureWindow).grid(row=0, column=4, padx=0, pady=0)
        button_frame.grid(row=1, column=0, padx=0, pady=5)

    # Step 7 Method: Zoom Figure Via Toolbar
    def zoomFigureViaToolbar(self) :
        if self.grid_plot_zoom_text.get() == 'Zoom' :
            self.current_figure_toolbar.zoom()
            self.grid_plot_zoom_text.set('Reset')
        else : # reset
            self.current_figure_toolbar.home()
            self.current_figure_toolbar.zoom()
            self.grid_plot_zoom_text.set('Zoom')

    # Step 7 Method: View Grid Plot Statistics
    def viewGridPlotStatistics(self) :
        
        # Remove existing grid plot statistics window
        if hasattr(self, 'grid_plot_statistics_window') :
            self.grid_plot_statistics_window.destroy()

        # Create window
        self.grid_plot_statistics_window = tk.Toplevel(self.view_climate_data_window)
        self.grid_plot_statistics_window.title('Grid Plot Statistics')
        self.grid_plot_statistics_window.transient(self.view_climate_data_window)
        self.grid_plot_statistics_window.focus_set()

        # Gather years for statistics data frame
        years = self.grid_plot_statistics['years_ad'][:]
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # both BP
            year_title = 'Year (BP)'
            for i, year in enumerate(years) :
                years[i] = 1950 - year
        elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # both AD
            year_title = 'Year (AD)'
        elif self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # from BP until AD
            year_title = 'Year'
            for i, year in enumerate(years) :
                if year <= 1950 :
                    years[i] = str(1950 - year) + 'BP'
                else :
                    years[i] = str(year) + 'AD'

        # Create a data frame from statistics
        if self.public_release or True :
            statistic_fields_included = ['minimum', 'percentile_5th', 'percentile_50th', 'percentile_95th', 'maximum', 'area_mean']
##        else :
##            statistic_fields_included = self.grid_region_statistics_keys # ['minimum', 'percentile_5th', 'percentile_25th', 'percentile_50th', 'percentile_75th', 'percentile_95th', 'maximum', 'grid_mean', 'grid_stdev', 'area_mean', 'area_stdev']
        if self.current_region != 'globe' :
            indexes = ['Region', year_title]
            region_list = []
            for i in range(len(years)) :
                region_list.append(self.region_selection_text.get()*int(not(i)))
            for i in range(len(years)) :
                region_list.append('Global'*int(not(i)))
            years.extend(years)
            data_dict = { 'Region' : region_list, year_title : years }
        else :
            indexes = [year_title]
            data_dict = { year_title : years }
        for statistic_field in statistic_fields_included :
            indexes.append(self.grid_region_statistics_names[statistic_field])
            data_dict[self.grid_region_statistics_names[statistic_field]] = self.grid_plot_statistics['region'][statistic_field][:]
            if self.current_region != 'globe' :
                data_dict[self.grid_region_statistics_names[statistic_field]].extend(self.grid_plot_statistics['global'][statistic_field])
        self.current_grid_plot_statistics_data_frame = pd.DataFrame(data_dict)[indexes]

        # Display statistics
        display_font = Font(font='TkFixedFont')
        statistics_text = self.current_plot_title + '\n' + '-'*len(self.current_plot_title) + '\n' + self.current_grid_plot_statistics_data_frame.to_string(index=False, float_format=(lambda f: '%.3f'%f))
        display_label_font = Font(family=display_font.cget('family'), size=display_font.cget('size')) #, weight='bold')
        tk.Label(self.grid_plot_statistics_window, text=statistics_text, font=display_label_font, bg='white', justify=tk.LEFT, padx=10, pady=10).grid(row=0, column=0, sticky=tk.NW+tk.SE, padx=0, pady=0)

        # Save and close buttons
        button_frame = tk.Frame(self.grid_plot_statistics_window, padx=0, pady=0)
        tk.Button(button_frame, text='Save', anchor=tk.CENTER, command=self.saveGridPlotStatistics).grid(row=0, column=0, padx=5, pady=0)
        tk.Button(button_frame, text='Close', anchor=tk.CENTER, command=self.closeGridPlotStatisticsWindow).grid(row=0, column=1, padx=0, pady=0)
        button_frame.grid(row=1, column=0, padx=0, pady=5)

    # Step 7 Method: Save Grid Plot Statistics
    def saveGridPlotStatistics(self) :
        if self.current_figure_save_directory :
            initialdir = self.current_figure_save_directory
        else :
            tool_option_values = self.getToolOptions()
            initialdir = tool_option_values['default_file_generation_directory']
            if not initialdir :
                if MAC_VERSION and environ.has_key('HOME') and path.exists(environ['HOME']) :
                    initialdir = environ['HOME']
                elif environ.has_key('USERPROFILE') and path.exists(environ['USERPROFILE']) : # PC version
                    initialdir = environ['USERPROFILE']
                else :
                    initialdir = getcwd()
        file_path = asksaveasfilename(master=self.grid_plot_statistics_window,
                                      title='Save Grid Plot Statistics',
                                      filetypes=[('Text document','*.txt')],
                                      defaultextension='.txt',
                                      initialdir=initialdir,
                                      initialfile='grid_plot_statistics.txt')
        if file_path :
            file_path = path.normpath(str(file_path))
            try :
                self.data_file_helper.generateTextTable(self.current_grid_plot_statistics_data_frame, self.current_plot_title, file_path=file_path)
                statistics_table_path_dict = self.data_file_helper.splitPath(file_path)
                self.updateToolGenerationLogEntry(statistics_table=statistics_table_path_dict)
                self.updateToolGenerationLogs()
            except Exception, e :
                showerror('File Save Error', 'Error saving grid plot statistics to \"'+file_path+'\". Check file permissions.')
                print >> sys.stderr, 'Error saving grid plot statistics to \"'+file_path+'\"', e

    # Step 7 Method: Close Grid Plot Statistics Window
    def closeGridPlotStatisticsWindow(self) :
        if hasattr(self, 'grid_plot_statistics_window') :
            self.grid_plot_statistics_window.destroy()

    # Step 7 Method: Save Figure Via Toolbar
    def saveFigureViaToolbar(self) :
        figure_path = self.current_figure_toolbar.save_figure(initialfile='figure', filetypes=['png', 'pdf'])
        if figure_path :
            figure_path = path.normpath(str(figure_path))
            if path.exists(figure_path) :
                figure_path_dict = self.data_file_helper.splitPath(figure_path)
                self.current_figure_save_directory = figure_path_dict['directory']
                self.updateToolGenerationLogEntry(figure=figure_path_dict)
                self.updateToolGenerationLogs()

    # Step 7 Method: Close Figure Window
    def closeFigureWindow(self) :
        if hasattr(self, 'view_climate_data_window') :
            self.view_climate_data_window.destroy()

    # Step 7 Method: View Series Plot
    def viewSeriesPlot(self, parameter_data) :
        #print 'TODO: viewSeriesPlot'

        # Remove existing climate data window
        if hasattr(self, 'view_climate_data_window') :
            self.view_climate_data_window.destroy()

        # Create the view plot window
        self.view_climate_data_window = tk.Toplevel(self)
        self.view_climate_data_window.title('View Time Series Plot')
        self.view_climate_data_window.transient(self)
        self.view_climate_data_window.focus_set()
        self.current_view_climate_data_window_type = 'series'

        # Parameter range for time series
        self.parameter_range_for_time_series = { 'temperature' : {}, 'precipitation' : {}, 'humidity' : {}, 'sea-level-pressure' : {}, 'southern-oscillation' : {} }
        for parameter in ['mean-temperature', 'minimum-temperature', 'maximum-temperature'] :
            self.parameter_range_for_time_series['temperature'][parameter] = { 'min' : None, 'max' : None }
        for parameter in ['diurnal-temperature-range', 'annual-temperature-range'] :
            self.parameter_range_for_time_series['temperature'][parameter] = { 'min' : 0, 'max' : None }
        self.parameter_range_for_time_series['temperature']['isothermality'] = { 'min' : None, 'max' : None }
        self.parameter_range_for_time_series['temperature']['temperature-seasonality'] = { 'min' : 0, 'max' : None }
        self.parameter_range_for_time_series['precipitation']['mean-precipitation'] = { 'min' : 0, 'max' : None }
        self.parameter_range_for_time_series['precipitation']['precipitation-seasonality'] = { 'min' : 0, 'max' : None }
        self.parameter_range_for_time_series['humidity']['specific-humidity'] = { 'min' : 0, 'max' : None }
        self.parameter_range_for_time_series['humidity']['relative-humidity'] = { 'min' : 0, 'max' : 100 }
        self.parameter_range_for_time_series['sea-level-pressure']['sea-level-pressure'] = { 'min' : None, 'max' : None }
        self.parameter_range_for_time_series['southern-oscillation']['soi'] = { 'min' : None, 'max' : None }
        self.parameter_range_for_time_series['southern-oscillation']['enso'] = { 'min' : None, 'max' : None }

        # Plot options (for gridded data only)
        if self.public_release :
            self.series_plot_options = ['median', '5th-median-95th', 'min-median-max', 'area_mean']
            self.current_series_plot_option = '5th-median-95th'
        else :
            self.series_plot_options = ['grid_mean', 'grid_mean-1grid_sd', 'grid_mean-2grid_sd',
                                        'area_mean', 'area_mean-1grid_sd', 'area_mean-2grid_sd', 'area_mean-1area_sd', 'area_mean-2area_sd',
                                        'median', 'q1-median-q3', '5th-median-95th', 'min-median-max']
            self.current_series_plot_option = 'area_mean-1grid_sd'
        self.series_plot_config = {}
        self.series_plot_config['grid_mean'] = { 'name' : 'Mean (grid)', 'mid' : 'grid_mean', 'interval' : None }
        self.series_plot_config['grid_mean-1grid_sd'] = { 'name' : 'Mean (grid) '+u'\u00B1'+' 1 Standard Deviation', 'mid' : 'grid_mean',
                                                          'interval' : { 'lower' : 'grid_mean-grid_stdev', 'upper' : 'grid_mean+grid_stdev' } }
        self.series_plot_config['grid_mean-2grid_sd'] = { 'name' : 'Mean (grid) '+u'\u00B1'+' 2 Standard Deviations', 'mid' : 'grid_mean',
                                                          'interval' : { 'lower' : 'grid_mean-2*grid_stdev', 'upper' : 'grid_mean+2*grid_stdev' } }
        self.series_plot_config['area_mean'] = { 'name' : 'Area Mean', 'mid' : 'area_mean', 'interval' : None }
        self.series_plot_config['area_mean-1grid_sd'] = { 'name' : 'Area Mean '+u'\u00B1'+' 1 Standard Deviation (grid)', 'mid' : 'area_mean',
                                                          'interval' : { 'lower' : 'area_mean-grid_stdev', 'upper' : 'area_mean+grid_stdev' } }
        self.series_plot_config['area_mean-2grid_sd'] = { 'name' : 'Area Mean '+u'\u00B1'+' 2 Standard Deviations (grid)', 'mid' : 'area_mean',
                                                          'interval' : { 'lower' : 'area_mean-2*grid_stdev', 'upper' : 'area_mean+2*grid_stdev' } }
        self.series_plot_config['area_mean-1area_sd'] = { 'name' : 'Area Mean '+u'\u00B1'+' 1 Area Standard Deviation', 'mid' : 'area_mean',
                                                          'interval' : { 'lower' : 'area_mean-area_stdev', 'upper' : 'area_mean+area_stdev' } }
        self.series_plot_config['area_mean-2area_sd'] = { 'name' : 'Area Mean '+u'\u00B1'+' 2 Area Standard Deviations', 'mid' : 'area_mean',
                                                          'interval' : { 'lower' : 'area_mean-2*area_stdev', 'upper' : 'area_mean+2*area_stdev' } }
        self.series_plot_config['median'] = { 'name' : 'Median', 'mid' : 'percentile_50th', 'interval' : None }
        self.series_plot_config['q1-median-q3'] = { 'name' : 'Q1-Median-Q3', 'mid' : 'percentile_50th',
                                                    'interval' : { 'lower' : 'percentile_25th', 'upper' : 'percentile_75th' } }
        self.series_plot_config['5th-median-95th'] = { 'name' : '5th-50th-95th Percentiles', 'mid' : 'percentile_50th',
                                                       'interval' : { 'lower' : 'percentile_5th', 'upper' : 'percentile_95th' } }
        self.series_plot_config['min-median-max'] = { 'name' : 'Minimum-Median-Maximum', 'mid' : 'percentile_50th',
                                                      'interval' : { 'lower' : 'minimum', 'upper' : 'maximum' } }
        
        # Create series plot contents
        self.ignore_series_plot_config_events = 0
        self.createSeriesPlot(parameter_data)

        # Bind window to resize/configure events
        self.view_climate_data_window.bind('<Configure>', self.__configureViewSeriesPlotWindow)

    # Step 7 Method: Configure View Series Plot Window (Event)
    def __configureViewSeriesPlotWindow(self, event) :
        #print 'TODO: __configureViewSeriesPlotWindow', 'event', event.width, event.height, 'window', self.view_climate_data_window.winfo_width(), self.view_climate_data_window.winfo_height(), '(req)', self.view_climate_data_window.winfo_reqwidth(), self.view_climate_data_window.winfo_reqheight(), 'fig', self.view_climate_data_figure.get_figwidth(), self.view_climate_data_figure.get_figheight()

        # Ignore config event?
        if self.ignore_series_plot_config_events :
            #print 'ignoring:', self.ignore_series_plot_config_events
            self.ignore_series_plot_config_events -= 1
            return True

        if (event.width == self.view_climate_data_window.winfo_width() and event.height == self.view_climate_data_window.winfo_height() and
            (event.width != self.view_climate_data_window.winfo_reqwidth() or event.height != self.view_climate_data_window.winfo_reqheight())) :

            #print 'resizing'

            # Resize canvas (and figure)
            padding = 12 # difference when set
            buttons_required_height = padding + self.view_climate_data_window.winfo_reqheight() - self.view_climate_data_canvas.get_tk_widget().winfo_reqheight()
            if event.width != self.view_climate_data_window.winfo_reqwidth() :
                self.view_climate_data_canvas.get_tk_widget().configure(width=event.width-padding)
            if event.height != self.view_climate_data_window.winfo_reqheight() :
                self.view_climate_data_canvas.get_tk_widget().configure(height=event.height-buttons_required_height)

            # Adjust spacing
            figure_width = self.view_climate_data_figure.get_figwidth()
            figure_height = self.view_climate_data_figure.get_figheight()
            if self.time_unit_is_all_months :
                initial_height = 9.0 #(14, 9)
                left_margin = 0.06*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
                right_margin = 0.04*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
                top_margin = 0.06*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
                bot_margin = 0.08*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
                w_space = 0.20*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
                h_space = 0.40*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
                self.view_climate_data_figure.subplots_adjust(left=(left_margin/figure_width), right=(1.0-right_margin/figure_width),
                                                              bottom=(bot_margin/figure_height), top=(1.0-top_margin/figure_height),
                                                              wspace=(w_space/figure_width), hspace=(h_space/figure_height))
            else :
                initial_height = 8.0 #(14, 8)
                left_margin = 0.08*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
                right_margin = 0.04*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
                top_margin = 0.07*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
                bot_margin = 0.10*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
                self.view_climate_data_figure.subplots_adjust(left=(left_margin/figure_width), right=(1.0-right_margin/figure_width),
                                                              bottom=(bot_margin/figure_height), top=(1.0-top_margin/figure_height))

            # Update font sizes
            font_scale = (figure_width/14.0 + figure_height/initial_height)/2
            self.current_figure_title.set_fontsize(14*font_scale)
            font_size = 12*font_scale
            for axes in self.view_climate_data_figure.get_axes() :
                axes.get_xaxis().get_label().set_fontsize(font_size)
                axes.get_yaxis().get_label().set_fontsize(font_size)
                for ticklabel in axes.get_xaxis().get_majorticklabels() :
                    ticklabel.set_fontsize(font_size)
                for ticklabel in axes.get_yaxis().get_majorticklabels() :
                    ticklabel.set_fontsize(font_size)

    # Step 7 Method: Create Series Plot
    def createSeriesPlot(self, parameter_data, figure_width=None, figure_height=None) :
        #print 'TODO: createSeriesPlot', figure_width, figure_height

        # Resolve selected parameter/group codes
        parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

        # Is the parameter data gridded?
        parameter_data_is_gridded = self.data_file_helper.parameterDataIsGridded(parameter_group_code, parameter_code)

        # Get period and interval values to form grid plot titles
        period_ad_from = int(self.period_text['from'].get())
        period_ad_until = int(self.period_text['until'].get())
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            period_ad_from = 1950 - period_ad_from
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            period_ad_until = 1950 - period_ad_until
        period_intervals = []
        for ad_year in range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value) :
            period_intervals.append({ 'from' : (ad_year - self.current_valid_interval_size_value/2), 'until' : (ad_year + self.current_valid_interval_size_value/2 - int(not bool(self.current_valid_interval_size_value%2))) })
        mid_interval_ad_years = []
        for period_interval in period_intervals :
            mid_interval_ad_years.append((period_interval['until']+period_interval['from']+1)/2)

        # Convert back to BP when period from is BP
        x_min = int(period_intervals[0]['from'])
        x_max = int(period_intervals[:].pop()['until'])
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            mid_interval_years = (1950 - np.array(mid_interval_ad_years)).tolist()
            x_min = 1950 - x_min
            x_max = 1950 - x_max
        else :
            mid_interval_years = mid_interval_ad_years

        # Construct main title
        title_prefix = ''
        if self.time_unit_text.get() == 'Month' :
            title_prefix = self.time_unit_months_text.get() + ' '
        elif self.time_unit_text.get() == 'Annual' and self.parameter_via_group_text[parameter_group_code].get().count('Annual') == 0 :
            title_prefix = 'Annual '
        if self.current_region in ['land', 'land-0-21KBP'] :
            title_prefix += 'Land '
        elif self.current_region in ['ocean', 'ocean-0-21KBP'] :
            title_prefix += 'Ocean '
        else :
            title_prefix += self.region_code_map[self.current_region] + ' '
        if self.current_region in ['n3', 'n3-4', 'n4', 'rola'] :
            title_prefix += 'Region '
        title_postfix = ''
        if self.time_unit_text.get() == 'Season' :
            title_postfix = ' for Season: ' + self.time_unit_seasons_text.get()
        elif self.time_unit_text.get() == 'User-defined' :
            title_postfix = ' for Months: ' + self.time_unit_other_text.get()
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]  
            delta_reference_text = str(self.delta_reference_value[delta_reference_period_code]['year']) + ' ' + self.delta_reference_value[delta_reference_period_code]['postfix']
            main_title = 'Change in ' + title_prefix + self.parameter_via_group_text[parameter_group_code].get() + ' Relative to ' + delta_reference_text + title_postfix
            if self.delta_as_percent.get() :
                main_title = '% ' + main_title
        else :
            main_title = title_prefix + self.parameter_via_group_text[parameter_group_code].get() + title_postfix
        if parameter_data_is_gridded :
            main_title += ': Region ' + self.series_plot_config[self.current_series_plot_option]['name']

        # Plot 12 subplots if all months
        if self.time_unit_is_all_months :
            subplots = 12 # self.month_names
            plot_rows = 4
            plot_columns = 3
            initial_height = 9.0
        else :
            subplots = 1
            plot_rows = 1
            plot_columns = 1
            initial_height = 8.0
            parameter_data = [parameter_data]
        if figure_width :
            figure_width -= 0.12
        else :
            figure_width = 14.0
        if figure_height :
            figure_height -= 0.12
        else :
            figure_height = initial_height

        # Set font sizes relative to figure size
        font_scale = (figure_width/14.0 + figure_height/initial_height)/2
        title_font_size = 14*font_scale
        font_size = 12*font_scale

        # Statistical data structure (gridded) or raw values (ungridded)?
        if parameter_data_is_gridded : # Resolve data intervals using config
            mid_data = []
            lower_data = []
            upper_data = []
            for i in range(subplots) :
                for statistic_key, statistic_values in parameter_data[i].items() :
                    exec(statistic_key + ' = np.array(statistic_values)')
                mid_data.append(eval(self.series_plot_config[self.current_series_plot_option]['mid']))
                if self.series_plot_config[self.current_series_plot_option]['interval'] :
                    lower_data.append(eval(self.series_plot_config[self.current_series_plot_option]['interval']['lower']))
                    upper_data.append(eval(self.series_plot_config[self.current_series_plot_option]['interval']['upper']))
        else :
            mid_data = parameter_data
            lower_data = []
            upper_data = []

        # Find minimum and maximum data values
        data_min = np.append(mid_data, lower_data).min()
        data_max = np.append(mid_data, upper_data).max()
        data_range = data_max - data_min
        data_min -= abs(data_range)*0.1
        data_max += abs(data_range)*0.1
        if self.utilise_delta.get() :
            if data_min > 0 :
                data_min = 0
            elif data_max < 0 :
                data_max = 0
        else :
            if self.parameter_range_for_time_series[parameter_group_code][parameter_code]['min'] != None and data_min < self.parameter_range_for_time_series[parameter_group_code][parameter_code]['min'] :
                data_min = self.parameter_range_for_time_series[parameter_group_code][parameter_code]['min']
            if self.parameter_range_for_time_series[parameter_group_code][parameter_code]['max'] != None and data_max > self.parameter_range_for_time_series[parameter_group_code][parameter_code]['max'] :
                data_max = self.parameter_range_for_time_series[parameter_group_code][parameter_code]['max']

        # Setup plots
        self.view_climate_data_frame = tk.Frame(self.view_climate_data_window, padx=0, pady=0)
        self.view_climate_data_figure = Figure(frameon=True, linewidth=0, dpi=100, figsize=(figure_width, figure_height))
        self.current_figure_title = self.view_climate_data_figure.suptitle(main_title, fontsize=title_font_size)
        self.view_climate_data_plot_axes = []
        for i in range(subplots) :
            self.view_climate_data_plot_axes.append(self.view_climate_data_figure.add_subplot(plot_rows, plot_columns, i+1))
            self.view_climate_data_plot_axes[i].plot(mid_interval_years, mid_data[i])
            if parameter_data_is_gridded and self.series_plot_config[self.current_series_plot_option]['interval'] :
                self.view_climate_data_plot_axes[i].fill_between(mid_interval_years, lower_data[i], upper_data[i], facecolor='yellow', alpha=0.5)
            if self.parameter_unit_string[parameter_group_code][parameter_code] and (not self.time_unit_is_all_months or (i+1)%plot_columns == 1) :
                if self.delta_as_percent.get() :
                    self.view_climate_data_plot_axes[i].set_ylabel('%', fontsize=font_size)
                else :
                    self.view_climate_data_plot_axes[i].set_ylabel(self.parameter_unit_string[parameter_group_code][parameter_code], fontsize=font_size)
            if self.time_unit_is_all_months :
                self.view_climate_data_plot_axes[i].locator_params(axis='x', nbins=5)
            if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
                self.view_climate_data_plot_axes[i].invert_xaxis()
            self.view_climate_data_plot_axes[i].set_xbound(lower=x_min, upper=x_max)
            self.view_climate_data_plot_axes[i].set_ybound(lower=data_min, upper=data_max)
            for ticklabel in self.view_climate_data_plot_axes[i].get_xaxis().get_majorticklabels() :
                ticklabel.set_fontsize(font_size)
            for ticklabel in self.view_climate_data_plot_axes[i].get_yaxis().get_majorticklabels() :
                ticklabel.set_fontsize(font_size)

            # Update status bar
            self.generation_status_bar['value'] += self.generation_status_times['view']['series']
            self.update_idletasks()

        # Adjust spacing
        if self.time_unit_is_all_months :
            left_margin = 0.06*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
            right_margin = 0.04*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
            top_margin = 0.06*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
            bot_margin = 0.08*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
            w_space = 0.20*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
            h_space = 0.40*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
            self.view_climate_data_figure.subplots_adjust(left=(left_margin/figure_width), right=(1.0-right_margin/figure_width),
                                                          bottom=(bot_margin/figure_height), top=(1.0-top_margin/figure_height),
                                                          wspace=(w_space/figure_width), hspace=(h_space/figure_height))
        else :
            left_margin = 0.08*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
            right_margin = 0.04*14.0*max(figure_width/14.0, (figure_width/14.0 + figure_height/initial_height)/2)
            top_margin = 0.07*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
            bot_margin = 0.10*initial_height*max(figure_height/initial_height, (figure_width/14.0 + figure_height/initial_height)/2)
            self.view_climate_data_figure.subplots_adjust(left=(left_margin/figure_width), right=(1.0-right_margin/figure_width),
                                                          bottom=(bot_margin/figure_height), top=(1.0-top_margin/figure_height))
        # Plot the figure
        self.view_climate_data_canvas = FigureCanvasTkAgg(self.view_climate_data_figure, master=self.view_climate_data_frame)
        self.view_climate_data_canvas.show()
        self.view_climate_data_canvas.get_tk_widget().grid(row=0, column=0)
        self.view_climate_data_frame.grid(row=0, column=0, padx=0, pady=0)

        # Alter x title and labels as required
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # both BP
            x_title = 'Year (BP)'
        elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # both AD
            x_title = 'Year (AD)'
        elif self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # from BP until AD
            x_title = 'Year'
            for i in range(subplots) :
                xticklabels = []
                for xticklabel in self.view_climate_data_plot_axes[i].get_xticklabels() :
                    xticklabel = str(xticklabel.get_text().replace(u'\u2212', '-')) # avoid large dash negative sign character
                    if self.isInteger(xticklabel) and int(xticklabel) < 1 : # convert to AD
                        xticklabels.append(str((1950 - int(xticklabel))) + 'AD')
                    elif self.isInteger(xticklabel) : # append 'BP'
                        xticklabels.append(xticklabel + 'BP')
                    else :
                        xticklabels.append('')
                self.view_climate_data_plot_axes[i].set_xticklabels(xticklabels)
        for i in range(subplots) :
            if self.time_unit_is_all_months :
                self.view_climate_data_plot_axes[i].set_xlabel((self.month_names[i] + ', ' + x_title), fontsize=font_size)
            else :
                self.view_climate_data_plot_axes[i].set_xlabel(x_title, fontsize=font_size)

        # Add toolbar
        toolbar = NavigationToolbar2TkAgg(self.view_climate_data_canvas, self.view_climate_data_window)
        toolbar.update()
        toolbar.grid(row=1, column=0, padx=0, pady=0)
        toolbar.grid_remove()
        tool_option_values = self.getToolOptions()
        if not(self.current_figure_save_directory and path.exists(self.current_figure_save_directory)) and (tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory'])) :
            rcParams['savefig.directory'] = tool_option_values['default_file_generation_directory']
        self.current_figure_toolbar = toolbar

        # Add option selection and buttons
        button_frame = tk.Frame(self.view_climate_data_frame, padx=0, pady=0)
        if parameter_data_is_gridded :
            self.series_plot_interval_text = tk.StringVar(value=self.series_plot_config[self.current_series_plot_option]['name'])
            series_plot_interval_selection = []
            for option in self.series_plot_options :
                series_plot_interval_selection.append(self.series_plot_config[option]['name'])
            series_plot_interval_menu = tk.OptionMenu(button_frame, self.series_plot_interval_text, *series_plot_interval_selection)
            select_series_plot_interval = self.view_climate_data_frame.register(self.selectSeriesPlotInterval)
            series_plot_interval_menu.config(highlightthickness=0, anchor=tk.W)
            for i, option in enumerate(self.series_plot_options) :
                series_plot_interval_menu['menu'].entryconfigure(i, command=(select_series_plot_interval, option))
            tk.Label(button_frame, text='Plot Interval:').grid(row=0, column=0, padx=0, pady=0)
            series_plot_interval_menu.grid(row=0, column=1, padx=0, pady=0)
        tk.Button(button_frame, text='Save', anchor=tk.CENTER, command=self.saveFigureViaToolbar).grid(row=0, column=2, padx=5, pady=0)
        tk.Button(button_frame, text='Close', anchor=tk.CENTER, command=self.closeFigureWindow).grid(row=0, column=3, padx=0, pady=0)
        button_frame.grid(row=1, column=0, padx=0, pady=5)

    # Step 7 Method: Select Series Plot Interval: the user selects an option
    def selectSeriesPlotInterval(self, selected) :
        #print 'TODO: selectSeriesPlotInterval', selected

        self.series_plot_interval_text.set(self.series_plot_config[selected]['name']) # needed as OptionMenu menu item commands have been overridden
        self.current_series_plot_option = selected

        # Update series plot
        
        # Remove current plot frame
        self.view_climate_data_frame.grid_remove()
        self.view_climate_data_figure.clear()

        # Create grid plots
        figure_width = self.view_climate_data_figure.get_figwidth()
        figure_height = self.view_climate_data_figure.get_figheight()
        self.ignore_series_plot_config_events = 6
        self.createSeriesPlot(self.series_plot_parameter_data, figure_width=figure_width, figure_height=figure_height)

    # Step 7 Method: Select data file type: the user selects an option
    def selectDataFileType(self, selected) :
        #print 'TODO: selectDataFileType', selected

        self.data_file_type_text.set(self.data_file_type_selection[self.data_file_type_keys.index(selected)]) # needed as OptionMenu menu item commands have been overridden

        # Reset generation
        self.resetGeneration()

    # Step 7 Method: Select Generation Directory
    def selectGenerationDirectory(self) :
        #print 'TODO: selectGenerationDirectory'

        # Place focus on select directory button
        self.generation_directory_button.focus_set()

        # Reset generation
        self.resetGeneration()

        # Get current config tool options
        tool_option_values = self.getToolOptions()

        # Use existing/last used generation directory if it exists otherwise use default directory
        if self.data_file_helper.getFileGenerationDirectoryPath() and path.exists(self.data_file_helper.getFileGenerationDirectoryPath()) :
            initial_directory = self.data_file_helper.getFileGenerationDirectoryPath()
        elif tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory']) :
            initial_directory = tool_option_values['default_file_generation_directory']
        elif MAC_VERSION and environ.has_key('HOME') and path.exists(environ['HOME']) :
            initial_directory = environ['HOME']
        elif environ.has_key('USERPROFILE') and path.exists(environ['USERPROFILE']) : # PC version
            initial_directory = environ['USERPROFILE']
        else :
            initial_directory = getcwd()

        # Open file selection dialog
        generation_directory_path = askdirectory(title='Select the directory to generate files', initialdir=initial_directory)

        if generation_directory_path : # Directory selected

            # Create directory if it doesn't already exist
            if not path.exists(generation_directory_path) :
                try :
                    generation_directory_path = self.data_file_helper.createDirectoryPath(generation_directory_path)
                except Exception, e :
                    directory_name = self.data_file_helper.splitPath(generation_directory_path)['name']
                    showerror('Directory Error', 'Error loading or creating directory \"'+directory_name+'\". Check file permissions.')
                    print >> sys.stderr, 'Error loading or creating directory:', e

            # Set path
            generation_directory_path = path.normpath(str(generation_directory_path))
            self.data_file_helper.setFileGenerationDirectory(generation_directory_path)
            location_descr = 'File generation in \"' + self.data_file_helper.getFileGenerationDirectoryName() + '\"'
            self.generation_directory_label_text.set(location_descr)

            # Set default when not already set via config options
            if not tool_option_values['default_file_generation_directory'] or not path.exists(tool_option_values['default_file_generation_directory']) or not tool_option_values['default_file_generation_directory_set'] :
                self.setToolOptions({ 'default_file_generation_directory' : generation_directory_path })

            # Enable the generate button
            self.generate_button.configure(state=tk.NORMAL)

        # Update workflow status
        self.updateStepsCompleted()

    # Step 7 Method: Generate Data Files
    def generateDataFiles(self) :
        #print 'TODO: generateDataFiles'

        # Place focus on generate button
        self.generate_button.focus_set()

        # Check that the details are complete
        if self.detailsIncomplete() :
            return True

        # Generate grids or series?
        generate_grids = (self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())] == 'map')

        # Check if the file generation directory is empty, if not then generate a time-stamped directory
        if not self.data_file_helper.fileFenerationDirectoryIsEmpty() :
            self.data_file_helper.generateTimestampedFileGenerationDirectory()

        # Disable generate button, add generation status bar, and change label text
        self.generate_button.configure(state=tk.DISABLED)
        self.update_idletasks()
        self.generation_status_bar['value'] = 0
        self.generation_status_bar['maximum'] = (self.current_interval_steps + 1) * self.current_valid_interval_size_value * len(self.selected_time_unit_month_indices)
        if generate_grids :
            self.generation_status_bar['maximum'] += (self.current_interval_steps + 1) * self.generation_status_times['files']['map']
            generation_status = self.generation_status_options['files']['map']['file']
        else :
            self.generation_status_bar['maximum'] += self.generation_status_times['files']['series']
            generation_status = self.generation_status_options['files']['series']['data']
        #print'generation_status_bar max:', self.generation_status_bar['maximum']
        self.generation_status_bar.grid()
        self.update_idletasks()
        self.generate_label_text.set(' '*50)
        self.update_idletasks()
        self.generate_label_text.set(generation_status)
        self.update_idletasks()

        # Resolve generation data file type
        data_file_type = self.data_file_type_keys[self.data_file_type_selection.index(self.data_file_type_text.get())]

        # Resolve selected parameter/group codes
        parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
        parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

        # Is the parameter data gridded?
        parameter_data_is_gridded = self.data_file_helper.parameterDataIsGridded(parameter_group_code, parameter_code)

        # Get period and interval values and convert to AD if required
        period_ad_from = int(self.period_text['from'].get())
        period_ad_until = int(self.period_text['until'].get())
        if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] : # BP
            period_ad_from = 1950 - period_ad_from
        if self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # BP
            period_ad_until = 1950 - period_ad_until

        # Get delta reference data when required
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
            delta_ref_period_ad = self.delta_reference_value[delta_reference_period_code]['year']
            if self.delta_reference_value[delta_reference_period_code]['postfix'] == self.period_postfix_keys[0] : # BP
                delta_ref_period_ad = 1950 - delta_ref_period_ad
            if generate_grids :
                if delta_reference_period_code is 'previous' or delta_ref_period_ad == period_ad_from :
                    period_ad_from += self.current_valid_interval_step_value
                elif delta_reference_period_code is 'next' or delta_ref_period_ad == period_ad_until :
                    period_ad_until -= self.current_valid_interval_step_value
        else :
            delta_ref_period_ad = None

        # Construct description (for netCDF files)
        description = ''
        if self.utilise_delta.get() :
            if self.delta_as_percent.get() :
                description += '% '
            description += 'Change in ' 
        if self.time_unit_text.get() == 'Month' :
            description += self.time_unit_months_text.get() + ' '
        elif self.time_unit_text.get() == 'Annual' :
            description += 'Annual '
        description += self.parameter_via_group_text[self.parameter_group_selection_map[self.parameter_group_text.get()]].get()
        if self.time_unit_text.get() == 'Season' :
            description += ' for Season ' + self.time_unit_seasons_text.get()
        elif self.time_unit_text.get() == 'User-defined' :
            description += ' for User-defined Months ' + self.time_unit_other_text.get()
        elif self.time_unit_text.get() == 'All Months' :
            description += ' for All Months'
        if self.utilise_delta.get() :
            delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
            description += ' Relative to ' + str(self.delta_reference_value[delta_reference_period_code]['year']) + ' ' + self.delta_reference_value[delta_reference_period_code]['postfix']

        # Data units
        if self.delta_as_percent.get() :
            data_units = '%'
        else :
            data_units = self.parameter_unit_string[parameter_group_code][parameter_code].replace(u'\u00B0', 'degrees ')

        # Generate files
        if generate_grids : # Generate one file at a time

            period_years_ad = range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value)
            generated_file_count = 0
            for year_ad in period_years_ad :

                # Collect grid data for year
                parameter_data = []
                try :
                    # Gather parameter data from the climate data files
                    parameter_data = self.data_file_helper.generateParameterData(parameter_group_code=parameter_group_code,
                                                                                 parameter_code=parameter_code,
                                                                                 period_ad_from=year_ad,
                                                                                 period_ad_until=year_ad,
                                                                                 delta_ref_period_ad=delta_ref_period_ad,
                                                                                 delta_as_percent=bool(self.delta_as_percent.get()),
                                                                                 interval_step=self.current_valid_interval_step_value,
                                                                                 interval_size=self.current_valid_interval_size_value,
                                                                                 month_indices=self.selected_time_unit_month_indices,
                                                                                 region_mask=self.region_mask,
                                                                                 generate_grids=generate_grids,
                                                                                 all_months=self.time_unit_is_all_months,
                                                                                 correct_bias=self.utilise_bias_correction.get())
                    self.parameter_data = parameter_data[0].copy()
                except Exception, e :
                    showerror('Data extraction error', str(e))
                    print >> sys.stderr, 'Data extraction error:', e

                # Generate the grid data file
                if parameter_data :

                    # Resolve year and postfix for data
                    if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # both BP
                        year = 1950 - year_ad
                        postfix = 'BP'
                    elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # both AD
                        year = year_ad
                        postfix = 'AD'
                    elif self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # from BP until AD
                        if year_ad <= 1950 :
                            year = 1950 - year_ad
                            postfix = 'BP'
                        else :
                            year = year_ad
                            postfix = 'AD'

                    # Apply region mask to grid
                    if self.region_is_time_dependent[self.current_region] :
                        region_mask_for_year = self.region_mask[self.data_file_helper.nearestTimeDependentRegionMaskYear(1950 - year_ad)]
                    else :
                        region_mask_for_year = self.region_mask
                    masked_parameter_data = np.ma.masked_array(parameter_data[0], mask=((region_mask_for_year - 1)*-1))

                    # Generate a grid data file
                    try :
                        self.data_file_helper.generateGridDataFile(masked_parameter_data, file_type=data_file_type, year_label=(str(year)+postfix), description=description, data_units=data_units)
                        generated_file_count += 1
                    except Exception, e :
                        showerror('File generation error', str(e))
                        print >> sys.stderr, 'File generation error:', e

            # Resolve generation status
            expected_when_error = ''
            if generated_file_count < len(period_years_ad) :
                expected_when_error = ' of the ' + str(len(period_years_ad)) + ' expected'
            generation_status = str(generated_file_count) + expected_when_error + ' grid data files generated in \"' + self.data_file_helper.getFileGenerationDirectoryName()+ '\"'
            if generated_file_count :
                self.updateToolGenerationLogEntry(grids_generated={ 'number' : generated_file_count, 'expected' : len(period_years_ad) })
                self.updateToolGenerationLogs()

        else : # Collect series data then generate file

            # Collect series data
            parameter_data = []
            try :
                # Gather parameter data from the climate data files
                parameter_data = self.data_file_helper.generateParameterData(parameter_group_code=parameter_group_code,
                                                                             parameter_code=parameter_code,
                                                                             period_ad_from=period_ad_from,
                                                                             period_ad_until=period_ad_until,
                                                                             delta_ref_period_ad=delta_ref_period_ad,
                                                                             delta_as_percent=bool(self.delta_as_percent.get()),
                                                                             interval_step=self.current_valid_interval_step_value,
                                                                             interval_size=self.current_valid_interval_size_value,
                                                                             month_indices=self.selected_time_unit_month_indices,
                                                                             region_mask=self.region_mask,
                                                                             generate_grids=generate_grids,
                                                                             all_months=self.time_unit_is_all_months,
                                                                             correct_bias=self.utilise_bias_correction.get())
                self.parameter_data = parameter_data
            except Exception, e :
                showerror('Data extraction error', str(e))
                print >> sys.stderr, 'Data extraction error:', e
                generation_status = 'Data extraction error'

            # Generate the data file
            if parameter_data :

                # Gather years for series data frame
                years = range(period_ad_from, period_ad_until+1, self.current_valid_interval_step_value)
                if self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[0] : # both BP
                    x_title = 'Year (BP)'
                    for i, year in enumerate(years) :
                        years[i] = 1950 - year
                elif self.period_postfix_text['from'].get() == self.period_postfix_keys[1] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # both AD
                    x_title = 'Year (AD)'
                elif self.period_postfix_text['from'].get() == self.period_postfix_keys[0] and self.period_postfix_text['until'].get() == self.period_postfix_keys[1] : # from BP until AD
                    x_title = 'Year'
                    for i, year in enumerate(years) :
                        if year <= 1950 :
                            years[i] = str(1950 - year) + 'BP'
                        else :
                            years[i] = str(year) + 'AD'

                if parameter_data_is_gridded : # Generate statistics

                    # Create data frames with the series data (for each month when required)
                    series_data_frames = []
                    if self.public_release :
                        statistic_fields_included = ['minimum', 'percentile_5th', 'percentile_50th', 'percentile_95th', 'maximum', 'area_mean']
                    else :
                        statistic_fields_included = self.grid_region_statistics_keys # ['minimum', 'percentile_5th', 'percentile_25th', 'percentile_50th', 'percentile_75th', 'percentile_95th', 'maximum', 'grid_mean', 'grid_stdev', 'area_mean', 'area_stdev']
                    if self.time_unit_is_all_months :
                        months = self.month_names
                    else :
                        months = ['']
                        parameter_data = [parameter_data]
                    for i, month in enumerate(months) :
                        indexes = [x_title]
                        data_dict = { x_title : years }
                        for statistic_field in statistic_fields_included :
                            indexes.append(self.grid_region_statistics_names[statistic_field])
                            data_dict[self.grid_region_statistics_names[statistic_field]] = parameter_data[i][statistic_field]
                        series_data_frames.append(pd.DataFrame(data_dict)[indexes])
                    self.series_data_frames = series_data_frames
                    
                    # Generate a series data file(s)
                    try :
                        for i, month in enumerate(months) :
                            if month :
                                month_description = description + ': ' + month
                            else :
                                month_description = description
                            self.data_file_helper.generateSeriesDataFile(data_frame=series_data_frames[i], file_type=data_file_type, month=month.lower(), description=month_description, data_units=data_units)
                        generation_status = 'Series data file' + 's'*(len(months) > 1) + ' generated in \"' + self.data_file_helper.getFileGenerationDirectoryName() + '\"'
                    except Exception, e :
                        showerror('File generation error', str(e))
                        print >> sys.stderr, 'File generation error:', e
                        generation_status = 'File generation error'

                else : # Generate raw data

                    # Create a data frame with the series data
                    if self.time_unit_is_all_months :
                        indexes = [x_title]
                        data_dict = { x_title : years }
                        for i, month in enumerate(self.month_names) :
                            indexes.append(month)
                            data_dict[month] = parameter_data[i]
                    else :
                        y_title = self.parameter_via_group_text[parameter_group_code].get()
                        if self.utilise_delta.get() :
                            if self.delta_as_percent.get() :
                                y_title = '% Change in ' + y_title
                            else :
                                y_title = 'Change in ' + y_title
                        indexes = [x_title, y_title]
                        data_dict = { x_title : years, y_title : parameter_data }
                    series_data_frame = pd.DataFrame(data_dict)[indexes]
                    self.series_data_frame = series_data_frame

                    # Generate a series data file
                    try :
                        self.data_file_helper.generateSeriesDataFile(data_frame=series_data_frame, file_type=data_file_type, description=description, data_units=data_units)
                        generation_status = 'Series data file generated in \"' + self.data_file_helper.getFileGenerationDirectoryName() + '\"'
                    except Exception, e :
                        showerror('File generation error', str(e))
                        print >> sys.stderr, 'File generation error:', e
                        generation_status = 'File generation error'

                # Generate log file entries
                try :
                    self.updateToolGenerationLogEntry(statistics_generated=parameter_data_is_gridded)
                    self.updateToolGenerationLogs()
                except Exception, e :
                    showerror('Log file generation error', str(e))
                    print >> sys.stderr, 'Log file generation error:', e
                    generation_status = 'Log file generation error'

        # Reset the file generation directory to its parent when a time-stamped directory was utilised
        if self.data_file_helper.fileGenerationDirectoryIsTimestamped() :
            self.data_file_helper.resetTimestampedFileGenerationDirectory()

        # Remove generation status bar, reinstate label text and re-enable button
        self.update_idletasks()
        self.generation_status_bar.grid_remove() # only when exception
        self.update_idletasks()
        self.generate_label_text.set('')
        self.update_idletasks()
        self.generate_label_text.set(generation_status)
        self.file_generation_completed = True
        self.generate_button.configure(state=tk.NORMAL)
    
    # Step 7 Method: Reset Generation
    def resetGeneration(self) :
        if self.file_generation_completed :
            data_type_key = self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())]
            self.generate_label_text.set(self.generation_options['files'][data_type_key])
            self.file_generation_completed = False

    # Step 7 Method: Update Tool Generation Log Entry
    def updateToolGenerationLogEntry(self, update_dict=None, figure=None, grids_generated=None, statistics_generated=False, statistics_table=None) :
        if figure :
            self.tool_generation_log_entry['figure'] = figure
            if self.tool_generation_log_entry['data_type'] == 'map' :
                self.tool_generation_log_entry['grids_generated'] = self.current_interval_steps + 1 - self.utilise_delta.get()
            elif self.tool_generation_log_entry['data_type'] == 'series' :
                self.tool_generation_log_entry['grids_generated'] = None
        else :
            # Collect entry details
            self.tool_generation_log_entry['data_type'] = self.data_type_keys[self.data_type_selection.index(self.data_type_text.get())]
            self.tool_generation_log_entry['data_action'] = self.data_action_keys[self.data_action_selection.index(self.data_action_text.get())]
            self.tool_generation_log_entry['parameter_group'] = self.parameter_group_text.get()
            self.tool_generation_log_entry['parameter'] = self.parameter_via_group_text[self.parameter_group_selection_map[self.parameter_group_text.get()]].get()
            self.tool_generation_log_entry['time_unit'] = self.time_unit_text.get()
            if self.time_unit_text.get() == 'Month' :
                self.tool_generation_log_entry['time_unit_value'] = self.time_unit_months_text.get()
            elif self.time_unit_text.get() == 'Season' :
                self.tool_generation_log_entry['time_unit_value'] = self.time_unit_seasons_text.get()
            else :
                self.tool_generation_log_entry['time_unit_value'] = self.time_unit_other_text.get()
            self.tool_generation_log_entry['region'] = self.region_selection_text.get()
            self.tool_generation_log_entry['period_from'] = { 'year' : int(self.period_text['from'].get()), 'postfix' : self.period_postfix_text['from'].get() }
            self.tool_generation_log_entry['period_until'] = { 'year' : int(self.period_text['until'].get()), 'postfix' : self.period_postfix_text['until'].get() }
            self.tool_generation_log_entry['interval_step'] = self.current_valid_interval_step_value
            self.tool_generation_log_entry['interval_size'] = self.current_valid_interval_size_value
            self.tool_generation_log_entry['bias_correction'] = bool(self.utilise_bias_correction.get())
            self.tool_generation_log_entry['utilise_delta'] = bool(self.utilise_delta.get())
            self.tool_generation_log_entry['delta_as_percent'] = bool(self.delta_as_percent.get())
            if self.tool_generation_log_entry['utilise_delta'] :
                delta_reference_period_code = self.delta_reference_period_codes[self.delta_reference_interval_selection.index(self.delta_reference_interval_text.get())]
                self.tool_generation_log_entry['delta_reference'] = self.delta_reference_value[delta_reference_period_code]
            else :
                self.tool_generation_log_entry['delta_reference'] = { 'year' : None, 'postfix' : None }
            self.tool_generation_log_entry['grids_generated'] = grids_generated
            self.tool_generation_log_entry['figure'] = None
            self.tool_generation_log_entry['existing'] = False
            self.tool_generation_log_entry['statistics_generated'] = statistics_generated
            self.tool_generation_log_entry['statistics_table'] = statistics_table

            # Overwrite some entries when required
            if update_dict :
                for key, value in update_dict.items() :
                    self.tool_generation_log_entry[key] = value

    # Step 7 Method: Update Tool Generation Logs
    def updateToolGenerationLogs(self) :
        #print 'TODO: updateToolGenerationLogs'

        tool_option_values = self.getToolOptions()

        # Collect log file locations
        logfiles = []
        if tool_option_values['default_file_generation_directory'] and path.exists(tool_option_values['default_file_generation_directory']) and tool_option_values['default_file_generation_directory_set'] :
            logfiles.append(path.join(tool_option_values['default_file_generation_directory'], self.tool_generation_log_file))

        # Log figure saves
        if self.tool_generation_log_entry['figure'] :
            logfile_in_figure_location = path.join(self.tool_generation_log_entry['figure']['directory'], self.tool_generation_log_file)
            if logfile_in_figure_location not in logfiles :
                logfiles.append(logfile_in_figure_location)
            try :
                if self.tool_generation_log_entry['existing'] :
                    self.data_file_helper.updateToolGenerationLogs(logfiles, self.createToolGenerationLogEntry(), log_entry_addition=self.createToolGenerationLogAdditionalPrintEntry())
                else :
                    self.data_file_helper.updateToolGenerationLogs(logfiles, self.createToolGenerationLogEntry())
                    self.tool_generation_log_entry['existing'] = True
            except Exception, e :
                showerror('Error writing to log files', str(e))
                print >> sys.stderr, 'Error writing to log files:', e

        # Log grid statistics table saves
        elif self.tool_generation_log_entry['statistics_table'] :
            logfile_in_table_location = path.join(self.tool_generation_log_entry['statistics_table']['directory'], self.tool_generation_log_file)
            if logfile_in_table_location not in logfiles :
                logfiles.append(logfile_in_table_location)
            try :
                self.data_file_helper.updateToolGenerationLogs(logfiles, self.createToolGenerationLogEntry())
            except Exception, e :
                showerror('Error writing to log files', str(e))
                print >> sys.stderr, 'Error writing to log files:', e

        # Log data file generations
        else :
            logfile_in_generation_location = path.join(self.data_file_helper.getFileGenerationDirectoryPath(), self.tool_generation_log_file)
            if logfile_in_generation_location not in logfiles :
                logfiles.append(logfile_in_generation_location)
            if self.data_file_helper.fileGenerationDirectoryIsTimestamped() :
                logfile_in_root_generation_location = path.join(self.data_file_helper.getFileGenerationDirectoryRoot(), self.tool_generation_log_file)
                if logfile_in_root_generation_location not in logfiles :
                    logfiles.append(logfile_in_root_generation_location)
            try :
                self.data_file_helper.updateToolGenerationLogs(logfiles, self.createToolGenerationLogEntry())
            except Exception, e :
                showerror('Error writing to log files', str(e))
                print >> sys.stderr, 'Error writing to log files:', e

    # Step 7 Method: Update Tool Generation Log Entry
    def createToolGenerationLogEntry(self) :

        # Timestamp line
        log_entry_string = self.data_file_helper.generateLogEntryTimestamp() + '\n'

        # Description line
        statistics_generated = self.tool_generation_log_entry['statistics_generated']
        multiple_files = (statistics_generated and self.time_unit_is_all_months)
        if self.tool_generation_log_entry['figure'] :
            if self.tool_generation_log_entry['data_type'] == 'map' :
                log_entry_string += '  Map Grid Plot Saved for '
            elif self.tool_generation_log_entry['data_type'] == 'series' :
                log_entry_string += '  Time Series Plot Saved for '
        elif self.tool_generation_log_entry['statistics_table'] :
            log_entry_string += '  Map Grid Plot Statistics Saved for '
        elif self.tool_generation_log_entry['data_action'] == 'files' :
            if self.tool_generation_log_entry['data_type'] == 'map' :
                log_entry_string += '  Grid Data Files Generated for '
            elif self.tool_generation_log_entry['data_type'] == 'series' :
                log_entry_string += '  Series Data File' + 's'*multiple_files + ' Generated for '
        if self.tool_generation_log_entry['utilise_delta'] :
            if self.tool_generation_log_entry['delta_as_percent'] :
                log_entry_string += '% '
            log_entry_string += 'Change in ' 
        if self.tool_generation_log_entry['time_unit'] == 'Month' :
            log_entry_string += self.tool_generation_log_entry['time_unit_value'] + ' '
        elif self.tool_generation_log_entry['time_unit'] == 'Annual' :
            log_entry_string += 'Annual '
        log_entry_string += self.tool_generation_log_entry['parameter']
        if self.tool_generation_log_entry['time_unit'] == 'Season' :
            log_entry_string += ' for Season ' + self.tool_generation_log_entry['time_unit_value']
        elif self.tool_generation_log_entry['time_unit'] == 'User-defined' :
            log_entry_string += ' for User-defined Months ' + self.tool_generation_log_entry['time_unit_value']
        elif self.tool_generation_log_entry['time_unit'] == 'All Months' :
            log_entry_string += ' for All Months'
        if self.tool_generation_log_entry['utilise_delta'] :
            log_entry_string += ' Relative to ' + str(self.tool_generation_log_entry['delta_reference']['year']) + ' ' + self.tool_generation_log_entry['delta_reference']['postfix']
        log_entry_string += '\n'

        # Other details lines
        log_entry_string += '  Region: ' + self.tool_generation_log_entry['region'] + '\n'
        log_entry_string += ( '  Period: ' + str(self.tool_generation_log_entry['period_from']['year']) + ' ' + self.tool_generation_log_entry['period_from']['postfix'] +
                              ' - ' + str(self.tool_generation_log_entry['period_until']['year']) + ' ' + self.tool_generation_log_entry['period_until']['postfix'] + '\n' ) 
        log_entry_string += ( '  Interval: ' + str(self.tool_generation_log_entry['interval_size']) + ' year intervals taken in ' +
                              str(self.tool_generation_log_entry['interval_step']) + ' year steps' + '\n' )
        log_entry_string += '  Bias Correction: '
        if self.tool_generation_log_entry['bias_correction'] :
            log_entry_string += 'On' + '\n'
        else :
            log_entry_string += 'Off' + '\n'

        # Files saved/generated line
        if self.tool_generation_log_entry['figure'] :
            if self.tool_generation_log_entry['data_type'] == 'map' :
                log_entry_string += '  Plot containing ' + str(self.tool_generation_log_entry['grids_generated']) + ' grid maps '
            elif self.tool_generation_log_entry['data_type'] == 'series' :
                log_entry_string += '  Time series plot '
                if statistics_generated :
                    log_entry_string += 'of Region ' + self.series_plot_config[self.current_series_plot_option]['name'].replace(u'\u00B1', '+/-') + ' '
            log_entry_string += 'saved as ' + self.tool_generation_log_entry['figure']['path']
        elif self.tool_generation_log_entry['statistics_table'] :
            log_entry_string += '  Grid plot statistics saved as ' + self.tool_generation_log_entry['statistics_table']['path']
        elif self.tool_generation_log_entry['data_action'] == 'files' : 
            if self.tool_generation_log_entry['data_type'] == 'map' :
                number_generated = self.tool_generation_log_entry['grids_generated']['number']
                number_expected = self.tool_generation_log_entry['grids_generated']['expected']
                if number_generated < number_expected :
                    log_entry_string += '  ' + str(number_generated) + ' of the expected ' + str(number_expected) + ' ' + self.data_file_type_text.get() + ' data files'
                else :
                    log_entry_string += '  ' + str(number_generated) + ' ' + self.data_file_type_text.get() + ' data files'
            elif self.tool_generation_log_entry['data_type'] == 'series' :
                log_entry_string += '  ' + self.data_file_type_text.get() + ' data file' + 's'*multiple_files
            log_entry_string += ' generated in ' + self.data_file_helper.getFileGenerationDirectoryPath()
        log_entry_string += '\n'

        self.log_entry_string = log_entry_string
        return log_entry_string

    # Step 7 Method: Update Tool Generation Log Additional Print Entry
    def createToolGenerationLogAdditionalPrintEntry(self) :
        if self.tool_generation_log_entry['data_type'] == 'map' :
            log_entry_string = '  Plot containing ' + str(self.tool_generation_log_entry['grids_generated']) + ' grid maps '
        elif self.tool_generation_log_entry['data_type'] == 'series' :
            log_entry_string = '  Time series plot '
            if self.tool_generation_log_entry['statistics_generated'] :
                log_entry_string += 'of Region ' + self.series_plot_config[self.current_series_plot_option]['name'].replace(u'\u00B1', '+/-') + ' '
        log_entry_string += 'saved as ' + self.tool_generation_log_entry['figure']['path']
        log_entry_string += '\n'
        return log_entry_string

    ## Shared Methods ################################################################################################################################################

    # Shared Method: Calculate Colour Scheme Boundaries (used in menu colour edit and grid plot methods)
    def calculateColourSchemeBoundaries(self) :

        # Find minimum and maximum data values and colour scheme interval
        if self.map_colour_scheme == '90%_range' :
            data_5th_percentile = min(self.grid_plot_statistics['region']['percentile_5th'])
            data_95th_percentile = max(self.grid_plot_statistics['region']['percentile_95th'])
            scheme_interval = (data_95th_percentile - data_5th_percentile)/9
            data_min = data_5th_percentile - scheme_interval
            data_max = data_95th_percentile + scheme_interval

        else : # fixed_range

            # Resolve selected parameter/group codes
            parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
            parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

            # Select fixed colour scheme via parameter codes and delta settings
            if self.utilise_delta.get() :
                if self.delta_as_percent.get() and self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code].has_key('%delta') :
                    fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['%delta']
                else :
                    fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['delta']
            else :
                fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['value']

            # Prioritise min/max then first/last boundaries, use statistical min/max when neither provided
            if fixed_range_colour_scheme['min'] != None :
                data_min = fixed_range_colour_scheme['min']
            elif fixed_range_colour_scheme['first_boundary'] != None :
                data_min = None
            else :
                data_min = min(self.grid_plot_statistics['region']['minimum'])
            if fixed_range_colour_scheme['max'] != None :
                data_max = fixed_range_colour_scheme['max']
            elif fixed_range_colour_scheme['last_boundary'] != None :
                data_max = None
            else :
                data_max = max(self.grid_plot_statistics['region']['maximum'])

            # Resolve scheme interval and unresolved min/max
            if data_min == None and data_max == None :
                scheme_interval = (fixed_range_colour_scheme['last_boundary'] - fixed_range_colour_scheme['first_boundary'])/9.0
                data_min = fixed_range_colour_scheme['first_boundary'] - scheme_interval
                data_max = fixed_range_colour_scheme['last_boundary'] + scheme_interval
            elif data_min == None :
                scheme_interval = (data_max - fixed_range_colour_scheme['first_boundary'])/10.0
                data_min = fixed_range_colour_scheme['first_boundary'] - scheme_interval
            elif data_max == None :
                scheme_interval = (fixed_range_colour_scheme['last_boundary'] - data_min)/10.0
                data_max = fixed_range_colour_scheme['last_boundary'] + scheme_interval
            else :
                scheme_interval = (data_max - data_min)/11.0

        # Return colour scheme boundary values
        return np.arange(data_min, data_max+0.1*scheme_interval, scheme_interval)

    # Shared Method: Adjust Colour Scheme Zero Boundaries (used in menu colour edit and grid plot methods)
    def adjustColourSchemeZeroBoundaries(self, colour_scheme_boundaries) :

        if self.map_colour_scheme == '90%_range' : # shift left method
            colour_scheme_boundaries_zero_index = (colour_scheme_boundaries >= 0).nonzero()[0][0]
            colour_scheme_boundaries -= colour_scheme_boundaries[colour_scheme_boundaries_zero_index]

        else : # fixed_range: minimal stretch method

            # Resolve selected parameter/group codes
            parameter_group_code = self.parameter_group_selection_map[self.parameter_group_text.get()]
            parameter_code = self.parameter_via_group_selection_map[parameter_group_code][self.parameter_via_group_text[parameter_group_code].get()]

            # Select fixed colour scheme via parameter codes and delta settings
            if self.utilise_delta.get() :
                if self.delta_as_percent.get() and self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code].has_key('%delta') :
                    fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['%delta']
                else :
                    fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['delta']
            else :
                fixed_range_colour_scheme = self.parameter_fixed_range_colour_scheme[parameter_group_code][parameter_code]['value']

            # Resolve colour scheme zero boundaries
            first_index = int(fixed_range_colour_scheme['first_boundary'] != None and fixed_range_colour_scheme['min'] == None)
            last_index = 11 - int(fixed_range_colour_scheme['last_boundary'] != None and fixed_range_colour_scheme['max'] == None)
            if colour_scheme_boundaries.round(12).min() >= 0 :
                data_min = 0.0
                scheme_interval = (colour_scheme_boundaries[last_index] - data_min)/last_index
                data_max = colour_scheme_boundaries[last_index] + scheme_interval*(11 - last_index)
                colour_scheme_boundaries_zero_index = 0
            elif colour_scheme_boundaries.round(12).max() <= 0 :
                data_max = 0.0
                scheme_interval = (data_max - colour_scheme_boundaries[first_index])/(11 - first_index)
                data_min = colour_scheme_boundaries[first_index] - scheme_interval*first_index
                colour_scheme_boundaries_zero_index = 11
            else :
                first_positive_index = (colour_scheme_boundaries >= 0).nonzero()[0][0]
                lower_stretch = None
                upper_stretch = None
                if first_positive_index < last_index :
                    lower_stretch = (last_index - first_index)*colour_scheme_boundaries[first_positive_index]/(last_index - first_positive_index)
                if first_positive_index > first_index + 1 :
                    upper_stretch = (last_index - first_index)*colour_scheme_boundaries[first_positive_index - 1]/(first_index - first_positive_index + 1)
                if upper_stretch == None or (lower_stretch != None and round(lower_stretch, 12) <= round(upper_stretch, 12)) :
                    colour_scheme_boundaries[first_index] -= lower_stretch
                    colour_scheme_boundaries_zero_index = first_positive_index
                else :
                    colour_scheme_boundaries[last_index] += upper_stretch
                    colour_scheme_boundaries_zero_index = first_positive_index - 1
                scheme_interval = (colour_scheme_boundaries[last_index] - colour_scheme_boundaries[first_index])/(last_index - first_index)
                data_min = colour_scheme_boundaries[first_index] - scheme_interval*first_index
                data_max = colour_scheme_boundaries[last_index] + scheme_interval*(11 - last_index)
            colour_scheme_boundaries = np.arange(data_min, data_max+0.1*scheme_interval, scheme_interval).round(12)

        return (colour_scheme_boundaries_zero_index, colour_scheme_boundaries)

    ## Generic Methods ####################################################################################################################################################

    # Generic Method: Ensures menu selection triggers entry field validation focusout events
    def shiftFocus(self, force_after=False, context=None) :
        if not(context) : # and self.validation_warning_pending == context) :
            self.focus_set()
        if force_after and self.validation_warning_pending :
            self.force_shift_focus = True
        
    # Copy dictionary mapping values (recursive)
    def copy_dict_mapping_values(self, dict_mapping) :
        mapping_copy = {}
        for key, item in dict_mapping.items() :
            if type(item) == dict :
                mapping_copy[key] = self.copy_dict_mapping_values(item)
            else :
                if 'get' in dir(item) :
                    mapping_copy[key] = item.get()
                else :
                    mapping_copy[key] = item
        return mapping_copy

    ## General Purpose Validation Methods ##################################################################################################################################

    # String is an integer?
    def isInteger(self, string_value) :
        try :
            integer_value = int(string_value)
            return True
        except Exception, e :
            return False

    # String is a positive integer?
    def isPositiveInteger(self, string_value) :
        if string_value.count(' ') or string_value.count('-') : # don't accept a space or a -
            return False
        try :
            integer_value = int(string_value)
            return integer_value > 0
        except Exception, e :
            return False

    # String is a non-negative integer?
    def isNonNegativeInteger(self, string_value) :
        if string_value.count(' ') or string_value.count('-') : # don't accept a space or a -
            return False
        try :
            integer_value = int(string_value)
            return integer_value >= 0
        except Exception, e :
            return False

    # String is a non-negative float?
    def isNonNegativetiveFloat(self, string_value) :
        try :
            float_value = float(string_value)
            return float_value >= 0
        except Exception, e :
            return False

#####################################################################################################################################################################################################################
#####################################################################################################################################################################################################################
#####################################################################################################################################################################################################################
#####################################################################################################################################################################################################################


    # Workflow Methods : Ensures user has completed steps before enabling downscaling generation

    # Update workflow progress
    def updateStepsCompleted(self) :
        True

    def dummy(self) :
        # Update completed status
        self.process_step['data_type']['completed'] = self.dataTypeCompleted()
        self.process_step['parameter_selection']['completed'] = self.parameterSelectionCompleted()
        self.process_step['generation']['completed'] = self.generationCompleted()

##        # Update parameter selection enable/disable
##        if not(self.dependentStepsToBeCompleted('parameter_selection')) :
##            self.baseline_year_entry.configure(state=)
##            self.projections_from_year_menu.configure(state=tk.NORMAL)
##            self.projections_until_year_menu.configure(state=tk.NORMAL)
##            self.data_mode_menu.configure(state=tk.NORMAL)
##            self.downscale_alignment_method_menu.configure(state=tk.NORMAL)
##        else :
##            self.baseline_year_entry.configure(state=tk.DISABLED)
##            self.projections_from_year_menu.configure(state=tk.DISABLED)
##            self.projections_until_year_menu.configure(state=tk.DISABLED)
##            self.data_mode_menu.configure(state=tk.DISABLED)
##            self.downscale_alignment_method_menu.configure(state=tk.DISABLED)
##
##        # Update file generation status
##        steps_to_be_completed = self.dependentStepsToBeCompleted('generation')
##        if steps_to_be_completed :
##            self.generation_directory_button.configure(state=tk.DISABLED)
##            self.generate_button.configure(state=tk.DISABLED)
##            if len(steps_to_be_completed) > 1 :
##                self.generate_label_text.set('Complete steps ' + string.join(steps_to_be_completed, ', '))
##            else :
##                self.generate_label_text.set('Complete step ' + str(steps_to_be_completed.pop()))
##        elif self.process_step['generation']['completed'] :
##            self.generate_label_text.set(str(self.generated_file_count) + ' downscaled R files generated in \"' + self.downscale_helper.getRDirName()+'\"')
##            self.r_file_generate_complete = False # Ready for next generation
##        elif self.r_file_generate_error :
##            self.generate_label_text.set('Error generating files')
##            self.r_file_generate_error = False # Ready to try again
##        else :
##            if self.generate_directory_ok :
##                self.generation_directory_button.configure(state=tk.NORMAL)
##                self.generate_button.configure(state=tk.NORMAL)
##                self.generate_label_text.set('Ready to generate downscaled R files')
##            else :
##                self.generation_directory_button.configure(state=tk.NORMAL)
##                self.generate_button.configure(state=tk.DISABLED)
##                self.generate_label_text.set('Complete this step')

    # Workflow: Data Type step is complete when ...
    def dataTypeCompleted(self) :
        return True

    # Workflow: Parameter selection step is complete when ...
    def parameterSelectionCompleted(self) :

        conditions_satisfied = 0
        total_conditions = 7

##        baseline_year = None
##        projections_from_year = None
##        projections_until_year = None
##
##        # Condition 1: Baseline year has value
##        if self.baseline_year_text.get() :
##            baseline_year = int(self.baseline_year_text.get())
##            conditions_satisfied += 1
##        
##        # Condition 2: Baseline year matches one obtained from Q file
##        if baseline_year and baseline_year == self.downscale_helper.getQBaselineYear() :
##            baseline_year = int(self.baseline_year_text.get())
##            conditions_satisfied += 1
##
##        # Condition 3: Projections from year has value
##        if self.projections_from_year_text.get() :
##            projections_from_year = int(self.projections_from_year_text.get())
##            conditions_satisfied += 1
##
##        # Condition 4: Projections until year has value
##        if self.projections_until_year_text.get() :
##            projections_until_year = int(self.projections_until_year_text.get())
##            conditions_satisfied += 1
##
##        # Condition 5: Projections from year <= until year
##        if projections_from_year <= projections_until_year :
##            conditions_satisfied += 1
##
##        # Condition 6: Data mode has value
##        if self.data_mode_text.get() :
##            conditions_satisfied += 1
##
##        # Condition 7: Downscale alignment method has value
##        if self.downscale_alignment_method_text.get() :
##            conditions_satisfied += 1
##
##        return conditions_satisfied == total_conditions

    # Workflow: Downscale generation step is complete when indicated via flag
    def generationCompleted(self) :
        return False #self.r_file_generate_complete

    # General workflow method: Determine what steps still need to be completed
    def dependentStepsToBeCompleted(self, step, process_step=None) :
        if not process_step :
            process_step = self.process_step
        step_numbers = []
        for dependent in process_step[step]['dependents'] :
            if not process_step[dependent]['completed'] :
                step_numbers.append(process_step[dependent]['number'])
        return step_numbers

    # Validation Methods: Ensure correct user inputs
        
    # Event handlers

    # Key releases on entry fields update the workflow steps completed
    def __keyReleaseOnEntryField(self, event) :
        self.updateStepsCompleted()

# END ApplicationGUI

## Main program

application_name = 'PaleoView v0.2'

# Set user application data directory
if MAC_VERSION :
    if environ.has_key('HOME') :       
        user_app_data_root = environ['HOME']
        if path.exists(path.join(user_app_data_root,'Library','Application Support')) :
            user_app_data_root = path.join(user_app_data_root,'Library','Application Support')
else : # PC version
    if environ.has_key('APPDATA') :
        user_app_data_root = environ['APPDATA']
    elif environ.has_key('USERPROFILE') :
        user_app_data_root = environ['USERPROFILE']
user_application_data_directory = path.join(user_app_data_root , application_name)
if not path.exists(user_application_data_directory) :
    try :
        mkdir(user_application_data_directory)
    except Exception, e :
        showerror('Directory Error', 'Cannot create application directory '+user_application_data_directory+'. Check file permissions.')
        print >> sys.stderr, 'Error creating user application directory', user_application_data_directory, ':', e
        user_application_data_directory = user_app_data_root

# Log files
if not DEBUG : # Re-direct stdout and stderr to log file
    log_file = path.join(user_application_data_directory , 'paleo_view_error_log.txt')
    if path.exists(log_file) :
        sys.stdout = open(log_file, 'a')
        sys.stderr = open(log_file, 'a')
    else :
        sys.stdout = open(log_file, 'w')
        sys.stderr = open(log_file, 'w')

root = tk.Tk()
app = ApplicationGUI(user_application_data_directory, master=root)
app.master.title(application_name)
app.mainloop()

if not DEBUG : # close log files
    sys.stdout.close()
    sys.stderr.close()

if root.children :
    root.destroy() # required for menu quit
else :
    0 # Window close already destroyed object

# END Main program
