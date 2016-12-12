# -*- coding: utf-8 -*-

# from __future__ import print_function

import argparse
import sys
import itertools
from osgeo import ogr
import os

HTMLREPORT = """
<!DOCTYPE html>
<html>
<head lang="en">
    <meta charset="UTF-8">
    <title>OGR Dataset Compare</title>
</head>
<body>
<style>
body {
    font-family: sans-serif;
}
table {
    margin-bottom: 1em;
}
table, th, td {
    border-collapse: collapse;
    border: 0.5px solid #ddd;
    padding: 0.25em;
}
th {
    text-align: left;
}
.match {
    background-color: {{color_match}};
}
.nomatch {
    background-color: {{color_nomatch}};
}
</style>
    <h1>OGR Dataset Compare</h1>
    <div>
        <table>
            <tr>
                <th>Source 1: </th>
                <td>{{source1}}</td>
            </tr>
            <tr>
                <th>Source 2:</th>
                <td>{{source2}}</td>
            </tr>
        </table>
    </div>
    <div>
        <h2>Fields</h2>
        <table>
            <tr>
                <th>{{source1}}</th>
                <th></th>
                <th>{{source2}}</th>
            </tr>
            {% for data in fields %}
            {% if data[1] == "=" %}
                {% set matched = 'match' %}
            {% else %}
                {% set matched = 'nomatch' %}
            {% endif %}
            <tr>
               <td class="c1 {{matched}}">{{data[0]}}</td>
               <td class="c2 {{matched}}">{{data[1]}}</td>
               <td class="c3 {{matched}}">{{data[2]}}</td>
            </td>
            {% endfor %}
        </table>
    </div>
    <div>
        <h2>Features</h2>
        {% for feature in features %}
        <table>
            <tr>
                <th></th>
                <th>{{source1}}</th>
                <th></th>
                <th>{{source2}}</th>
            </tr>
            {% for data in feature[2] %}
            {% if data[2] == "=" %}
                {% set matched = 'match' %}
            {% else %}
                {% set matched = 'nomatch' %}
            {% endif %}
            <tr>
                <th class="c1">{{data[0]}}</th>
                <td class="c2 {{matched}}">{{data[1]}}</td>
                <td class="c3 {{matched}}">{{data[2]}}</td>
                <td class="c3 {{matched}}">{{data[3]}}</td>
            </tr>
            {% endfor %}
        </table>
        {% endfor %}
    </div>
</body>
</html>
"""

NODATA = "---"

## HTML outpuut has color set to noop
Color = None
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
        self.mode = "Clean"

    def dump_console(self):
        if self.mode == "Clean":
            TableType = SingleTable
        else:
            TableType = AsciiTable
        print "Comparing:"
        print u"Layer 1 - {}".format(self.source1)
        print u"Layer 2 - {}".format(self.source2)
        print
        if self.featurecounts:
            table = TableType(self.featurecounts, title="Feature Counts")
            print table.table
            print

        if self.fields:
            print "Fields Differ: {0}".format("Yes" if self.fieldsdiffer else "No")
            table = TableType(self.fields, title="Fields")
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
                table = TableType(data, title="{} vs {}".format(name1, name2))
                table.inner_heading_row_border = False
                table.justify_columns[1] = "center"
                print table.table

    def dump_html(self, color_match, color_nomatch):
        from jinja2 import Template
        template = Template(HTMLREPORT, trim_blocks=True, keep_trailing_newline=False, lstrip_blocks=True)
        data = {
            "source1": self.source1,
            "source2": self.source2,
            "fields": self.fields,
            "features": self.featurecompare,
            "color_match": color_match,
            "color_nomatch": color_nomatch
        }
        print template.render(**data)

def compare(source1, source2, args=None):
    if not args:
        args = []

    global results
    results = Results(source1, source2)
    if args.ascii:
        results.mode = "ascii"

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

    if args.html:
        results.dump_html(args.color_match, args.color_nomatch)
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
            if Color:
                op = Color(r'{autored}!={/autored}')
            else:
                op = "!="
        elif item1 == item2:
            if Color:
                op = Color(r'{autogreen}={/autogreen}')
            else:
                op = "="

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
    parser = argparse.ArgumentParser(description='Compare two OGR datasets')
    parser.add_argument('--matched-fields-only', action='store_true', help="Only show matching fields when comparing data.")
    parser.add_argument('--report-all', action='store_true', help="Include all fields even if equal")
    parser.add_argument('--schema-only', action='store_true', help="Only compare schemas.")
    parser.add_argument('--ascii', action='store_true', help="Generate the report tables in ascii mode. Use this if you want to pipe stdout")
    parser.add_argument('--html', action='store_true', help="Create a HTML report")
    parser.add_argument('--color_match', nargs='?', default='#dff5e1', help="Background color for matching values")
    parser.add_argument('--color_nomatch', nargs='?', default='#f5e5df', help="Background color for differing values")
    parser.add_argument('Source1', help='OGR supported format')
    parser.add_argument('Source2', help='OGR supported format')

    args = parser.parse_args()
    if not args.html:
        from terminaltables import SingleTable, AsciiTable
        from colorclass import Color, Windows
        Windows.enable()
    compare(args.Source1, args.Source2, args)
