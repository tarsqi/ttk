"""

Simple tokenizer that leaves the input unchanged and that generates character
offsets of tokens and sentences.

Usage:

    tokenizer = Tokenizer(text_string)
    tokenizer.tokenize_text()

At this point, you can get lists of sentences offsets and token offsets in the
tokenizer object:

    print tokenizer.sentences
    print tokenizer.tokens

You can also get the output as an xml string or in the old-fashioned
format with one-sentences-per-line and tokens separated by spaces:

    print tokenizer.get_tokenized_as_xml()
    print tokenizer.get_tokenized_as_string()

Both methods return unicode strings.

If you run this file as the main script, it expects a filename as the single
argument. It prints both the xml string and the old-fashioned string to the
standard output, followed by a note on elasped time. Edit the end of the script
to change this.

"""

import re
from StringIO import StringIO
from xml.sax.saxutils import escape

from abbreviation import dict_abbrevs
from abbreviation import dict_end_abbrevs
from abbreviation import dict_initial_tokens


abbrev_pattern = re.compile(r'^([A-Z]\.)+$')

punctuation_pattern = re.compile(r'[.,!?\'\`\";:\]\[\(\){}\<\>]')

# may want to use an exaustive list instead (see contractions.txt), but note
# that this pattern also covers possessives
contraction_pattern1 = re.compile(r"(\w+)(n't)$", re.IGNORECASE)
contraction_pattern2 = re.compile(r"(\w+)'(t|d|s|m|re|ll|ve|s)$", re.IGNORECASE)


def test_space(char):
    return char.isspace()


def test_nonspace(char):
    return not char.isspace()


def token_is_abbreviation(token):
    """Return True if token is an abbreviation or acronym. Note that this
    overgeneralizes since it catches all initials, including 'So would I. This
    is...'. Decided that it was better to miss some sentence boundaries than
    adding wrong boundaries."""
    return token in dict_abbrevs or abbrev_pattern.search(token)


