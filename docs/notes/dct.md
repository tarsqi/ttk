# Dealing with the DCT

The DCT is available on the TarsqiDocument through the `get_dct()` method, which simply gets the DCT from the `metadata` dictionary. Metadata are handed to the TarsqiDocument by the docmodel.metadata_parser module and can be accessed later by other components. The idea is that those other components do not set the meta data and that they are just consumers.


## Creating the DCT

The MetadataParser class in docmodel.metadata_parser sets the default behavior. The `parse()` method calls the default implementation of `get_dct()` which is to collect the DCT from all the four places where it could be defined: command line option, metadata, tarsqi tags and source tags.

```python
def parse(self, tarsqidoc):
    self.tarsqidoc = tarsqidoc
    self.tarsqidoc.metadata['dct'] = self.get_dct()

def get_dct(self):
    return _moderate_dct_vals(
        self.tarsqidoc.options.dct,
        self.tarsqidoc.sourcedoc.metadata.get('dct'),
        _get_dct_values(self.tarsqidoc.sourcedoc.tags),
        _get_dct_values(self.tarsqidoc.tags))
```

When getting DCT values from a TagRepository all tags ar eselected that have (1) the tagname `TIMEX3` and (2) the `functionInDocument` attribute set to `CREATION_TIME` (following the TimeML standard). The `_moderate_dct_vals` method will resolve any conflicts, using a precedence ordering between the kinds of DCTs: DCT in option > DCT in metadata > DCT in tarsqi tags > DCT in source tags. If multiple values are found and they are not the same then a warning will be written to the log file. If no value is found then the method will default to the current date.

Specialized metadata parsers can be created that override the default behavior. For example, parsing the metadata is more involved for the MetadataParserTimebank class, where the SourceDoc's TagRepository and text content are searched for the desired information.

Notice that no matter what the metadata parser does, in the end it puts the result in the metadata dictionary.

It is the responsibility of the source parser to get the information from the source to where it needs to go. The behavior is different depending on what the source document is:

- If the source is `text` then no tags or metadata will be instantiated. The only DCT available to the metadata parser would be the one handed in as a command line option.

- If the source is `xml` then all tags in the XML will be added to the TagRepository on the SourceDoc. These may include TIMEX3 tags that perform the DCT function. So the metadata parser may find DCTs in the source tags and perhaps a DCT handed in as an option. The source parser works the same for subtypes of `xml`, like `timebank`, but not that while the source parsing is the same, the metadata parsing can be very different.

- If the source is `ttk` then information is distributed the contents over the TagRepository on the TarsqiDocument, the metadata dictionary on the SourceDoc, and the TagRepository on the SourceDoc. In this case, potential DCTs are available in all four spots.

Here is a rather tendentious example of a TTK document with three kinds of DCTs. It is simplified in that only Timex tags are printed and that some attributes are ignored.

```xml
<ttk>
<text>Today and tomorrow.</text>
<metadata>
  <dct value="20170403"/>
</metadata>
<source_tags>
  <TIMEX3 begin="0" end="5" type="DATE" value="20170403" functionInDocument="CREATION_TIME" />
</source_tags>
<tarsqi_tags>
  <TIMEX3 begin="0" end="5" tid="t1" type="DATE" value="20170403" functionInDocument="CREATION_TIME"/>
  <TIMEX3 begin="10" end="18" tid="t2" type="DATE" value="20170404" functionInDocument="CREATION_TIME"/>
</tarsqi_tags>
</ttk>
```

This could be a document created by the a pipeline with the preprocessor and GUTime and where the original document had an existing TIMEX3 tag. Assume for now that GUTime has the ability to import existing tags (it hasn't, but importing tags is a feature that was recently added to Evita). Also assume that GUTime erroneously assigns DCT status to the TIMEX3 tag that it adds. So we have the following DCTs:

| DCT source  | values            |
| ----------- | ----------------- |
| metadata    | 20170403          |
| source_tags | 20170403          |
| tarsqi_tags | 20170403 20170404 |

With this input, DCT moderation will decide to take 20170403 as the DCT, but also write a warning because there are two different values suggested for the DCT.


## Discussion

The above design was in part to deal with some issues that older code presented. There have always been several spots where a DCT could show up, but there never was a way to decide which one would be taken as **the** DCT. It was felt that there was a need to sync the value in the metadata and values that may come from the traditional TimeML way of representing DTCs. There was also a need to add the option to hand in a DCT, which further stressed the need for a principled approach. The moderation code resolves these issues. We do not require the values to be in sync, but we do have a mechanism to pick one, and we do warn the user if there was a conflict.

A not yet resolved question is whether the DCT should be added as an empty TIMEX3 tag to the document's TagRepository in case no exiting TIMEX3 tag expresses the DCT. At first we said no way. But it turns out that Blinker tries to generate TLINKs between TIMEX3 tags including the DCT. Which would be hard to do with the DCT just inside the metadata. Also, the classifier should probably also try to add links from events to the DCT, and we can only do that if there is a Timex tag with an identifier. So we probably should add a non-consuming tag with id="t0" in case there is no DCT Timex or add the `functionInDocument` attribute if we find a Timex with the same value as the DCT (adding it for just one or perhaps for all Timexes with the dct value).
