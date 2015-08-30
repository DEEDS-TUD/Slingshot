#!/usr/bin/python

import glob
from collections import defaultdict

filesizes = {}
counter = 0
processed = set()
mfiles = defaultdict(list)

def linescount(ifile):
    lcounter = 0
    tcs_file = open(ifile)
    for line in open(ifile): lcounter += 1
    tcs_file.close()
    return lcounter

# create dict of file names and line counts
for f in glob.glob("*.tcs"):
    lc = linescount(f)
    if lc < 100000:
        filesizes[f] = linescount(f)

# create merge file 'buckets'
for t in sorted(filesizes, key=lambda x: filesizes[x], reverse=True):
    print("Processing {0}: {1}".format(t,filesizes[t]))
    # skip processed files
    if t in processed: continue
    # if this is the first merge file, create an entry in the dict
    # the first list element is the cumulated line count
    if not mfiles:
        print("mfiles is empty")
        mfiles["merged_tcs{0}.tcs".format(counter)].append(filesizes[t])
        mfiles["merged_tcs{0}.tcs".format(counter)].append(t)
        processed.add(t)
        counter += 1
        continue;
    # check if the current file fits any existing bucket of merge files; if so, add it
    for m in mfiles.iterkeys():
        if mfiles[m][0] > 100000 - filesizes[t]: continue
        print("Adding {0} to bucket {1}.".format(t,m))
        mfiles[m][0] += filesizes[t]
        mfiles[m].append(t)
        processed.add(t)
        break
    if t in processed: continue # only if no bucket was found, create a new dict entry
    print("No bucket found for {}. Creating new bucket.".format(t))
    mfiles["merged_tcs{0}.tcs".format(counter)].append(filesizes[t])
    mfiles["merged_tcs{0}.tcs".format(counter)].append(t)
    processed.add(t)
    counter += 1

# create merge files from buckets
for m in mfiles.iterkeys():
    print("Writing {}".format(m))
    flist = mfiles[m]
    flist.pop(0)
    mergefile = open(m, "w")
    for f in flist:
        tmpfile = open(f)
        mergefile.write(tmpfile.read())
        tmpfile.close()
    mergefile.close()

