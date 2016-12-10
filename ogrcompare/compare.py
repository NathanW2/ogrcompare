# -*- coding: utf-8 -*-

import sys
import itertools
from osgeo import ogr
import os

from terminaltables import SingleTable, AsciiTable
from colorclass import Color, Windows

NODATA = "---"

class Results:
    def __init__(self, source1, source2):
        self.fields = []
        self.featurecounts = []
        self.featurecompare = []
        self.fieldsdiffer = False
        self.source1 = source1
        self.source2 = source2

    def dump_console(self):
        print "Comparing:"
        print u"Layer 1 - {}".format(self.source1)
        print u"Layer 2 - {}".format(self.source2)
        print
        table = AsciiTable(self. featurecounts, title="Feature Counts")
        print table.table
        print
        print "Fields Differ: {0}".format("Yes" if self.fieldsdiffer else "No")
        print
        table = AsciiTable(self.fields, title="Fields")
        table.justify_columns[1] = "center"
        print table.table
        print
        table = AsciiTable(self.featurecompare, title="Value Compare")
        table.justify_columns[1] = "center"
        print table.table

def compare(source1, source2, args=None):
    if not args:
        args = []

    global results
    results = Results(source1, source2)

    source1 = ogr.Open(source1)
    source2 = ogr.Open(source2)
    layer1 = source1.GetLayer()
    layer2 = source2.GetLayer()

    compare_layers(layer1, layer2)
    compare_feature_counts(layer1, layer2)

    compare_same_fields = "--matched-fields-only" in args
    print  args
    print compare_same_fields
    compare_features(layer1, layer2, compare_common_fields=compare_same_fields)

    Windows.enable()
    results.dump_console()

def compare_features(layer1, layer2, compare_common_fields=True):
    fields1 = _getfields(layer1, names_only=True)
    fields2 = _getfields(layer2, names_only=True)
    iter1 = iter(layer1)
    iter2 = iter(layer2)
    f1 = iter1.next()
    f2 = iter2.next()
    if compare_common_fields:
        rowtitles = list(set(fields1) & set(fields2))
    else:
        rowtitles = list(set(fields1 + fields2))

    rowtitles.insert(0, "Fields")
    values1 = []
    values2 = []
    for field in rowtitles[1:]:
        try:
            value1 = f1.GetField(field)
        except ValueError:
            value1 = NODATA
        try:
            value2 = f2.GetField(field)
        except ValueError:
            value2 = NODATA
        values1.append(value1)
        values2.append(value2)
    results.featurecompare = _gen_compare_table(values1, values2, rowtitles=rowtitles)

def _getfields(layer, names_only=False, keep_order=False):
    layerDefinition = layer.GetLayerDefn()
    fields = []
    for i in range(layerDefinition.GetFieldCount()):
        fielddef = layerDefinition.GetFieldDefn(i)

        fieldName = fielddef.name
        if not names_only:
            fieldTypeCode = fielddef.type
            fieldType = fielddef.GetFieldTypeName(fieldTypeCode)
            fieldWidth = fielddef.width
            fieldPrecision = fielddef.precision
            formatted = "{} ({} ({} {})".format(fieldName, fieldType, fieldWidth, fieldPrecision)
            fields.append(formatted)
        else:
            fields.append(fieldName)

    if keep_order:
        return fields
    else:
        return sorted(fields)

def _gen_compare_table(list1, list2, rowtitles=None):
    header = ['Layer 1', "", 'Layer 2']
    if rowtitles:
        header.insert(0, rowtitles[0])

    comparetable = []
    comparetable.append(header)
    for count, items  in enumerate(itertools.izip_longest(list1, list2, fillvalue="--"), start=1):
        item1, item2 = items[0], items[1]
        op = "="
        if item1 != item2:
            op = Color(r'{autored}!={/autored}')
        elif item1 == item2:
            op = Color(r'{autogreen}={/autogreen}')
        data = [item1, op, item2]
        if rowtitles:
            try:
                data.insert(0, rowtitles[count])
            except IndexError:
                data.insert(0, "")

        comparetable.append(data)
    return comparetable

def compare_feature_counts(layer1, layer2):
    featureCount1 = layer1.GetFeatureCount()
    featureCount2 = layer2.GetFeatureCount()
    results.featurecounts = _gen_compare_table([featureCount1], [featureCount2])

def compare_layers(layer1, layer2):
    fields1 =  _getfields(layer1)
    fields2 =  _getfields(layer2)
    samefields = set(fields1) & set(fields2)
    difffields = set(fields1) ^ set(fields2)
    if difffields:
        results.fieldsdiffer = True

    results.fields = _gen_compare_table(fields1, fields2)



if __name__ == "__main__":
    Windows.enable()
    source = r"F:\gis_data\test3.shp"
    source2 = r"F:\gis_data\testfiles.shp"
    compare(source, source2)
    results.dump_console()
