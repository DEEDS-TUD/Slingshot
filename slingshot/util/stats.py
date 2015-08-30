#!/usr/bin/python
import re
from lxml import html, etree

def parse(tree):
    m_posix2 = re.compile("(?:.*)SUSv2(?:.*)")
    m_posix3 = re.compile("(?:.*)SUSv3(?:.*)")
    m_posix4 = re.compile("(?:.*)SUSv4(?:.*)")
    m_lsb = re.compile("(?:.*)LSB(?:.*)")
    m_rpc = re.compile("(?:.*)RPC & XDR(?:.*)")
    m_lfs = re.compile("(?:.*)LFS(?:.*)")
    m_svid3 = re.compile("(?:.*)SVID.3(?:.*)")
    m_svid4 = re.compile("(?:.*)SVID.4(?:.*)")
    pos2 = set()
    pos3 = set()
    pos4 = set()
    lsb = set()
    lfs = set()
    rpc = set()
    svid3 = set()
    svid4 = set()
    # check all tables
    for row in tree.xpath('//table[@class="CALSTABLE"]/tbody/tr'):
        # check all columns
        for column in row.xpath('./td'):
            func_name = column.text.strip()
            func_name = re.sub(r'^(?:_)*','', func_name)
            # The link text defines which standard is used
            for link in column.xpath('./a'):
                # if we get a match add function to appropriate set
                m = m_posix2.match(link.text)
                if m:
                    pos2.add(func_name)

                m = m_posix3.match(link.text)
                if m:
                    pos3.add(func_name)

                m = m_posix4.match(link.text)
                if m:
                    pos4.add(func_name)

                m = m_lsb.match(link.text)
                if m:
                    lsb.add(func_name)

                m = m_rpc.match(link.text)
                if m:
                    rpc.add(func_name)

                m = m_lfs.match(link.text)
                if m:
                    lfs.add(func_name)

                m = m_svid3.match(link.text)
                if m:
                    svid3.add(func_name)

                m = m_svid4.match(link.text)
                if m:
                    svid4.add(func_name)

    return {'pos2' : pos2, 'pos3' : pos3, 'pos4' : pos4, 'lsb' : lsb, 'lfs' : lfs, 'rpc' : rpc, 'svid3' : svid3, 'svid4' : svid4}

def get_ballista_functions():
    ballista = set()
    # read in ballista functions:
    try:
        fd = open("functions_all")
        for line in fd:
            line = line.rstrip('\n')
            #print line
            ballista.add(line)
        fd.close()
    except IOError as e:
        print("({})".format(e))
        sys.exit("Could not read ballista functions")
    return ballista

def get_all(key):
    return libc[key] | libm[key] | libpthread[key] | libdl[key] | librt[key] | libcrypt[key]

parser = etree.HTMLParser()
libc_tree = etree.parse("Interfaces_for_libc.html",parser)
libm_tree = etree.parse("Interfaces_for_libm.html",parser)
libpthread_tree = etree.parse("Interfaces_for_libpthread.html",parser)
libdl_tree = etree.parse("Interfaces_for_libdl.html",parser)
librt_tree = etree.parse("Interfaces_for_librt.html",parser)
libcrypt_tree = etree.parse("Interfaces_for_libcrypt.html",parser)

libc = parse(libc_tree)
libm = parse(libm_tree)
libpthread = parse(libpthread_tree)
libdl = parse(libdl_tree)
librt = parse(librt_tree)
libcrypt = parse(libcrypt_tree)

ballista = get_ballista_functions()


# set of all posix functions
all_posix = get_all('pos2') | get_all('pos3') | get_all('pos4')

# set of all functions
all_functions = all_posix | get_all('lsb') | get_all('rpc') | get_all('lfs') | get_all('svid3') | get_all('svid4')

print('Of {0} functions in the LSB there are {1} POSIX functions'.format(len(all_functions),  len(all_posix)))

print('They are distributed through the libc, libm, libpthread, libdl, librt and libcrypt library as follows:')

print('\t libc: {}'.format(len(libc['pos2'] | libc['pos3'] |libc['pos4'])))
print('\t libm: {}'.format(len(libm['pos2'] | libm['pos3'] |libm['pos4'])))
print('\t libpthread: {}'.format(len(libpthread['pos2'] | libpthread['pos3'] |libpthread['pos4'])))
print('\t libdl: {}'.format(len(libdl['pos2'] | libdl['pos3'] |libdl['pos4'])))
print('\t librt: {}'.format(len(librt['pos2'] | librt['pos3'] |librt['pos4'])))
print('\t libcrypt: {}'.format(len(libcrypt['pos2'] | libcrypt['pos3'] |libcrypt['pos4'])))

print('POSIX2 has {0}, POSIX3 has {1} and POSIX4 has {2} function-definitions'.format(len(get_all('pos2')), len(get_all('pos3')), len(get_all('pos4'))))



print('')
print('Ballista includes {} functions:'.format(len(ballista)))
print('\t {0} POSIX2 functions are used in the LSB'.format(len(ballista.intersection(get_all('pos2')))))
print('\t {0} POSIX3 functions are used in the LSB'.format(len(ballista.intersection(get_all('pos3')))))
print('\t {0} POSIX4 functions are used in the LSB'.format(len(ballista.intersection(get_all('pos4')))))

print('\nThe unused {0} functions are:\n {1}'.format(len(ballista.difference(all_posix)),ballista.difference(all_posix)))

print('\n{0} functions are defined in Ballista but not in the LSB:\n {1}'.format(len(ballista.difference(all_functions)), ballista.difference(all_functions)))
