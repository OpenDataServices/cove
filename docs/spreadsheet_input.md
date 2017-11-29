# Spreadsheet and CSV input.

Cove allows XLSX and CSV import in all the standards it supports.  It uses the [flattentool](http://flatten-tool.readthedocs.io) library to do the conversion from these formats to either XML or JSON.  Please look at flattentool documentation for detailed information on how to create spreadsheet templates for the particular standard.

## Metatab

Cove configures flattentool to allow an extra sheet in your spreadsheets (not for CSV) named "Meta" (case sensative). This sheet contains items at the top level of your document. For JSON this means key/value pairs that appear at the top level object and in XML attributes on the outermost tag. 

The "Meta" sheet is expected to be vertically aligned, so headings are on first column (not first row), and values are on second column. So a sheet named Meta could look like:

```eval_rst
+---------------+------------+
| dataLicense   | CC         |
+---------------+------------+
| version       | 2          |
+---------------+------------+
| publishedDate | 2001-01-01 |
+---------------+------------+
```

This will create a JSON object like:

```
{"dataLicense": "CC",
 "version: "2",
 "publishedDate": "2001-01-01",
 "someNestedData: [...]}
```

For XML like:

```
<toptag dataLicense="CC" version="2" publishedData="2001-01-01">
  ...
</toptag>
```


## Hash command line at top of file.

For both CSV and Spreadsheet (XLSX) flattentool allows a special line at the top of the file. This line has to start with a "#" character in the first cell (i.e A1 in a spreadsheet) and nothing else. The rest of line contains commands to customize how the spreadsheet is parsed. For example:

```eval_rst
+---------------+------------+-------------+
| #             | skipRows 1 | headerRows 2|
+---------------+------------+-------------+
| this line     | is         | ignored     |
+---------------+------------+-------------+
| Some          | Headings   | Here        |
+---------------+------------+-------------+
| Some More     | Headings   | Here        |
+---------------+------------+-------------+
| some          | data       | here        |
+---------------+------------+-------------+
```

```eval_rst
.. important ::
    If there exists a hash command line at the top of the metatab sheet this will apply default commands across all other sheets (not the metatab itself). This can be overridden by supplying a hash commend line for a particular sheet.
```

The commands that flattentool (and therefore cove) allows are the following:

### skipRows

This is followed by a number i.e ```skipRows 3``` and says how many rows at the top of the file (ignoring the hash line) will be ignored. For example:

```eval_rst
+---------------+------------+-------------+
| #             | skipRows 1 |             |
+---------------+------------+-------------+
| this line     | is         | ignored     |
+---------------+------------+-------------+
| Some          | Headings   | Here        |
+---------------+------------+-------------+
| some          | data       | here        |
+---------------+------------+-------------+
```

Defaults to 0 rows skipped.

### headerRows

This is followed by a number i.e ```headerRows 2``` and says how many rows are header lines in the file. All header rows apart from the first one will be ignored. For example:

```eval_rst
+---------------+------------+------------+
| #             | skipRows 1 |            |
+---------------+------------+------------+
| Some          | Headings   | Here       |
+---------------+------------+------------+
| More          | headings   | here       |
+---------------+------------+------------+
| some          | data       | here       |
+---------------+------------+------------+
```

Defaults to 1 header rows. 0 rows is invalid as cove needs a heading row.


### ignore

This says that this whole sheet should not be looked at by cove:

```eval_rst
+---------------+------------+------------+
| #             | ignore     |            |
+---------------+------------+------------+
| Everthing     | ignored    | on         |
+---------------+------------+------------+
| this          | sheet      |            |
+---------------+------------+------------+
```

### hashComments

This says that columns can be commented out by placing a ```#``` before the column name.  If this command is used in the metatab it means that sheet names can be ignored by adding a ```#``` before the sheet name:

```eval_rst
+---------------+--------------+------------+
| #             | hashcomments |            |
+---------------+--------------+------------+
| Heading       | # Ignored    | Heading 2  |
+---------------+--------------+------------+
| some          | ignored data | data       |
+---------------+--------------+------------+
```




