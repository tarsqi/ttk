# Collect the issues from GitHub and store them locally as JSON files. To run it
# you need to give a range of the issues to download, so the following would get
# issues from 2 up to and including 9:
#
#     $ sh get_issues.sh 2 9
#
# Do not run this willy-nilly because there is a limit to how many requests the
# API takes and that limit seems to be about 60 per hour.

# TODO: would like to merge this into get_issues.py and then add a flag so that
# only open issues are downloaded

mkdir issues
mkdir issues/json

GH_ISSUES_DIR=https://api.github.com/repos/tarsqi/ttk/issues

for i in $(eval echo {$1..$2});
do
    echo "\nGetting" $GH_ISSUES_DIR/$i
    echo "   curl -sS $GH_ISSUES_DIR/$i > issues/json/issue-$i.json"
    echo "   curl -sS $GH_ISSUES_DIR/$i/comments > issues/json/issue-$i-comments.json"
    #curl -sS $GH_ISSUES_DIR/$i > issues/json/issue-$i.json
    #curl -sS $GH_ISSUES_DIR/$i/comments > issues/json/issue-$i-comments.json
done
