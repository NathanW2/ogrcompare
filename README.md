# OGR Compare

Compare OGR datasets on the command line.

Reports difference in schema, data, feature count, etc

## Usage

`python ogrcompare.py "test3.shp" "test4.shp"`

**HTML Export**

`python ogrcompare.py "test3.shp" test4.shp" --html > report.html`

```
usage: ogrcompare.py [-h] [--matched-fields-only] [--report-all]
                     [--schema-only] [--ascii] [--html]
                     [--color_match CSSCOLOR] [--color_nomatch CSSCOLOR]
                     Source1 Source2

Compare two OGR datasets

positional arguments:
  Source1               OGR supported format
  Source2               OGR supported format

optional arguments:
  -h, --help            show this help message and exit
  --matched-fields-only
                        Only show matching fields when comparing data.
  --report-all          Include all fields even if equal
  --schema-only         Only compare schemas.
  --ascii               Generate the report tables in ascii mode. Use this if
                        you want to pipe stdout
  --html                Create a HTML report
  --color_match         Background color for matching values (default #dff5e1)
  --color_nomatch       Background color for differing values (default #f5e5df)
```


## Requirements

- Python
- OGR
- `pip install terminaltables` (for non-HTML reports)
- `pip install colorclass` (for non-HTML reports)
