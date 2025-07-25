#!/usr/bin/awk -f

B
BEGIN {
    print "["
    first = 1
}
/^---$/ {
    if (!first) print "  },"
    first = 0
    next
}
/^Name:/ {
    print "  {"
    print "    \"Name\": \"" substr($0, 7) "\","
    next
}
/^Version:/ {
    print "    \"Version\": \"" substr($0, 10) "\","
    next
}
/^Location:/ {
    print "    \"Location\": \"" substr($0, 11) "\","
    next
}
/^Requires:/ {
    req = substr($0, 10)
    gsub(/, */, "\", \"", req)
    print "    \"Requires\": [" (req ? "\"" req "\"" : "") "],"
    next
}
/^Required-by:/ {
    reqby = substr($0, 14)
    gsub(/, */, "\", \"", reqby)
    print "    \"Required-by\": [" (reqby ? "\"" reqby "\"" : "") "]"
    next
}
END {
    print "  }"
    print "]"
}
