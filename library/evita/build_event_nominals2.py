"""

Create three anydbm dictionaries with words from wordnet that can be events: (1)
whose primary sense in WordNet is an event, those where all senses are events
and (3) those where some senses are events.

New dbm files are written to the dictionaries directory, where they will overwrite
existing anydbm files if present. This script may improve Evita performance. This
scripts requires the files

     dictionaries/wnPrimSenseIsEvent.txt
     dictionaries/wnAllSensesAreEvents.txt
     dictionaries/wnSomeSensesAreEvents.txt

The Evita code expects the dbm files to end in .db, so if this script generates
another extenstion then it should b echanged.

The third WordNet derived file (wnSomeSensesAreEvents.txt, with nouns where some
senses are events) is currently not used by Evita.

"""

import os
import sys
import anydbm

# Open text versions of DBM files in Dicts directory.
file1 = open(os.path.join('dictionaries', 'wnPrimSenseIsEvent.txt'), 'r')
file2 = open(os.path.join('dictionaries', 'wnAllSensesAreEvents.txt'), 'r')
file3 = open(os.path.join('dictionaries', 'wnAllSensesAreEvents.txt'), 'r')

# Put newly created dbms in the dictionaries directory, where they will
# overwrite the current ones.
dbm1 = anydbm.open(os.path.join('dictionaries', 'wnPrimSenseIsEvent'), 'n')
dbm2 = anydbm.open(os.path.join('dictionaries', 'wnAllSensesAreEvents'), 'n')
dbm3 = anydbm.open(os.path.join('dictionaries', 'wnSomeSensesAreEvents'), 'n')

for line in file1: dbm1[line.strip()] = '1'
for line in file2: dbm2[line.strip()] = '1'
for line in file3: dbm3[line.strip()] = '1'
