import argparse
import pprint
import sys
import random
from itertools import ifilter

pp = pprint.PrettyPrinter()

def parse_arguments():
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', action='store', type=int, choices=xrange(10000000), dest='lines', default='100000', help='number of sample lines to be extracted')
    parser.add_argument('-o', '--outfile', action='store', type=argparse.FileType('w'), dest='outfile', default=sys.stdout, help='file to write the extracted samples to')
    parser.add_argument('infile', action='store', type=argparse.FileType('r'), help='file from which to extract sample lines')
    return parser.parse_args()

def random_lines(total_lines, lines_wanted):
    random_numbers = set()
    for i in xrange(lines_wanted):
        rnum = random.randint(0, total_lines - 1)
        while rnum in random_numbers:
            rnum = random.randint(0, total_lines - 1)
        random_numbers.add(rnum)
    return random_numbers

args = parse_arguments()
lcount = sum(1 for line in args.infile)
print("{}".format(lcount))
rlines = random_lines(lcount,args.lines)
args.infile.seek(0)
for i in ifilter(lambda x: x[0] in rlines, enumerate(args.infile)):
    args.outfile.write(i[1])
args.infile.close()
args.outfile.close()
    
