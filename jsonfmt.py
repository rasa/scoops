#!/usr/bin/env python

from __future__ import print_function
from jsoncomment import JsonComment
from jsonschema import validate

import json
import os
import sys

if sys.version_info >= (3,0):
    sys.exit("Sorry, this script has only been tested with Python 2.x")

def decode(s):
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
    jstr = f.read(os.path.getsize(file))
    jstr_no_bom = decode(jstr)

parser = JsonComment(json)
json_data = parser.loads(jstr_no_bom)

new_data = json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': '))
with open(file + '.tmp', 'w') as f:
  f.write(new_data+"\n")

if os.path.isfile(file + '.bak'):
    os.remove(file + '.bak')
os.rename(file, file + '.bak')
os.rename(file + '.tmp', file)

touch(file, mtime)

sys.exit(0)
