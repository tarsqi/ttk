"""

Script to download issues from the TTK Github repository and turn them into HTML
pages.

To download the issues do the following

   $ python get_issues.py --download INTEGER_1 INTEGER_2

   Here, issues ranging from issue INTEGER_1 through INTEGER_2 qill be download,
   except for those issues that are closed. To include closed issues set the
   value of SKIP_CLOSED below to Falose. Issues are downloaded from GITHUB_DIR
   and put in JSON_DIR.

   You need to have some awareness on what issues to download since the Github
   API has a limit of 60 requests per hour.

To turn the downloaded JSON files into HTM files do the following:

   $ python get_issues.py --html

   This takes all issues in JSON_DIR and creates HTML files in HTML_DIR.

"""


from __future__ import absolute_import
import os, sys, json, pprint, re
from HTMLParser import HTMLParser


DEBUG = False
SKIP_CLOSED = False


GITHUB_DIR = 'https://api.github.com/repos/tarsqi/ttk/issues'
ISSUES_DIR = os.path.join('issues', 'json')
HTML_DIR = os.path.join('issues', 'html')


STYLE = """
<style>
body { margin: 5pt; }
p, td, body { font-size: 14pt; }
.header { color: darkblue; font-weight: bold; }
.description { margin-left: 5pt; padding: 5pt; border: thin dotted gray; background-color: #eee; }
.comments { margin-left: 5pt; padding-left: 5pt; border-left: thin dotted darkblue; }
.hide { color: #eee; }
</style>
"""

# expression for links in issues, only deals with links to other issues
LINK_EXPR = re.compile(r'https://github.com/tarsqi/ttk/issues/\d+')


class HTML_File(object):

    """Class to simplify creating html files for issues."""

    def __init__(self, fname):
        self.fname = fname
        self.fh = open(fname, 'w')
        self.write_lines(['<html>', '<head>', STYLE, '</head>', '<body>'])

    def write_lines(self, lines):
        for line in lines:
            self.fh.write(line + "\n")

    def finish(self):
        self.write_lines(['</body>', '</html>'])


class Issue(object):

    """Instances of this class store the various elements of an issue. Each
    issue comes in as an issue json file and a comments json file."""

    def __init__(self, issue_file, comments_file):
        print '>> reading', issue_file
        self.issue = read_json(issue_file)
        self.number = self.issue['number']
        self.title = self.issue['title']
        self.state = self.issue['state']
        self.user = self.issue['user']['login']
        self.body = self.issue['body']
        self.created_at = self.issue['created_at']
        self.fname = os.path.join(HTML_DIR, "issue-%03d.html" % self.number)
        self.comments = [Comment(c) for c in read_json(comments_file)]
        
    def __str__(self):
        return "<Issue %d '%s'>" % (self.number, self.title)

    def __cmp__(self, other):
        return cmp(self.number, other.number)
    
    def write(self):
        html_file = HTML_File(self.fname)
        html_file.write_lines([
                "<h2>Issue %s - %s</h2>" % (self.number, self.title),
                "<p class=header>%s - %s</p>" % (self.user, self.created_at),
                "<p class=description>%s</p>" % massage_text(self.body)])
        if self.comments:
            html_file.write_lines(["<div class=comments>"])
            for comment in self.comments:
                html_file.write_lines([
                        "<p class=header>%s - %s" % (comment.user, comment.created_at),
                        '<p class=description>', comment.body, '</p>'])
            html_file.write_lines(['</div>'])
        html_file.finish()


class Comment(object):

    """Models the relevant aspect of a comment."""

    def __init__(self, json_object):
        self.comment = json_object
        self.user = self.comment['user']['login']
        self.body = self.comment['body']
        self.created_at = self.comment['created_at']
        self.updated_at = self.comment['updated_at']


def read_json(fname):
    """Return the json object stored in a file."""
    with open(os.path.join(ISSUES_DIR, fname)) as json_data:
        return json.load(json_data)


def massage_text(text):
    """Replace some element of the text for display purposes."""
    # could also do some other things like replacing ``` with <pre> or </pre>
    # and replacing list with items like "- [x]" with <li> and checkmarks, too
    # much work for little return though
    text = add_links(text)
    text = text.replace("\n", '<br/>')
    text = text.replace("[ ]", '[<span class=hide>x</span>]')
    return text


