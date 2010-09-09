"""

Simple tokenizer.

Presents results in a one-line-per-sentence format with all tokens
separated by one space.

Top-level methods:

    tokenize_file(fin, fout)
    tokenize_string(string)

Algorithm:

    For each line l
       trim(l)
       if paragraph marker <p> is found
          insert sentence marker (EOS) and remove <p>
       tokens = split(l)
       for token t in tokens
          if t contains punctuation:
             split punctuation
             restore abbreviation
             add EOS marker
          t = split_contractions(t)
          print t
          if t contains EOD:
              print newline

Need to clean this up and create a version that can simply add <lex>
tags and <s> tags but nothing else.

"""

import re
from abbreviation import dict_abbrevs
from abbreviation import dict_end_abbrevs
from abbreviation import dict_initial_tokens

# patterns for contractions
t_pattern = re.compile(r"(\w+)'t ", re.IGNORECASE)
d_pattern = re.compile(r"(\w+)'d ", re.IGNORECASE)
s_pattern = re.compile(r"(\w+)'s ", re.IGNORECASE)
m_pattern = re.compile(r"(\w+)'m ", re.IGNORECASE)
re_pattern = re.compile(r"(\w+)'re ", re.IGNORECASE)
ll_pattern = re.compile(r"(\w+)'ll ", re.IGNORECASE)
ve_pattern = re.compile(r"(\w+)'ve ", re.IGNORECASE)
posse_pattern = re.compile(r"(\S+)'s ", re.IGNORECASE) 

# pattern for abbreviations
abbrev_pattern = re.compile(r'^([A-Z]\.)+$')
split_abbrev_pattern = re.compile(r'(\S+) \.')

# pattern for sentence boundaries
eos_pattern = re.compile(r' [.!?]( [")])?$')

# punctuation patterns
punctuation_pattern = re.compile(r'([.,!?\'\`\";:]|[\]\[\(\){}])')
final_punct1_pattern = re.compile(r'(([.,!?\'\`\";:]|[\]\[\(\){}])$)')
final_punct2_pattern = re.compile(r'(([.,!?\'\`\";:]|[\]\[\(\){}]) .$)')
final_punct3_pattern = re.compile(r'(([.,!?\'\`\";:]|[\]\[\(\){}]) . .$)')
init_punct1_pattern = re.compile(r'(^([.,!?\'\`\";:]|[\]\[\(\){}]))')
init_punct2_pattern = re.compile(r'(^. ([.,!?\'\`\";:]|[\]\[\(\){}]))')
init_punct3_pattern = re.compile(r'(^. . ([.,!?\'\`\";:]|[\]\[\(\){}]))')

    
def Split_Punctuation(token):

    """Split punctuation at beginning and end of token. Maximum of
    three punctuation marks at end of token is allowed. Possibly
    better not to split closing brackets if token contains
    corresponding closing bracket (but what about putting one word
    between brackets --> exception)."""

    token = final_punct1_pattern.sub(r' \1', token)
    token = final_punct2_pattern.sub(r' \1', token)
    token = final_punct3_pattern.sub(r' \1', token)
    token = init_punct1_pattern.sub(r'\1 ', token)
    token = init_punct2_pattern.sub(r'\1 ', token)
    token = init_punct3_pattern.sub(r'\1 ', token)
    return token


def Restore_Abbrevs(token):

    """Restore abbreviations. If a period is preceded by a number of
    non-whitespace characters, then check whether those characters
    with the period are an abbreviation. If so, glue them back
    together."""

    found = split_abbrev_pattern.search(token)
    if found:
        if Abbrev(found.group(1)+'.'):
            token = split_abbrev_pattern.sub(r'\1.', token)
    return token


def Abbrev(token):

    """Abbreviation Lookup. A token is an abbreviation either if it is
    on the abbrevs list or if it matches the regular expression
    /(^[A-Z]\.)+/, which encodes initials."""

    found = abbrev_pattern.search(token)
    return ((token in dict_abbrevs) or found)


def Add_EOS_Marker(token, i, line):
   
    """Adding end-of-sentence markers (ie newlines). First check for a
    space followed by a period, exclamation mark or question
    mark. These may be followed by one other punctuation, which is
    either a quote or a closing bracket. Otherwise check whether the
    token is a possible sentence-final abbreviations followed by a
    possible sentence-initial token. In other cases there will be no
    end-of-sentence."""

    if eos_pattern.search(token):
        return token + '\n'
    elif (dict_end_abbrevs.get(token,False)
          and i < len(line)-1 
          and dict_initial_tokens.get(line[i+1],False)):
        return token + '\n'
    else: 
        return token + ' '


def Split_Contractions(token):

#   $token =~ s/(\S+)\'s /$1 \'s /; # hack for for possessive 's
    token = re_pattern.sub(r"\1 're ", token)
    token =  t_pattern.sub(r"\1 't ", token)
    token = ll_pattern.sub(r"\1 'll ", token)
    token = ve_pattern.sub(r"\1 've ", token)
    token =  d_pattern.sub(r"\1 'd ", token)
    token =  s_pattern.sub(r"\1 's ", token)
    token =  m_pattern.sub(r"\1 'm ", token)
    token = posse_pattern.sub(r"\1 's ", token)
    return token



def tokenize_file(in_name, out_name):

    """Take the content of the input file, tokenize it, and write it to
    the output file."""
    
    fin = open(in_name,'r')
    fout = open(out_name,'w')
    fout.write(tokenize_string(fin.read()))
    fin.close()
    fout.close()


def tokenize_string(string, format='text'):

    """Tokenize a string and return it in a one-sentence-per-line
    format with tokens separated by a space.

    arguments:
       string - the string to be tokenized
       format - determines output format, choice of text and xml
                (not yet used)

    returns:
       a tokenized string in text or xml format."""
    
    tokenized_string = ''

    for line in string.split("\n"):
        line = line.strip()
        if line.startswith('<P>'):
            line = line[2:]
            tokenized_string += '\n<P>\n\n'
        tokens = line.split()  
        index_count = 0
        for token in tokens:
            found_punc = punctuation_pattern.search(token)
            if(found_punc):
                token = Split_Punctuation(token)
                token = Restore_Abbrevs(token)
                token = Add_EOS_Marker(token, index_count, tokens)
            else:
                token = token + ' '
            token = Split_Contractions(token)
            tokenized_string += token
            index_count += 1

    return tokenized_string



if __name__ == '__main__':
    from time import time
    btime = time()
    in_file = '../../data/in/simple-xml/test.xml'
    out_file = '../../data/tmp/tok.txt'
    Tokenize_File(in_file, out_file)
    print "\nDONE, processing time was %.3f seconds\n" % (time() - btime)
    print open(out_file).read()
