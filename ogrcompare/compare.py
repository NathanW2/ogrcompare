# -*- coding: utf-8 -*-

import sys
import itertools
from osgeo import ogr
import os

from terminaltables import SingleTable, AsciiTable
from colorclass import Color, Windows

class Results:
    def __init__(self, source1, source2):
        self.fields = []
        self.fieldsdiffer = False
        self.source1 = source1
        self.source2 = source2

    def dump_console(self):
        print "Comparing:"
        print u" - {}".format(self.source1)
        print u" - {}".format(self.source2)
        print
        print "Fields Differ: {0}".format("Yes" if self.fieldsdiffer else "No")
        print
        table = AsciiTable(self.fields, title="Fields")
        table.justify_columns[1] = "center"
        print table.table

def compare(source1, source2):
    global results
    results = Results(source1, source2)

    source1 = ogr.Open(source1)
    source2 = ogr.Open(source2)
    layer1 = source1.GetLayer()
    layer2 = source2.GetLayer()
    compare_layers(layer1, layer2)

    Windows.enable()
    results.dump_console()

def _getfields(layer):
    layerDefinition = layer.GetLayerDefn()
    fields = []
    for i in range(layerDefinition.GetFieldCount()):
        fields.append(layerDefinition.GetFieldDefn(i).GetName())
    return sorted(fields)

def compare_layers(layer1, layer2):
    fields1 =  _getfields(layer1)
    fields2 =  _getfields(layer2)
    samefields = set(fields1) & set(fields2)
    difffields = set(fields1) ^ set(fields2)
    if difffields:
        results.fieldsdiffer = True

    header = ['Layer 1', "", 'Layer 2']
    results.fields.append(header)
    for item1, item2  in itertools.izip_longest(fields1, fields2, fillvalue="--"):
        op = "="
        if item1 != item2:
            op = Color(r'{autored}!={/autored}')
        elif item1 == item2:
            op = Color(r'{autogreen}={/autogreen}')
        results.fields.append([item1, op, item2])



if __name__ == "__main__":
    Windows.enable()
    source = r"F:\gis_data\test3.shp"
    source2 = r"F:\gis_data\testfiles.shp"
    compare(source, source2)
    results.dump_console()
