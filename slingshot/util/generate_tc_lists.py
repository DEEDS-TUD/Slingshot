#!/usr/bin/python

import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

calltable = BeautifulSoup(open("../bin/terror_call_table.xml"),"xml")
functions = calltable.findAll('function')
parameters = set(calltable.findAll('param'))
function_to_fsig = defaultdict(list)
function_parameters = defaultdict(list)
for f in functions:
    plist =[]
    fsig = f.find('name').get_text().strip()
    for p in f('param'):
        plist.append(p.get_text().strip())
        fsig = fsig + " " + p.get_text().strip()
    function_parameters[fsig] = plist
    function_to_fsig[f.find('name').get_text().strip()].append(fsig)
parameter_parent = dict()
parameter_dials = defaultdict(list)

def evaluate_tpl(dtype):
    dtype = dtype.strip()
    tplsoup = BeautifulSoup(open(dtype+"_dummy.xml"),"xml")
    namelist = tplsoup('name')
    for name in namelist:
        name_string = name.get_text().strip()
        if name_string != dtype:
            if name_string not in parameter_dials[dtype]:
                parameter_dials[dtype].append(name_string)
    parent = tplsoup.find('parent')
    parent_string = parent.get_text().strip()
    if parent_string != 'paramAccess':
        parameter_parent[dtype] = parent_string
        if parent_string in parameter_dials:
            return
        else:
            evaluate_tpl(parent.get_text())
    return

for p in parameters:
    evaluate_tpl(p.get_text().strip())

def add_dials(line,t_list):
    if not t_list:
        line = line + "\n"
        tcs_file.write(line)
        return
    item = t_list[0]
    for d in parameter_dials[item]:
        t_list.pop(0)
        add_dials(line+"; "+item+" "+d,t_list)
        t_list.insert(0,item)
    if item in parameter_parent:
        t_list.pop(0)
        t_list.insert(0,parameter_parent[item])
        add_dials(line,t_list)
        t_list.pop(0)
        t_list.insert(0,item)
    else:
        return

for f in functions:
    line = f.find('name').get_text().strip()
    print("Processing function "+function_to_fsig[line][0])
    with open(re.sub(r'\s',r'-',function_to_fsig[line][0])+".tcs","w") as tcs_file:
        add_dials(function_to_fsig[line][0],function_parameters[function_to_fsig[f.find('name').get_text().strip()][0]])
        function_to_fsig[f.find('name').get_text().strip()].pop(0)
        

