from distutils.core import setup
from glob import glob
import matplotlib
import statsmodels.api
import sys
import py2exe

# >python setup_pc.py py2exe

sys.path.append("C:\Users\shaythorne\Dropbox\GlobalEcology\PythonResources\Microsoft.VC90.CRT")

data_files = matplotlib.get_py2exe_datafiles()
#data_files.append(("Microsoft.VC90.CRT", glob(r'C:\Users\shaythorne\Dropbox\GlobalEcology\PythonResources\Microsoft.VC90.CRT\*.*')))
data_files.append((r'mpl-data\basemap-data', glob(r'C:\Python27\Lib\site-packages\mpl_toolkits\basemap\data\*')))
data_files.append((r'docx-data\templates', glob(r'C:\Python27\Lib\site-packages\docx\templates\*')))
#data_files.append((r'Map Data', glob(r'C:\afat32\Dropbox\GlobalEcologyGroup\ProjectCode\PaleoclimateTool\v0.1\Map Data\*')))
setup(
    data_files=data_files,
    windows=['paleo_view_v0_4.py'],
)
#    options={'py2exe': { 'includes': 'patsy' }}
#    options={'py2exe': { 'excludes': ['_gtkagg', '_qt4agg', '_agg2', '_cairo', '_cocoaagg', '_fltkagg', '_gtk', '_gtkcairo'] }}
