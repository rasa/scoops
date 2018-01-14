#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" @todo add docstring """

# ### imports ###

from __future__ import (
    absolute_import,
    division,
    print_function  # ,
    #  unicode_literals
)

from jsoncomment import JsonComment
# from jsonschema import validate

import json
import os
import sys


def decode(s):
    if sys.version_info >= (3, 0):
        return s

    for encoding in 'utf-8-sig', 'utf-16':
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            continue
    return s.decode('latin-1')


def touch(filename, mtime):
    with open(filename, 'a+'):
        pass
    os.utime(filename, (mtime, mtime))
    return 0


file = sys.argv[1]
print('Updating', file)

mtime = os.path.getmtime(file)

with open(file, 'r') as f:
    jstr = f.read()
    jstr_no_bom = decode(jstr)

parser = JsonComment(json)
json_data = parser.loads(jstr_no_bom)

new_data = json.dumps(
    json_data, sort_keys=True, indent=4, separators=(',', ': '))
with open(file + '.tmp', 'wb') as f:
    new_data = new_data.encode('utf-8')
    new_data += b"\n"
    f.write(new_data)

if os.path.isfile(file + '.bak'):
    os.remove(file + '.bak')
os.rename(file, file + '.bak')
os.rename(file + '.tmp', file)

touch(file, mtime)

sys.exit(0)
