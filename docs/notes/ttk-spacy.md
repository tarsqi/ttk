# Adding spaCy to TTK

March 2021

We wantr to run spaCy as the very first component, doing at least two parts of what the preprocessor did (tokenization and tagging). Later we can see whether we want to modify the spaCy tokenizer with some of the dictionaries in the TTK tokenizer. Because spaCy only has noun chunks it will not take the part of the chunker.

We have two ways to preprocess

```bash
$> python3 tarsqi.py --pipeline=PREPROCESSOR INFILE OUTFILE
$> python3 tarsqi.py --pipeline=TOKENIZER,TAGGER,CHUNKER INFILE OUTFILE
```

To simplify things we move to just having the first. Later we can add flags for settings if needed.

Current processing is that we loop over the document elements, get the text for each of them and then do the following steps:

1. The tokenizer creates a list of sentence markers and tokenizer objects

   ```
   [('<s>', None),
    ('The', <components.preprocessing.tokenizer.TokenizedLex object at 0x11fe9fca0>),
    ('dog', <components.preprocessing.tokenizer.TokenizedLex object at 0x11fe9ffd0>),
    ('sleeps', <components.preprocessing.tokenizer.TokenizedLex object at 0x11fe9fd00>),
    ('today', <components.preprocessing.tokenizer.TokenizedLex object at 0x11fe9fd60>),
    ('.', <components.preprocessing.tokenizer.TokenizedLex object at 0x11fe9f040>)]
   ```

   A TokenizedLex instance has `begin`, `end` and `text` variables.

2. All offsets are adjusted in place so they are relative to the beginning of the text instead of the beginning of the docelement.

3. The TreeTagger is called on the list returned from the tokenizer and returns a list of lists of tuples

   ```
   [[('The', 'DT', 'the', 2, 5),
     ('dog', 'NN', 'dog', 6, 9),
     ('sleeps', 'VBZ', 'sleep', 10, 16),
     ('today', 'NN', 'today', 17, 22),
     ('.', '.', '.', 22, 23)]]
   ```

   Each tuple is a token with text, tag, lemma, start and end fields.

4. The chunker inserts xml tags for the noun and verb groups

   ```
   [['<ng>', ('The', 'DT', 'the', 2, 5), ('dog', 'NN', 'dog', 6, 9), '</ng>',
     '<vg>', ('sleeps', 'VBZ', 'sleep', 10, 16), '</vg>',
     '<ng>', ('today', 'NN', 'today', 17, 22), '</ng>', 
     ('.', '.', '.', 22, 23)]]
   ```

5. The output of the chunker is exported as tags to the TarsqiDocument.

The code for this is

```python
for element in self.document.elements():
    text = self.document.sourcedoc.text[element.begin:element.end]
    tokens = self._tokenize_text(text)
    adjust_lex_offsets(tokens, element.begin)
    tags = self._tag_text(tokens)
    chunks = self._chunk_text(tags)
    self._export(chunks)
```

The easiest way to insert spaCy is probably something like the following.

```python
for element in self.document.elements():
    text = self.document.sourcedoc.text[element.begin:element.end]
    doc = nlp(text)
    tags = extract_tags(doc)
    adjust_lex_offsets2(tags, element.begin)
    chunks = self._chunk_text(tags)
    self._export(chunks)
```

Here, `extract_tags()` should create the same kind of output as we got from `self._tag_text(tokens)`, and `adjust_lex_offsets2()` is very similar to `adjust_lex_offsets()` except that it takes a slightly different datastructure as input.

Some benchmarking, runnig the preprocessor on the entire TimeBank.

- Old version: 12.490 seconds
- New version (slow): 26.334 seconds
- New version (fast): 11.713 seconds

The slow new version uses the default pipeline, the fast one disables a bunch of components:

```python
NLP = spacy.load("en_core_web_sm")
for component in NLP.component_names:
    if component not in ('tagger', 'attribute_ruler', 'lemmatizer', 'senter'):
        NLP.disable_pipe(component)
NLP.add_pipe('sentencizer')
```

The annoying thing is that with the fast version you get stuff like the following, which is dealt with much better in the slow version.

```xml
  <lex begin="498" end="499" id="l89" lemma="$" pos="IN" text="$" />
  <lex begin="499" end="502" id="l90" lemma="110" pos="IN" text="110" />
  <lex begin="503" end="510" id="l91" lemma="million" pos="IN" text="million" />
```

Output comparison: many many many changes. Hard to say whether this is okay since we have not set up a gold standard for this task. When running the tests we get the same results as before though, so there are no significant downstream issues.

Weird stuff, full version stopped working, not sure why, but there was an issue where in some cases we got a sentence tag without a start offset.

```xml
<Tag s None:1102 { id='s16' origin='PREPROCESSOR' }>
```

This turned out to be caused by an empty sentence, added a check for that.



TODO:

- need to check whether the tags are the same
- do some more speed benchmarking
- first version will probably run all standard parts of the spaCy pipeline, fix that later
- remove the 

