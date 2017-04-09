# Curious offsets

This document explains why the docelement tag might appear to be outside the top-level xml tag of a file.

Consider the following minimal input.

```xml
<?xml version="1.0" ?>
<text></text>
```

And the resulting ttk file after processing.


```xml
<ttk>
<text>

</text>
<metadata>
  <dct value="20170409"/>
</metadata>
<source_tags>
  <text begin="1" end="1" />
</source_tags>
<tarsqi_tags>
  <docelement begin="0" end="2" id="d1" origin="DOCSTRUCTURE" type="paragraph" />
</tarsqi_tags>
</ttk>
```

It may look weird that the text tag has offsets 1:1 while the docelement tag has offsets 0:2. But note that the opening text tag does not start immediately after the ?xml processing instruction and that the closing text tag is followed by a newline.

The document structure parser in docmodel.docstructure_parser.DocumentStructureParser takes the full text content of the document, which includes characters before and after the main tag. Therefore, if you have only one docelement, the main tag's offsets will be included in the docelement tag's offsets.
