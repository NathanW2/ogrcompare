# -*- coding: utf-8 -*-

# from __future__ import print_function

import argparse
import sys
import itertools
from osgeo import ogr
import os

from terminaltables import SingleTable, AsciiTable, GithubFlavoredMarkdownTable
from colorclass import Color, Windows

HTMLREPORT = """
<!DOCTYPE html>
<html>
<head lang="en">
    <meta charset="UTF-8">
    <title>OGR Dataset Compare</title>
</head>
<body>
<style>
table, td {
    border-collapse: collapse;
   border: 0.5px solid black;
}
</style>
    <h1>OGR Dataset Compare</h1>
    <div>
        Comparing: <b>{{source1}}</b>
        <br>
        Comparing: <b>{{source2}}</b>
    </div>
    <div>
        <h2>Fields</h2>
        <table>
            {% for data in fields %}
            <TR>
               <TD class="c1">{{data[0]}}</TD>
               <TD class="c2">{{data[1]}}</TD>
               <TD class="c3">{{data[2]}}</TD>
            </TR>
            {% endfor %}
        </table>
    <div>
    <div>
        <h2>Featurs</h2>
            {% for feature in features %}
                <table>
                {% for data in feature[2] %}
                    <TR>
                       <TD class="c1">{{data[0]}}</TD>
                       <TD class="c2">{{data[1]}}</TD>
                       <TD class="c3">{{data[2]}}</TD>
                       <TD class="c3">{{data[3]}}</TD>
                    </TR>
                {% endfor %}
                </table>
                <br>
            {% endfor %}
    <div>
</body>
</html>
"""

## HTML outpuut has color set to noop
Color = None

NODATA = "---"
#
# def eprint(*args, **kwargs):
#     print(*args, file=sys.stderr, **kwargs)

class Results:
    def __init__(self, source1, source2):
        self.fields = []
        self.featurecounts = []
        self.countsdiff = False
        self.featurecompare = []
        self.fieldsdiffer = False
        self.source1 = source1
        self.source2 = source2
        self.TableType = SingleTable

    def dump_console(self):
        print "Comparing:"
        print u"Layer 1 - {}".format(self.source1)
        print u"Layer 2 - {}".format(self.source2)
        print
        if self.featurecounts:
            table = self.TableType(self.featurecounts, title="Feature Counts")
            print table.table
            print

        if self.fields:
            print "Fields Differ: {0}".format("Yes" if self.fieldsdiffer else "No")
            table = self.TableType(self.fields, title="Fields")
            table.justify_columns[1] = "center"
            table.inner_heading_row_border = False
            print table.table
            print

        if self.featurecompare:
            print "Data Compare"
            if self.countsdiff:
                print "Feature counts diff. Value compare is cut off at shortest layer."
            for comparedata in self.featurecompare:
                name1, name2, data = comparedata[0], comparedata[1], comparedata[2]
                if not data:
                    continue
                table = self.TableType(data, title="{} vs {}".format(name1, name2))
                table.inner_heading_row_border = False
                table.justify_columns[1] = "center"
                print table.table

    def dump_html(self):
        from jinja2 import Template
        template = Template(HTMLREPORT)
        data = {
            "source1": self.source1,
            "source2": self.source2,
            "fields": self.fields,
            "features": self.featurecompare
        }
        print template.render(**data)

def compare(source1, source2, args=None):
    if not args:
        args = []

    global results
    results = Results(source1, source2)
    if args.ascii:
        results.TableType = AsciiTable

    source1 = ogr.Open(source1)
    source2 = ogr.Open(source2)
    layer1 = source1.GetLayer()
    layer2 = source2.GetLayer()

    compare_fields(layer1, layer2)
    if not args.schema_only:
        compare_feature_counts(layer1, layer2)
        compare_features(layer1,
                         layer2,
                         compare_common_fields=args.matched_fields_only,
                         ignore_equal=not args.report_all)

    Windows.enable()
    if args.html:
        results.dump_html()
    else:
        results.dump_console()

def compare_features(layer1,
                     layer2,
                     compare_common_fields=True,
                     ignore_equal=True
                     ):
    fields1 = _getfields(layer1, names_only=True)
    fields2 = _getfields(layer2, names_only=True)
    iter1 = iter(layer1)
    iter2 = iter(layer2)
    if compare_common_fields:
        rowtitles = list(set(fields1) & set(fields2))
    else:
        rowtitles = list(set(fields1 + fields2))

    fieldsfordata = list(rowtitles)
    rowtitles.insert(0, "Fields")
    rowtitles.append("GEOMETRY")
    count = 0
    for f1 in iter1:
        rowheaders = list(rowtitles)
        values1 = []
        values2 = []
        try:
            f2 = iter2.next()
        except StopIteration:
            break

        for field in fieldsfordata:
            try:
                value1 = f1.GetField(field)
            except ValueError:
                value1 = NODATA
            try:
                value2 = f2.GetField(field)
            except ValueError:
                value2 = NODATA

            if value1 == value2 and ignore_equal:
                index = rowheaders.index(field)
                del rowheaders[index]
                continue

            values1.append(value1)
            values2.append(value2)

        geom1 = f1.GetGeometryRef()
        geom2 = f2.GetGeometryRef()
        if geom1 == geom2 and ignore_equal:
            index = rowheaders.index("GEOMETRY")
            del rowheaders[index]
            continue

        values1.append(geom1)
        values2.append(geom2)

        datatable =  _gen_compare_table(values1, values2,
                                        rowtitles=rowheaders)
        results.featurecompare.append([f1.GetFID(), f2.GetFID(), datatable])

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
    # comparetable.append(header)
    for count, items  in enumerate(itertools.izip_longest(list1, list2, fillvalue="--"), start=1):
        item1, item2 = items[0], items[1]
        if isinstance(item1, ogr.Geometry) and isinstance(item2, ogr.Geometry):
            geom1, geom2 = item1, item2
            item1, item2 = geom1.ExportToWkt(), geom2.ExportToWkt()
            display1, display2 = item1[:30], item2[:30]
        else:
            display1, display2 = item1, item2

        op = "="
        if item1 != item2:
            op = Color(r'{autored}!={/autored}')
        elif item1 == item2:
            op = Color(r'{autogreen}={/autogreen}')

        data = [display1, op, display2]
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
    results.countsdiff = featureCount2 != featureCount1

def compare_fields(layer1, layer2):
    fields1 =  _getfields(layer1)
    fields2 =  _getfields(layer2)
    samefields = set(fields1) & set(fields2)
    difffields = set(fields1) ^ set(fields2)
    if difffields:
        results.fieldsdiffer = True

    results.fields = _gen_compare_table(fields1, fields2)


if __name__ == "__main__":
    Windows.enable()
    parser = argparse.ArgumentParser(description='Compare two OGR datasets')
    parser.add_argument('--matched-fields-only', action='store_true', help="Only show matching fields when comparing data.")
    parser.add_argument('--report-all', action='store_true', help="Include all fields even if equal")
    parser.add_argument('--schema-only', action='store_true', help="Only compare schemas.")
    parser.add_argument('--ascii', action='store_true', help="Generate the report tables in ascii mode. Use this if you want to pipe stdout")
    parser.add_argument('--html', action='store_true', help="Create a HTML report")
    parser.add_argument('Source1', help='OGR supported format')
    parser.add_argument('Source2', help='OGR supported format')

    args = parser.parse_args()
    compare(args.Source1, args.Source2, args)
