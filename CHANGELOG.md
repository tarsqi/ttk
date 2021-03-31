# Change Log

All notable changes to this project are documented in this file.

The format is loosely based on [Keep a Changelog](http://keepachangelog.com/). Loosely because we do not keep separate sections within a version for additions and fixes etcetera, instead most logged changes will start with one of Added, Changed, Updated, Deprecated, Removed, Fixed, or Security.

This project tries to adhere to [Semantic Versioning](http://semver.org/).



## Current Changes

- Added spaCy for tokenization and tagging.



## Version 3.0.1 — 2021-03-02

- Overhauled the documentation for GitHub pages.
- Fixed issue with GUTime failing because working directory is not on search path anymore (issue [#105](https://github.com/tarsqi/ttk/issues/105)).
- Fixed issue with warning in Python 3 (issue [#104](https://github.com/tarsqi/ttk/issues/104)).
- Changed how the TTK_ROOT variable is loaded into the environment (issue [#103](https://github.com/tarsqi/ttk/issues/103)).

## Version 3.0.0 — 2021-01-05

- Identical to version 2.2.1 except for some changes in documentation and minor changes in this file and the version file.

## Version 2.2.1 — 2021-01-05

- Changed code to make it run on both Python 2.7 and Python 3.8.5  (issue [#79](https://github.com/tarsqi/ttk/issues/79)).
- Updated documentation, included minor refactoring of code.
- Added some past results of running the regression script.


## Version 2.2.0 — 2020-12-12

- Changed source format parameter (issue [#39](https://github.com/tarsqi/ttk/issues/39)), now using --source-format.
- Added code for TTK to Knowtator conversion (issue [#77](https://github.com/tarsqi/ttk/issues/77)).
- Fixed issue [#43](https://github.com/tarsqi/ttk/issues/43) by adding minimal pipeline checks.
- Fixed installation issues with the TreeTagger (issues [#89](https://github.com/tarsqi/ttk/issues/89) and [#90](https://github.com/tarsqi/ttk/issues/90)).
- Fixed problem with file names in vectors.
- Fixed some encoding issues with Evita and the classifier.
- Added initial capability to process and create LIF documents (issue [#88](https://github.com/tarsqi/ttk/issues/88)).
- Fixed problem with weird GUTime output with multiple ERROR properties in the XML tag.
- Updated conversion from ECB to TTK (part of issue [#83](https://github.com/tarsqi/ttk/issues/83)).


## Version 2.1.1 — 2018-10-17

- Fixed issue [#84](https://github.com/tarsqi/ttk/issues/84).
- Fixed issue [#74](https://github.com/tarsqi/ttk/issues/74). Changed inline error reporting by sending errors to standard error instead of standard output and removed all other print statements that are not embedded in print methods and functions.
- Added processing history to TTK document (issue [#14](https://github.com/tarsqi/ttk/issues/14), in progress).
- Fixed some errors in Thyme conversion code.
- Added initial version of converter from the EventCoreferenceBank format to the TTK format (issue [#83](https://github.com/tarsqi/ttk/issues/83), in progress).


## Version 2.1.0 — 2017-06-13

- Added code to update chunks given Timex tags. This was done in order to fix issue [#75](https://github.com/tarsqi/ttk/issues/75).
- Added functionality to the evaluation code that makes inspection easier: it can now print html files with aligned tags from the gold data and system data.
- Changed the chunker so that it can now take known terms as input. This is for example useful for cases where we want to import events from an external source and we want to make sure that these events are not missed because they are not in chunks. See issue [#63](https://github.com/tarsqi/ttk/issues/63).
- Added code to guess the input format (issue [#51](https://github.com/tarsqi/ttk/issues/63)), with this the --source option does not always need to be specified.
- Changed the main script and the logger so that the main script now writes a warning to standard output if errors or warnings were logged.
- Fixed inconsistent DCT import behavior (issue [#70](https://github.com/tarsqi/ttk/issues/70)).
- Updated documentation (mostly spelling out some Windows limitations).
- Changed command line options a bit (minor simplifications).
- Fixed UnicodeDecodeError bug when printing a tag as a TTK tag.
- Fixed problem with often-used harmful print statement that caused problems when using the --pipe option (this is a partial fix of issue [#74](https://github.com/tarsqi/ttk/issues/74)).


## Version 2.0.2 — 2017-04-09

- Fixed bug where id attributes were added to source tags (issue #56).
- Fixed bug where directory names could not have spaces in them (issue #42).
- Added explanation on unintuitive character offsets of docelement (issue #15).
- Changed how Tag instances are created, which used to be somewhat inconsistent.


## Version 2.0.1 — 2017-04-03

- Added links to Tarsqi publications to the manual.
- Added use of confidence scores to LinkMerger (issue #23).
- Fixed bug where TTK created output with duplicate attributes (issue #32).
- Fixed issue with missing link identifiers (issue #38).
- Fixed bug where duplicate links were created by S2T component.
- Removed some completely out-of-date or irrelevant documentation and notes.


## Version 2.0.0 — 2017-03-27

A complete reset of the Tarsqi code. The most significant changes are:

- Massive simplification of many components.
- New and updated documentation.
- Use Mallet toolkit instead of the old classifier.
- Uses stand-off annotation thoughout instead of inline XML.
- Redesigned libraries.
- New test and evaluation code.


## Version 1.0 — 2007-11-15

First released version. Basically a wrapper around a series of components that were not released before individually. This version, unlike all later versions, is not available on GitHub, but it can be downloaded from [http://timeml.org/tarsqi/toolkit/index.html](http://timeml.org/tarsqi/toolkit/index.html).
