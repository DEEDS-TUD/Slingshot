#! /usr/bin/python

import re
import glob
from collections import defaultdict
from bs4 import BeautifulSoup, CData
from os.path import basename
import pprint

pp = pprint.PrettyPrinter()

parent_def = re.compile(r'^parent\s+(\w+)\s*;\s*$')
dial_def = re.compile(r'^\s*enum_dial\s+([A-Z_]+)\s*:.*$')
#dials_start = re.compile(r'^\s*enum_dial\s*\w+')
dials_single_row = re.compile(r'^\s*enum_dial\s\w+\s*:\s*(\w+\s*(,\s*\w+)*)\s*;\s*(//.*)?$')
dials_multi_row_start = re.compile(r'^\s*enum_dial\s\w+\s*:\s*((\w+\s*,\s*)*)(//.*)?$')
dials_multi_row_continued = re.compile(r'^\s*(\w+\s*,(\s*\w+\s*,)*)\s*(//.*)?$')
dials_multi_row_end = re.compile(r'^\s*(\w+\s*(,\s*\w+\s*)*);\s*(//.*)?$')
empty_row = re.compile(r'^\s*$')
comment_row = re.compile(r'^\s*//.*$')
name_row = re.compile(r'^name\s+(\w+\**)\s+\w+;\s*(//.*)?$')
includes_start_row = re.compile(r'^\s*includes\s*(//.*)?$')
defines_start_row = re.compile(r'^\s*global_defines\s*(//.*)?$')
access_start_row = re.compile(r'^\s*access\s*(//.*)?$')
commit_start_row = re.compile(r'^\s*commit\s*(//.*)?$')
cleanup_start_row = re.compile(r'^\s*cleanup\s*(//.*)?$')
blockdef_start = re.compile(r'^\[\s*(//.*)?$')
blockdef_end = re.compile(r'^\]\s*(//.*)?$')
block_start = re.compile(r'^\{\s*(//.*)?$')
#block_start_comment = re.compile(r'^\{\s*(//.*)$')
block_end = re.compile(r'^\}\s*(//.*)?$')
dial_block_dials = re.compile(r'^\s{2}(\w+(\s*,\s*\w+)*)\s*(//.*)?$')
dial_block_start = re.compile(r'^\s{2}\{\s*(//.*)?$')
#dial_block_start_comment = re.compile(r'^\s{2}\{\s*(//.*)$')
dial_block_end = re.compile(r'^\s{2}\}\s*(//.*)?$')

def extractDialGroup(f,l):
    dial_group = []
    # all dials in a single row
    if dials_single_row.match(l):
        dial_group = dials_single_row.sub(r'\1',l).split(',')
    # dials over several rows
    else:
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
        dial_name = dial_def.sub(r'\1',l).strip()
        groups[dial_name] = extractDialGroup(f,l)
        groups['dialgroup_names'].append(dial_name)
        l = f.readline()
        while empty_row.match(l) or comment_row.match(l):
            l = f.readline()
    return groups

def getCodeBlock(f,l):
    codeblock = ""
    # if block_start_comment.match(l):
    #     codeblock += block_start_comment.sub(r'\1',l)
    #     print("Start comment matched: "+codeblock)
    l = f.readline() # skip the block starting bracket
    while not block_end.match(l):
        codeblock += l
        l = f.readline()
    return codeblock

def getDialCodeBlock(f,l):
    codeblock = ""
    while not dial_block_start.match(l):
        l = f.readline()
    # if block_start_comment.match(l):
    #     codeblock += block_start_comment.sub(r'\1',l)
    #     print("Start comment matched: "+codeblock)
    l = f.readline() # skip the block starting bracket
    while not dial_block_end.match(l):
        codeblock += l
        l = f.readline()
    return codeblock
    
def extractBlocks(f,l,dg):
    blocks = []
    while not blockdef_end.match(l):
        # unlabeled blocks
        if block_start.match(l):
            blocks.append(['',getCodeBlock(f,l)])
        # labeled blocks
        elif dial_block_dials.match(l):
            dials = dial_block_dials.sub(r'\1',l)
            dlist = dials.split(',')
            known_dials = [item for dglist in dg.values() for item in dglist]
            illegal_dial = 0
            for d in dlist:
                illegal_dial = (d.strip() not in known_dials)
                if illegal_dial:
                    break
            if illegal_dial:
                print("Illegal dial label detected: "+l)
                l = f.readline()
                if block_start.match(l):
                    print("Skipping the following block...")
                    l = f.readline()
                continue
            else:
                 blocks.append([dials,getDialCodeBlock(f,l)])
        l = f.readline()
    return blocks