def add_links(text):
    """Replace a link of the form https://github.com/tarsqi/ttk/issues/12 with a
    local link to an html file for the issue linked to."""
    current_position = 0
    new_text = ''
    while True:
        link_begin = text.find('https://', current_position)
        if link_begin == -1:
            new_text += text[current_position:]
            break
        new_text += text[current_position:link_begin]
        link = slurp_link(text, link_begin)
        if link is not None:
            link_end = link_begin + len(link)
            issue_number = link.split('/')[-1]
            new_text += "<a href=issue-%03d.html>%s</a>" % (int(issue_number), link)
        else:
            link_end = link_begin + 1
        if DEBUG:
            print "   [%s-%s-%s] [%s]" % (current_position, link_begin, link_end, link)
        current_position = link_end
    return new_text


def slurp_link(text, link_begin):
    """Consume and return the link in the text, starting at position
    link_begin."""
    result = LINK_EXPR.match(text[link_begin:])
    return result.group() if result else None


def print_index(issues):
    index_file = HTML_File(os.path.join(HTML_DIR, 'index.html'))
    index_file.write_lines([
            '<h2>Issues</h2>',
            '<table cellpadding=5 cellspacing=0 border=1>'])
    for issue in issues:
        index_file.write_lines([
                "<tr>",
                "  <td align=right>%s</td>" % issue.number,
                "  <td>%s</td>" % issue.state,
                "  <td><a href=issue-%03d.html>%s</a></td>" % (issue.number, issue.title),
                "</tr>"])
    index_file.write_lines(['</table>'])
    index_file.finish()


def download_issues(i, j, skip_closed=True):
    closed = closed_issues() if skip_closed else []
    print closed
    i, j = int(i), int(j)
    for i in range(i, j+1):
        if skip_closed and i in closed:
            continue
        print"Getting %s/%d" % (GITHUB_DIR, i)
        args = (GITHUB_DIR, i, ISSUES_DIR, i)
        command1 = "curl -sS %s/%s > %s/issue-%s.json" % args
        command2 = "curl -sS %s/%s/comments > %s/issue-%s-comments.json" % args
        for c in (command1, command2):
            if DEBUG:
                print '  ', c
            # os.system(c)


def process_issues():
    json_files = [f for f in os.listdir(ISSUES_DIR) if f.startswith('issue-')]
    issues = []
    while json_files:
        comments_file = json_files.pop(0)
        issue_file = json_files.pop(0)
        issue = Issue(issue_file, comments_file)
        issues.append(issue)
        issues.sort()
    for issue in issues:
        print issue
        issue.write()
    print_index(issues)
    print "Done, results are in %s/index.html" % HTML_DIR

        
def closed_issues():
    # instantiate the parser and fed it some HTML
    parser = IndexParser()
    IndexParser.current_tag = None
    IndexParser.issue = None
    IndexParser.open_issues = []
    IndexParser.closed_issues = []
    parser.feed(open(os.path.join(HTML_DIR, 'index.html')).read())
    #print 'OPEN', IndexParser.open_issues
    #print 'CLOSED', IndexParser.closed_issues
    return set(IndexParser.closed_issues)


class IndexParser(HTMLParser):

    """Parse the index and build two lists and store them in class variables
    named open_issues and closed_issues."""

    # could not use an __init__() method to set instance variables, using class
    # variables instead
    current_tag = None
    issue = None
    open_issues = []
    closed_issues = []

    def handle_starttag(self, tag, attrs):
        #print "<%s>" % tag
        IndexParser.current_tag = tag

    def handle_endtag(self, tag):
        #print "</%s>" % tag
        if tag == 'tr':
            IndexParser.current_tag = None
            IndexParser.issue = None

    def handle_data(self, data):
        #print IndexParser.current_tag, '-',  IndexParser.issue, '-', data.strip()
        if IndexParser.current_tag == 'td':
            if data.isdigit():
                IndexParser.issue = data
            elif data in ('open', 'closed'):
                #print "issue %s is %s" % (IndexParser.issue, data)
                tmp = IndexParser.open_issues if data == 'open' else IndexParser.closed_issues
                tmp.append(int(IndexParser.issue))



if __name__ == '__main__':

    if sys.argv[1] == '--download':
        download_issues(sys.argv[2], sys.argv[3], SKIP_CLOSED)
    
    elif sys.argv[1] == '--html':
        process_issues()
