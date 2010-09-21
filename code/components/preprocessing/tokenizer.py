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
from xml.sax.saxutils import escape

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

abbrev_pattern = re.compile(r'^([A-Z]\.)+$')

punctuation_pattern = re.compile(r'[.,!?\'\`\";:\]\[\(\){}\<\>]')

# may want to use an exaustive list instead (see contractions.txt), but note that this
# pattern also covers possessives
contraction_pattern = re.compile(r"(\w+)'(t|d|s|m|re|ll|ve|s)$", re.IGNORECASE)


def _test_space(char):
    return char.isspace()

def _test_nonspace(char):
    return not char.isspace()


class Tokenizer:

    def __init__(self, text):
        self.text = text
        self.length = len(text)
        self.lexes = []
        self.sentences = []
        
        
    def tokenize_text(self):

        """Tokenize a text and return a set of tokens and a set of sentences. Each token and each
        sentence is a pair of a begin position and end position."""

        offset = 0
        self.lexes = []
        self.sentences = []
        
        all_tokens = []
        while offset < self.length:
            (space, word) = self.slurp_token(offset)
            if word[2]:
                tokens = self._split_word(word)
                all_tokens.append(tokens)
            offset = word[1]

        self._set_sentences(all_tokens)
        all_tokens = self._split_contractions(all_tokens)
        self._set_lexes(all_tokens)
    
        return (self.sentences, self.lexes)        


    def slurp_token(self, offset):
        """Given a string and an offset in the string, return two tuples, one for whitespace after
        the offset and one for a sequence of non-whitespace immdediately after the
        whitespace. A tuple consists of an begin offset, an end offset and a string."""
        (o1, o2, space) = self._slurp(offset, _test_space)
        (o3, o4, token) = self._slurp(o2, _test_nonspace)
        return ((o1, o2, space), (o3, o4, token))

    def _slurp(self, offset, test):
        begin = offset
        end = offset
        while offset < self.length:
            char = self.text[offset]
            if test(char):
                offset += 1
                end = offset
            else:
                return (begin, end, self.text[begin:end])
        return (begin, end, self.text[begin:end])
    
    def _set_lexes(self, all_tokens):
        """Set lexes list by flattening all_tokens. Sometimes empty core tokens are created,
        filter those out at this step."""
        for (p1, ct, p2) in all_tokens:
            self.lexes += p1
            for tok in ct:
                if tok[0] != tok[1]:
                    self.lexes.append(tok)
            self.lexes += p2

            
    def _set_sentences(self, all_tokens):

        def is_sentence_final_abbrev(tok, puncts2):
            if not puncts2 and tok[2] in dict_end_abbrevs:
                (space, next_token) = self.slurp_token(tok[1])
                return next_token[2] in dict_initial_tokens
            return False

        def token_has_eos(token):
            return token[2] in ('.', '?', '!')
        
        def has_eos(puncts):
            return filter( token_has_eos, puncts)
            
        if all_tokens:
            first = all_tokens[0][0][0][0]
            for (puncts1, tok, puncts2) in all_tokens:
                if first is None:
                    first = tok[0]
                if is_sentence_final_abbrev(tok, puncts2) or has_eos(puncts2):
                    last = tok[1]
                    if puncts2:
                        last = puncts2[-1][1]
                    self.sentences.append( [first, last])
                    first = None


    def _split_word(self, word):
        """Split a word into it's constitutent parts. A word is a tuple of begin offset, end
        offset and a sequence of non-whitespace characters."""
        (opening_puncts, core_token, closing_puncts) = self._split_punctuation(word)
        if closing_puncts and closing_puncts[0][2] == '.':
            (core_token, closing_puncts) = \
                self._restore_abbreviation(core_token, closing_puncts)
        return (opening_puncts, core_token, closing_puncts)


    def _restore_abbreviation(self, core_token, closing_puncts):
        """Glue the period back onto the core token if the first closing punctuation is a period
        and the core token is a known abbreviation."""
        last = closing_puncts[-1][1]
        (space, next_token) = self.slurp_token(last)
        restored = core_token[2] + '.'
        if restored in dict_abbrevs or abbrev_pattern.search(restored):
            core_token = (core_token[0], core_token[1] + 1, restored)
            closing_puncts.pop(0)
        return (core_token, closing_puncts)


    def _split_punctuation(self, word):

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
                opening_puncts.append((off1, off1 + 1, tok[0]))
                core_token = (off1 + 1, off2, tok[1:])
                off1 += 1
                tok = tok[1:]
            else:
                break
    
        while True:
            if not tok: break
            found_punc = punctuation_pattern.search(tok[-1])
            if found_punc:
                closing_puncts.append((off2 - 1, off2, tok[-1]))
                core_token = (off1, off2 - 1, tok[:-1])
                off2 += -1
                tok = tok[:-1]
            else:
                break
    
        return (opening_puncts,  core_token, closing_puncts)


    def _split_contractions(self, all_tokens):

        new_tokens = []
        for (puncts1, tok, puncts2) in all_tokens:
            if not "'" in tok[2]:
                new_tokens.append( (puncts1, [tok], puncts2) )
                continue
            found = contraction_pattern.search(tok[2])
            if found:
                idx = found.start(2) - 1
                split_token = [(tok[0], tok[0] + idx, tok[2][:idx]),
                               (tok[0] + idx, tok[1], tok[2][idx:])]
                new_tokens.append( (puncts1, split_token, puncts2) )
            else:
                new_tokens.append( (puncts1, [tok], puncts2) )
        return new_tokens


    def print_xml(self, outfile):

        fh = open(outfile,'w')
        fh.write("<TOKENS>\n")
        
        opening_lexes = {}
        closing_lexes = {}
        for l in self.lexes:
            opening_lexes[l[0]] = l
            closing_lexes[l[1]] = l

        opening_sents = {}
        closing_sents = {}
        for s in self.sentences:
            opening_sents[s[0]] = s
            closing_sents[s[1]] = s
        
        in_lex = False
        in_sent = False
        off = 0

        for char in self.text:

            closing_lex = closing_lexes.get(off)
            opening_lex = opening_lexes.get(off)
            closing_s = closing_sents.get(off)
            opening_s = opening_sents.get(off)

            if closing_lex:
                fh.write("</lex>\n")
                in_lex = False
            if closing_s:
                fh.write("</s>\n")
                in_sent = False
                
            if opening_s:
                fh.write("<s>\n")
                in_sent = True
            if opening_lex:
                indent = ''
                if in_sent: indent = '  '
                fh.write(indent + "<lex begin='%s' end='%s'>" % (opening_lex[0], opening_lex[1]))
                in_lex = True

            if in_lex:
                fh.write(escape(char))
                
            off += 1

        fh.write("</TOKENS>\n")



if __name__ == '__main__':
    import sys
    from time import time
    in_file = sys.argv[1]
    btime = time()
    tokenizer = Tokenizer( open(in_file).read() )
    for i in range(100):
        tokenizer.tokenize_text()
    tokenizer.print_xml('out-tokens.xml')
    
    print "\nDONE, processing time was %.3f seconds\n" % (time() - btime)
