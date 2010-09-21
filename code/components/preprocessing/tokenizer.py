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
punctuation_pattern = re.compile(r'([.,!?\'\`\";:]|[\]\[\(\){}]\<\>)')
punctuation_pattern = re.compile(r'[.,!?\'\`\";:\]\[\(\){}\<\>]')
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




#### NEW STUFF

# TODO: add abbrev patter for initials and acronyms

punctuation_pattern = re.compile(r'[.,!?\'\`\";:\]\[\(\){}\<\>]')

t_pattern = re.compile(r"(\w+)'t ", re.IGNORECASE)
d_pattern = re.compile(r"(\w+)'d ", re.IGNORECASE)
s_pattern = re.compile(r"(\w+)'s ", re.IGNORECASE)
m_pattern = re.compile(r"(\w+)'m ", re.IGNORECASE)
re_pattern = re.compile(r"(\w+)'re ", re.IGNORECASE)
ll_pattern = re.compile(r"(\w+)'ll ", re.IGNORECASE)
ve_pattern = re.compile(r"(\w+)'ve ", re.IGNORECASE)
posse_pattern = re.compile(r"(\S+)'s ", re.IGNORECASE)

contraction_pattern = re.compile(r"(\w+)'(t|d|s|m|re|ll|ve|s)$", re.IGNORECASE)


def _test_space(char):
    return char.isspace()

def _test_nonspace(char):
    return not char.isspace()
        
def _slurp(string, offset, test):
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
    """Given a string and an offset in the string, return two tuples, one for whitespace after
    the offset and one for a sequence of non-whitespace immdediately after the whitespace. A
    tuple consists of an begin offset, an end offset and a string."""
    begin = offset
    end = offset
    (o1, o2, space) = _slurp(string, offset, _test_space)
    (o3, o4, token) = _slurp(string, o2, _test_nonspace)
    return ((o1, o2, space), (o3, o4, token))


def tokenize_text(text):

    """Tokenize a text and return a set of tokens and a set of sentences. Each token and each
    sentence is a pair of a begin position and end position."""

    offset = 0
    length = len(text)

    all_tokens = []
    while offset < length:
        (space, word) = slurp_token(text, offset)
        if word[2]:
            tokens = _split_word(word, text)
            all_tokens.append(tokens)
        offset = word[1]

    _split_contractions(all_tokens)
        
    lexes = _get_lexes(all_tokens)
    sentences = _get_sentences(all_tokens, text)
    
    return (sentences, lexes)



def _get_lexes(all_tokens):
    """Return all lexes in all_tokens as a flat list."""
    all_lexes = []
    for lexes in  [ p1 + [ct] + p2 for (p1, ct, p2) in all_tokens]:
        all_lexes += lexes
    return all_lexes


def _get_sentences(all_tokens, text):

    def is_sentence_final_abbrev(tok, puncts2, text):
        if not puncts2 and tok[2] in dict_end_abbrevs:
            (space, next_token) = slurp_token(text, tok[1])
            return next_token[2] in dict_initial_tokens
        return False

    def is_eos(puncts2):
        if puncts2:
            for p in puncts2:
                if p[2] in ('.', '?', '!'):
                    return True
        return False
    
    sentences = []
    if not all_tokens:
        return sentences
    first = all_tokens[0][0][0][0]
    for (puncts1, tok, puncts2) in all_tokens:
        if first is None:
            first = tok[0]
        if is_sentence_final_abbrev(tok, puncts2, text) or is_eos(puncts2):
            sentences.append( [first, tok[1]])
            first = None
    return sentences


def _split_word(word, text):
    """Split a word into it's constitutent parts. A word is a tuple of begin offset, end
    offset and a sequence of non-whitespace characters."""
    (opening_puncts, core_token, closing_puncts) = _split_punctuation(word)
    if closing_puncts and closing_puncts[0][2] == '.':
        (core_token, closing_puncts) = \
            _restore_abbreviation(core_token, closing_puncts, text)
    return (opening_puncts, core_token, closing_puncts)


def _restore_abbreviation(core_token, closing_puncts, string):
    """Glue the period back onto the core token if the first closing punctuation is a period
    and the core token is a known abbreviation."""
    last = closing_puncts[-1][1]
    (space, next_token) = slurp_token(string, last)
    if core_token[2]+'.' in dict_abbrevs:
        core_token = (core_token[0], core_token[1] + 1, core_token[2] + '.')
        closing_puncts.pop(0)
    return (core_token, closing_puncts)


def _split_punctuation(word):

    """Return a triple of opening punctuations, core token and closing punctuation. A core
    token can contain internal punctuation but token-initial and token-final punctuations
    are stripped off. If a token has punctuation characters only, then the core token wil
    be the empty string and the closing list will be empty."""
    
    opening_puncts = []
    closing_puncts = []
    core_token = word

    (off1, off2, tok) = word

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
    
    return (opening_puncts,  core_token, closing_puncts)


def _split_contractions(all_tokens):

    new_tokens = []
    for (puncts1, tok, puncts2) in all_tokens:
        found = contraction_pattern.search(tok[2])
        if found:
            idx = found.start(2) - 1
            split_token = [(tok[0], tok[0] + idx, tok[2][:idx]),
                           (tok[0] + idx, tok[1], tok[2][idx:])]
            print split_token
            new_tokens.append( (puncts1, split_token, puncts2) )
        else:
            new_tokens.append( (puncts1, tok, puncts2) )
    return new_tokens


if __name__ == '__main__':
    import sys
    from time import time
    in_file = sys.argv[1]
    btime = time()
    result = tokenize_text(open(in_file).read())
    #print result
    print "\nDONE, processing time was %.3f seconds\n" % (time() - btime)