class Tokenizer:

    """Class to create lex tags and s tags given a text string that is not
    modified. The lexes and sentences are gathered in the variables with the
    same name. The token variable contains intermediate data, basically starting
    with a list of non-whitespace character sequences, splitting and merging
    these sequences as processing continues.

    One thing that should be added is functionality that forces sentence
    boundaries, so that document structure level processing or prior tags can
    help correctly tokenize headers and such."""

    def __init__(self, text):
        self.text = text
        self.length = len(text)
        self.tokens = []
        self.lexes = []
        self.sentences = []

    def tokenize_text(self):
        """Tokenize a text and return an instance of TokenizedText. Create lists
        of sentences and lexes and feed these into the TokenizedText. Each token
        and each sentence is a pair of a begin position and end position."""
        offset = 0
        self.tokens = []
        self.lexes = []
        self.sentences = []
        while offset < self.length:
            (space, word) = self.slurp_token(offset)
            if word[2]:
                tokens = self._split_word(word)
                self.tokens.append(tokens)
            offset = word[1]
        self._set_sentences()
        self._split_contractions()
        self._set_lexes()
        return TokenizedText(self.sentences, self.lexes)

    def slurp_token(self, offset):
        """Given a string and an offset in the string, return two tuples, one
        for whitespace characters after the offset and one for non-whitespaces
        characters immediately after the whitespace. A tuple consists of a begin
        offset, an end offset and a string."""
        (o1, o2, space) = self._slurp(offset, test_space)
        (o3, o4, token) = self._slurp(o2, test_nonspace)
        return ((o1, o2, space), (o3, o4, token))

    def _slurp(self, offset, test):
        begin = offset
        end = offset
        length = self.length
        while offset < length:
            char = self.text[offset]
            if test(char):
                offset += 1
                end = offset
            else:
                return (begin, end, self.text[begin:end])
        return (begin, end, self.text[begin:end])

    def _set_lexes(self, ):
        """Set lexes list by flattening self.tokens. Sometimes empty core tokens are
        created, filter those out at this step."""
        for (p1, ct, p2) in self.tokens:
            self.lexes += p1
            for tok in ct:
                if tok[0] != tok[1]:
                    self.lexes.append(tok)
            self.lexes += p2

    def _set_sentences(self):

        def is_sentence_final_abbrev(tok, puncts2):
            if not puncts2 and tok[2] in dict_end_abbrevs:
                (space, next_token) = self.slurp_token(tok[1])
                return next_token[2] in dict_initial_tokens
            return False

        def has_eos(puncts):
            token_has_eos = (lambda token: token[2] in ('.', '?', '!'))
            return filter( token_has_eos, puncts)

        if self.tokens:
            first = self._first_token_start()
            for (puncts1, tok, puncts2) in self.tokens:
                if first is None:
                    first = tok[0]
                if is_sentence_final_abbrev(tok, puncts2) or has_eos(puncts2):
                    last = tok[1]
                    if puncts2:
                        last = puncts2[-1][1]
                    self.sentences.append([first, last])
                    first = None


    def _first_token_start(self):
        """Return the begin position of the first token. This could be of the
        core token or of a punctuation marker that was split off."""
        first = self.tokens[0]
        tok = first[1]
        if first[0]:
            tok = first[0][0]
        return tok[0]

    def _split_word(self, word):
        """Split a word into it's constitutent parts. A word is a tuple of begin
        offset, end offset and a sequence of non-whitespace characters."""
        (opening_puncts, core_token, closing_puncts) = self._split_punctuation(word)
        if closing_puncts and closing_puncts[0][2] == '.':
            (core_token, closing_puncts) = \
                self._restore_abbreviation(core_token, closing_puncts)
        return (opening_puncts, core_token, closing_puncts)

    def _restore_abbreviation(self, core_token, closing_puncts):
        """Glue the period back onto the core token if the first closing punctuation
        is a period and the core token is a known abbreviation."""
        last = closing_puncts[-1][1]
        (space, next_token) = self.slurp_token(last)
        restored = core_token[2] + '.'
        if token_is_abbreviation(restored):
            core_token = (core_token[0], core_token[1] + 1, restored)
            closing_puncts.pop(0)
        return (core_token, closing_puncts)


    def _split_punctuation(self, word):

        """Return a triple of opening punctuations, core token and closing
        punctuation. A core token can contain internal punctuation but
        token-initial and token-final punctuations are stripped off. If a token
        has punctuation characters only, then the core token wil be the empty
        string and the closing list will be empty."""

        opening_puncts = []
        closing_puncts = []
        core_token = word

        (off1, off2, tok) = word

        while True:
            if not tok:
                break
            found_punc = punctuation_pattern.search(tok[0])
            if found_punc:
                opening_puncts.append((off1, off1 + 1, tok[0]))
                core_token = (off1 + 1, off2, tok[1:])
                off1 += 1
                tok = tok[1:]
            else:
                break
    
        while True:
            if not tok:
                break
            found_punc = punctuation_pattern.search(tok[-1])
            if found_punc:
                closing_puncts.append((off2 - 1, off2, tok[-1]))
                core_token = (off1, off2 - 1, tok[:-1])
                off2 += -1
                tok = tok[:-1]
            else:
                break

        # need to reverse because the closing punctuations were added from the
        # end
        closing_puncts.reverse()
        return (opening_puncts,  core_token, closing_puncts)


    def _split_contractions(self):
        new_tokens = []
        for (puncts1, tok, puncts2) in self.tokens:
            new_tokens.append(self._split_contraction(puncts1, tok, puncts2))
        self.tokens = new_tokens

    def _split_contraction(self, puncts1, tok, puncts2):
        def split(tok, i):
            return [(tok[0], tok[0]+i, tok[2][:i]), (tok[0]+i, tok[1], tok[2][i:])]
        if "'" not in tok[2]:
            return (puncts1, [tok], puncts2)
        found_neg = contraction_pattern1.search(tok[2])
        if found_neg:
            idx = found_neg.start(2)
            return (puncts1, split(tok, idx), puncts2)
        found_pos = contraction_pattern2.search(tok[2])
        if found_pos:
            idx = found_pos.start(2) - 1
            return (puncts1, split(tok, idx), puncts2)
        return (puncts1, [tok], puncts2)

    def get_tokenized_as_xml(self):
        """Return the tokenized text as an XML string. Crappy way of printing
        XML, will only work for lex and s tags. Need to eventually use a method
        on TarsqiDocument (now there is a method on DocSource that probably
        needs to be moved."""
        lex_open_function = lambda lex: u"<lex begin='%s' end='%s'>" % (lex[0], lex[1])
        return self.get_tokenized(xml=True,
                                  s_open=u"<s>\n",
                                  s_close=u"</s>\n",
                                  lex_open=lex_open_function,
                                  lex_close=u"</lex>\n",
                                  lexindent=u"  ")
    
    def get_tokenized_as_string(self):
        """Return the tokenized text as a string where sentences are on one line
        and tokens are separated by spaces. Not that each sentence ends with a
        space because each token is followed by a space."""
        lex_open_function = (lambda lex: u'')
        return self.get_tokenized(xml=False,
                                  s_open=u'',
                                  s_close=u"\n",
                                  lex_open=lex_open_function,
                                  lex_close=u' ',
                                  lexindent=u'')


    def get_tokenized(self, xml, s_open, s_close, lex_open, lex_close, lexindent):
        
        """Return the tokenized text as a string."""

        self._set_tag_indexes()

        fh = StringIO()

        if xml:
            fh.write(u"<TOKENS>\n")

        (in_lex, in_sent, off) = (False, False, 0)

        for off in range(len(self.text) + 1):

            char = self.text[off] if off < len(self.text) else None
            closing_lex = self.closing_lexes.get(off)
            opening_lex = self.opening_lexes.get(off)
            closing_s = self.closing_sents.get(off)
            opening_s = self.opening_sents.get(off)

            if closing_lex:
                if not closing_s:
                    fh.write(lex_close)
                in_lex = False
            if closing_s:
                fh.write(s_close)
                in_sent = False
            if opening_s:
                fh.write(s_open)
                in_sent = True
            if opening_lex:
                indent = ''
                if in_sent:
                    indent = lexindent
                fh.write(indent + lex_open(opening_lex))
                in_lex = True

            if in_lex and char is not None:
                write_char = char
                if xml:
                    write_char = escape(char)
                fh.write(write_char)

        if xml:
            fh.write(u"</TOKENS>\n")

        return fh.getvalue()


    def _set_tag_indexes(self):
        """Populate dictionaries that stire tags on first and last offsets."""
        self.opening_lexes = {}
        self.closing_lexes = {}
        for l in self.lexes:
            self.opening_lexes[l[0]] = l
            self.closing_lexes[l[1]] = l
        self.opening_sents = {}
        self.closing_sents = {}
        for s in self.sentences:
            self.opening_sents[s[0]] = s
            self.closing_sents[s[1]] = s


