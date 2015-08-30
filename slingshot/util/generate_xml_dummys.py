#! /usr/bin/python

import re
import glob
from collections import defaultdict
from bs4 import BeautifulSoup
from os.path import basename
import pprint

pp = pprint.PrettyPrinter()

parent_def = re.compile(r'^parent\s+(\w+)\s*;\s*$')
dial_def = re.compile(r'^\s*enum_dial\s+([A-Z_]+)\s*:')
#dials_start = re.compile(r'^\s*enum_dial\s*\w+')
dials_single_row = re.compile(r'^\s*enum_dial\s\w+\s*:\s*(\w+\s*(,\s*\w+)*)\s*;\s*(//.*)?$')
dials_multi_row_start = re.compile(r'^\s*enum_dial\s\w+\s*:\s*((\w+\s*,\s*)*)(//.*)?$')
dials_multi_row_continued = re.compile(r'^\s*(\w+\s*,(\s*\w+\s*,)*)\s*(//.*)?$')
dials_multi_row_end = re.compile(r'^\s*(\w+\s*(,\s*\w+\s*)*);\s*(//.*)?$')
empty_row = re.compile(r'^\s*$')
comment_row = re.compile(r'^\s*//.*$')

def extractDialGroup(f,l):
    dial_group = []
    # all dials in a single row
    if dials_single_row.match(l):
        print("File "+f.name+": single row dial definition matched: "+l)
        dial_group = dials_single_row.sub(r'\1',l).split(',')
    # dials over several rows
    else:
        print("File "+f.name+": multi row dial definition matched: "+l)
        try:
            dial_group.extend(dials_multi_row_start.sub(r'\1',l).split(','))
        except re.error as err:
            print("Regex error: probably tried to extract non-existing dial from first row of multi-row dial definition")
        l = f.readline()
        while not (dials_multi_row_end.match(l)):
            dial_group.extend(dials_multi_row_continued.sub(r'\1',l).split(','))
            l = f.readline()
        dial_group.extend(dials_multi_row_end.sub(r'\1',l).split(','))
    # post processing
    for index, d in enumerate(dial_group):
        dial_group[index] = d.strip()
    for d in dial_group:
        if d == '':
            dial_group.remove(d)
    return dial_group

def extractDialGroups(f,l):
    groups = defaultdict(list)
    while dials_single_row.match(l) or dials_multi_row_start.match(l):
        dial_name = dial_def.sub(r'\1',l)
        groups[dial_name] = extractDialGroup(f,l)
        groups['dialgroup_names'].append(dial_name)
        l = f.readline()
        while empty_row.match(l) or comment_row.match(l):
            l = f.readline()
    return groups

def dial_combinations(d,dstring,soup):
    if not d['dialgroup_names']:
        setup_tag = soup.new_tag("setup")
        n_tag = soup.new_tag("name")
        n_tag.string = "("+dstring.strip()+")"
        setup_tag.append(n_tag)
        setup_tag.append(soup.new_tag("code"))
        soup.access.append(setup_tag)
        return
    dgroup = d['dialgroup_names'].pop(0)
    for dial in d[dgroup]:
        dial_combinations(d,dstring+" "+dial,soup)
    d['dialgroup_names'].insert(0,dgroup)
    return    
    

def writeXml(tpl_fname,p,d,xmlf):
    dummy_soup = BeautifulSoup(features="xml")
    dummy_soup.append(dummy_soup.new_tag("dt"))
    name_tag = dummy_soup.new_tag("name")
    name_tag.string = re.sub(r'\.tpl',r'',tpl_fname)
    dummy_soup.dt.append(name_tag)
    parent_tag = dummy_soup.new_tag("parent")
    parent_tag.string = p
    dummy_soup.dt.append(parent_tag)
    dummy_soup.dt.append(dummy_soup.new_tag("dt_type"))
    dummy_soup.dt.append(dummy_soup.new_tag("include"))
    dummy_soup.dt.append(dummy_soup.new_tag("defines"))
    dummy_soup.dt.append(dummy_soup.new_tag("access"))
    dummy_soup.dt.append(dummy_soup.new_tag("commit"))
    dummy_soup.dt.append(dummy_soup.new_tag("cleanup"))
    
    dial_combinations(d,"",dummy_soup)
    
    xmlf.write(dummy_soup.prettify())
    return

for f in glob.glob("../../../ballista/templates/*.tpl"):
#for f in glob.glob("*.tpl"):
    print("Processing "+basename(f))
    parent = ""
    dial_groups = defaultdict(list)
    tpl_file = open(f)
    line = tpl_file.readline()
    while line:
        # get data type parent
        if parent_def.match(line):
            parent = parent_def.sub(r'\1',line)
        # get dials
        if dials_single_row.match(line) or dials_multi_row_start.match(line):
            dial_groups = extractDialGroups(tpl_file,line)
            break
        line = tpl_file.readline()
    tpl_file.close()
    # write dummy xml file
    with open(re.sub(r'\.tpl',r'',basename(f))+"_dummy.xml","w") as xml_file:
        writeXml(basename(f),parent,dial_groups,xml_file)
        print("File "+xml_file.name+" written")
