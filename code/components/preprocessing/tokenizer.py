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
    """Split punctuation at beginning and end of token. Maximum of three punctuation marks
    at end of token is allowed. Possibly better not to split closing brackets if token
    contains corresponding closing bracket (but what about putting one word between
    brackets --> exception)."""
    token = final_punct1_pattern.sub(r' \1', token)
    token = final_punct2_pattern.sub(r' \1', token)
    token = final_punct3_pattern.sub(r' \1', token)
    token = init_punct1_pattern.sub(r'\1 ', token)
    token = init_punct2_pattern.sub(r'\1 ', token)
    token = init_punct3_pattern.sub(r'\1 ', token)
    return token

def Restore_Abbrevs(token):
    """Restore abbreviations. If a period is preceded by a number of non-whitespace
    characters, then check whether those characters with the period are an
    abbreviation. If so, glue them back together."""
    found = split_abbrev_pattern.search(token)
    if found:
        if Abbrev(found.group(1)+'.'):
            token = split_abbrev_pattern.sub(r'\1.', token)
    return token

def Abbrev(token):
    """Abbreviation Lookup. A token is an abbreviation either if it is on the abbrevs list
    or if it matches the regular expression /(^[A-Z]\.)+/, which encodes initials."""
    found = abbrev_pattern.search(token)
    return ((token in dict_abbrevs) or found)

def Add_EOS_Marker(token, i, line):
    """Adding end-of-sentence markers (ie newlines). First check for a space followed by a
    period, exclamation mark or question mark. These may be followed by one other
    punctuation, which is either a quote or a closing bracket. Otherwise check whether the
    token is a possible sentence-final abbreviations followed by a possible
    sentence-initial token. In other cases there will be no end-of-sentence."""
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
    """Take the content of the input file, tokenize it, and write it to the output
    file."""
    fin = open(in_name,'r')
    fout = open(out_name,'w')
    fout.write(tokenize_string(fin.read()))
    fin.close()
    fout.close()


def tokenize_string(string, format='text'):

    """Tokenize a string and return it in a one-sentence-per-line format with tokens
    separated by a space.

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





def test_space(char):
    return char.isspace()

def test_nonspace(char):
    return not char.isspace()
        
def slurp(string, offset, test):
    begin = offset
    end = offset
    length = len(string)
    while offset < length:
        char = string[offset]
        if test(char):
            offset += 1
            end = offset
        else:
            return (begin, end, string[begin:end])
    return (begin, end, string[begin:end])



def slurp_token(string, offset):

    begin = offset
    end = offset
    (o1, o2, space) = slurp(string, offset, test_space)
    (o3, o4, token) = slurp(string, o2, test_nonspace)
    return ((o1, o2, space), (o3, o4, token))




def tokenize_string_new(string, format='text'):

    """Tokenize a string and return it in a one-sentence-per-line format with tokens
    separated by a space.

    arguments:
       string - the string to be tokenized
       format - determines output format, choice of text and xml
                (not yet used)
    returns:
       a tokenized string in text or xml format."""

    offset = 0
    length = len(string)

    all_tokens = []
    while offset < length:
        (space, token) = slurp_token(string, offset)
        if token[2]:
            tokens = X_tokenize(token, string)
            all_tokens += tokens
        offset = token[1]

    return all_tokens




def X_tokenize(token, string):

    (opening_puncts, core_token, closing_puncts) = X_split_punctuation(token)

    if closing_puncts and closing_puncts[0][2] == '.':
        print ':::', core_token
        
    return [token]


def X_split_punctuation(token):

    """Return a triple of opening punctuations, core token and closing punctuation. A core
    token can contain internal punctuation but token-initial and token-final punctuations
    are stripped off. If a token has punctuation characters only, then the core token wil
    be '' and the closing list will be empty."""
    
    opening_puncts = []
    closing_puncts = []
    core_token = token

    tok = token[2]
    off1 = token[0]
    off2 = token[1]

    while True:
        if not tok: break
        found_punc = punctuation_pattern.search(tok[0])
        if found_punc:
            opening_puncts.append((off1, off1+1, tok[0]))
            core_token = (off1+1, off2,tok[1:])
            off1 += 1
            tok = tok[1:]
        else:
            break
    
    while True:
        if not tok: break
        found_punc = punctuation_pattern.search(tok[-1])
        if found_punc:
            closing_puncts.append((off2-1, off2, tok[-1]))
            core_token = (off1, off2-1, tok[:-1])
            off2 += -1
            tok = tok[:-1]
        else:
            break
    
    print opening_puncts + [core_token] + closing_puncts
    #print (opening_puncts,  core_token, closing_puncts)
    return (opening_puncts,  core_token, closing_puncts)



def X__something():
    
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
    import sys
    from time import time
    in_file = sys.argv[1]
    btime = time()
    result = tokenize_string_new(open(in_file).read())
    #print result
    print "\nDONE, processing time was %.3f seconds\n" % (time() - btime)
