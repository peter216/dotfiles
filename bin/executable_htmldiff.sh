#!/bin/bash

FILE1=$1
FILE2=$2
PLAIN_DIFF_FILE=$3
HTML_DIFF_FILE=$3.html

diff -u $FILE1 $FILE2 > $PLAIN_DIFF_FILE

echo "<html><body><pre>" > $HTML_DIFF_FILE
awk '
/^[ ]/ {print "<span style=\"color:black\">" $0 "</span>"}
/^\+/ {print "<span style=\"color:green\">" $0 "</span>"}
/^\-/ {print "<span style=\"color:red\">" $0 "</span>"}
/^\@/ {print "<span style=\"color:blue\">" $0 "</span>"}
' $PLAIN_DIFF_FILE >> $HTML_DIFF_FILE
echo "</pre></body></html>" >> $HTML_DIFF_FILE

echo "Colored diff output is in $HTML_DIFF_FILE"
