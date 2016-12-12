# OGR Compare

Compare OGR dataset on the command line.

Reports differeence in schema, data, feature count, etc

## Usage

`python ogrcompare.py "test3.shp" "test4.shp"`

**HTML Export**

`python ogrcompare.py "test3.shp" test4.shp" --html > report.html`

```
usage: ogrcompare.py [-h] [--matched-fields-only] [--report-all]
                     [--schema-only] [--ascii] [--html]
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
```


## Requirements

- Python
- OGR
- `pip install terminaltables`
- `pip install colorclass`

