import sys
from compare import compare
from colorclass import Color, Windows

source = r"F:\gis_data\test3.shp"
source2 = r"F:\gis_data\testfiles.shp"
source2 = r"F:\gis_data\QGIS_Training\AssetSnapshot\Drainage\SW_Structures.TAB"

print
print "---------------------"
print
args = sys.argv[1:]
compare(source, source2, args)
print
print "---------------------"
print
compare(source, source)