def blockTag(block,soup):
    block_tag = soup.new_tag("block")
    if block[0] != '':
        block_tag['dials'] = block[0]
    block_tag.append(CData(block[1].strip()))
    return block_tag

def writeXml(data,xmlf):
    soup = BeautifulSoup(features="xml")
    soup.append(soup.new_tag("dt"))

    # name
    name_tag = soup.new_tag("name")
    soup.dt.append(name_tag)
    name_tag.string = data['name']

    # parent type
    parent_tag = soup.new_tag("parent")
    soup.dt.append(parent_tag)
    parent_tag.string = data['ptype']

    # C type
    type_tag = soup.new_tag("dt_type")
    soup.dt.append(type_tag)
    type_tag.string = data['ctype']

    # dial-groups
    dial_group_tag = soup.new_tag("dial_groups")
    soup.dt.append(dial_group_tag)
    for group_name, dials in data['dial_groups'].items():
        if group_name == 'dialgroup_names':
            dial_group_tag['order'] = ';'.join(dials)
            continue
        group_tag = soup.new_tag("group")
        group_tag['name'] = group_name
        for dial in dials:
            dial_tag = soup.new_tag("dial")
            dial_tag.string = dial
            group_tag.append(dial_tag)
        dial_group_tag.append(group_tag)



    # includes
    include_tag = soup.new_tag("include")
    soup.dt.append(include_tag)
    for block in data['includes']:
        include_tag.append(blockTag(block,soup))
    
    # defines
    def_tag = soup.new_tag("defines")
    soup.dt.append(def_tag)
    for block in data['defs']:
        def_tag.append(blockTag(block,soup))

    # access blocks
    access_tag = soup.new_tag("access")
    soup.dt.append(access_tag)
    for block in data['ablocks']:
        access_tag.append(blockTag(block,soup))

    # commit blocks
    commit_tag = soup.new_tag("commit")
    soup.dt.append(commit_tag)
    for block in data['coblocks']:
        commit_tag.append(blockTag(block,soup))

    # cleanup blocks
    cleanup_tag = soup.new_tag("cleanup")
    soup.dt.append(cleanup_tag)
    for block in data['clblocks']:
        cleanup_tag.append(blockTag(block,soup))
    
    xmlf.write(soup.prettify(formatter=None))
    return

for f in glob.glob("../../../ballista/templates/*.tpl"):
#for f in glob.glob("*.tpl"):
    print("Processing "+basename(f))
    dial_groups = defaultdict(list)
    tpl_file = open(f)
    line = tpl_file.readline()
    while line:
        # ignore comment lines
        if comment_row.match(line):
            line = tpl_file.readline()
            continue
        # get C type
        if name_row.match(line):
            ctype = name_row.sub(r'\1',line)
        # get data type parent
        if parent_def.match(line):
            parent = parent_def.sub(r'\1',line)
        # TODO: get includes
        if includes_start_row.match(line):
             includes = extractBlocks(tpl_file,line,dial_groups)
        # TODO: get global defines
        if defines_start_row.match(line):
            defines = extractBlocks(tpl_file,line,dial_groups)
        # get dials
        if dials_single_row.match(line) or dials_multi_row_start.match(line):
            dial_groups = extractDialGroups(tpl_file,line)
        # get access blocks
        if access_start_row.match(line):
            access_blocks = extractBlocks(tpl_file,line,dial_groups)
        # get commit blocks
        if commit_start_row.match(line):
            commit_blocks = extractBlocks(tpl_file,line,dial_groups)
        # get cleanup blocks
        if cleanup_start_row.match(line):
            cleanup_blocks = extractBlocks(tpl_file,line,dial_groups)
        line = tpl_file.readline()
    tpl_file.close()
    tpl_data = {'name': re.sub(r'\.tpl',r'',basename(f)), 'ptype': parent, 'ctype': ctype, 'includes': includes, 'defs': defines, 'ablocks': access_blocks, 'coblocks': commit_blocks, 'clblocks': cleanup_blocks, 'dial_groups': dial_groups}
    #pp.pprint(tpl_data)
    # write xml file
    with open(re.sub(r'\.tpl',r'',basename(f))+".xml","w") as xml_file:
        writeXml(tpl_data,xml_file)
        print("File "+xml_file.name+" written")
