#!/usr/bin/env python
import sys
import re

def main():
    file_name = sys.argv[1:][0]

    blocks = { 'commit ': '<commit>\n</commit>', 'cleanup':
    '<cleanup>\n</cleanup'}

    with open(file_name, 'r') as f:
        all_lines = f.read()

    for block_name, block_pattern in blocks.iteritems():
        if not has_empty_block(all_lines, block_pattern):
            print("{} is not empty! {}".format(block_name, file_name))


def has_empty_block(file_as_string, block_pattern):
    match = re.findall(block_pattern, file_as_string)
    if match:
        return True
    else:
        return False


if __name__ == '__main__':
    main()