class TokenizedText:

    """This class takes a list of sentences of the form (begin_offset, end_offset)
    and a list of tokens of the form (begin_offset, end_offset, text), and
    creates a list of elements. Each element can either be a TokenizedSentence
    or a TokenizedLex (the latter for a token outside a sentence tag)."""

    def __init__(self, sentences, tokenizer_lexes):
        self.sentences = []
        lexes = tokenizer_lexes[:]
        for s in sentences:
            (first, last) = s[0:2]
            # slurp in lexes that occur before the first sentence boundary, will
            # typically only occur for the very first sentence
            while lexes:
                lex = lexes[0]
                if lex[0] < first:
                    self.sentences.append(TokenizedLex(lex[0], lex[1], lex[2]))
                    lexes.pop(0)
                else:
                    break
            self.sentences.append(TokenizedSentence(first, last))
            while lexes:
                lex = lexes[0]
                if lex[0] >= first and lex[1] <= last:
                    self.sentences[-1].append(TokenizedLex(lex[0], lex[1], lex[2]))
                    lexes.pop(0)
                else:
                    break
        # put all remaining lexes into one sentence, only does something when
        # there are no sentences
        if lexes:
            (first, last) = (lexes[0][0], lexes[-1][1])
            self.sentences.append(TokenizedSentence(first, last))
            while lexes:
                lex = lexes[0]
                self.sentences[-1].append(TokenizedLex(lex[0], lex[1], lex[2]))
                lexes.pop(0)

    def as_string(self):
        str = u''
        for s in self.sentences:
            str += s.as_string()
        return str

    def as_vertical_string(self):
        str = ''
        for s in self.sentences:
            str += "<s>\n" + s.as_vertical_string()
        return str

    def as_pairs(self):
        """Return self as a list of pairs, where usually each pair contains a
        string and a TokenizedLex instance. Also inserts a ('<s>', None) for the
        beginning of each sentence.  This is intended to take tokenized text and
        prepare it for the TreeTagger (which does not recognize </s> tags."""
        objects = []
        for s in self.sentences:
            objects += [("<s>", None)] + s.as_pairs()
        return objects

    def print_as_string(self):
        for s in self.sentences:
            s.print_as_string()

    def print_as_xmlstring(self):
        print "<TOKENS>"
        for s in self.sentences:
            s.print_as_xmlstring()
        print "</TOKENS>"


class TokenizedSentence:

    def __init__(self, b, e):
        self.begin = b
        self.end = e
        self.tokens = []

    def append(self, item):
        self.tokens.append(item)

    def as_string(self):
        return u' '.join([t.text for t in self.tokens]) + u"\n"

    def as_vertical_string(self):
        return "\n".join([t.text for t in self.tokens]) + "\n"

    def as_pairs(self):
        return [(t.text, t) for t in self.tokens]

    def print_as_string(self):
        print ' '.join([t.text for t in self.tokens])

    def print_as_xmlstring(self):
        print '<s>'
        for t in self.tokens:
            t.print_as_xmlstring(indent='  ')
        print '</s>'


class TokenizedLex:

    def __init__(self, b, e, text):
        self.begin = b
        self.end = e
        self.text = text

    def __str__(self):
        return "TokenizedLex(%d,%d,'%s')" % (self.begin, self.end, self.text)

    def as_string(self, indent=''):
        return self.text

    def as_vertical_string(self, indent=''):
        return self.text + "\n"

    def as_pairs(self):
        return [(self.text, self)]

    def print_as_string(self, indent=''):
        print self.text

    def print_as_xmlstring(self, indent=''):
        print "%s<lex begin=\"%d\" end=\"%d\">%s</lex>" % \
              (indent, self.begin, self.end, escape(self.text))


if __name__ == '__main__':

    import sys, codecs
    from time import time

    in_file = sys.argv[1]
    t1 = time()
    tk = Tokenizer(codecs.open(in_file, encoding="utf-8").read())
    for i in range(1):
        text = tk.tokenize_text()
    # print tk.sentences
    # print tk.lexes
    print tk.get_tokenized_as_xml()
    print tk.get_tokenized_as_string()
    print "\nDONE, processing time was %.3f seconds\n" % (time() - t1)
