#!/usr/bin/python
import sys
import re
from lxml import html, etree
import pprint
from bs4 import BeautifulSoup
import glob
import shutil
import os
from os.path import basename, exists

# LSB URLs of interest

url_libc = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-a.html#APP-LIBC"
url_libm = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-libm.html"
url_libcrypt = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-libcrypt.html"
url_libpthread = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-libpthread.html"
url_libdl = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-libdl.html"
url_librt = "http://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic/app-librt.html"

# TODO: reimplement using bs4
def parse(tree):
    return_set = set()
    # check all tables
    for row in tree.xpath('//table[@class="CALSTABLE"]/tbody/tr'):
        # check all columns
        for column in row.xpath('./td'):
            func_name = column.text.strip()
            func_name = re.sub(r'(.+)\(.*\)',r'\1', func_name)
            return_set.add(func_name)
    return return_set

# extract function names

parser = etree.HTMLParser()
libc_tree = etree.parse(url_libc,parser)
libm_tree = etree.parse(url_libm,parser)
libpthread_tree = etree.parse(url_libpthread,parser)
libdl_tree = etree.parse(url_libdl,parser)
librt_tree = etree.parse(url_librt,parser)
libcrypt_tree = etree.parse(url_libcrypt,parser)

libc = parse(libc_tree)
libm = parse(libm_tree)
libpthread = parse(libpthread_tree)
libdl = parse(libdl_tree)
librt = parse(librt_tree)
libcrypt = parse(libcrypt_tree)

#pp = pprint.PrettyPrinter()
#pp.pprint(libpthread)

if not exists("libc"):
    os.mkdir("libc")
if not exists("libm"):
    os.mkdir("libm")
if not exists("libpthread"):
    os.mkdir("libpthread")
if not exists("libdl"):
    os.mkdir("libdl")
if not exists("librt"):
    os.mkdir("librt")
if not exists("libcrypt"):
    os.mkdir("libcrypt")
if not exists("default"):
    os.mkdir("default")

for f in glob.glob("*.tcs"):
    function_name = re.sub(r'^(\w+)-b.*$',r'\1',re.sub(r'\.tcs','',basename(f)))
    copy_flag = 0
    if function_name in libc:
        shutil.copy2(f,"libc")
        copy_flag += 1
    if function_name in libm:
        shutil.copy2(f,"libm")
        copy_flag += 1
    if function_name in libpthread:
        shutil.copy2(f,"libpthread")
        copy_flag += 1
    if function_name in libdl:
        shutil.copy2(f,"libdl")
        copy_flag += 1
    if function_name in librt:
        shutil.copy2(f,"librt")
        copy_flag += 1
    if function_name in libcrypt:
        shutil.copy2(f,"libcrypt")
        copy_flag += 1
    if copy_flag == 0:
        shutil.copy2(f,"default")
    if copy_flag > 1:
        print("File copied more than once: "+basename(f))
