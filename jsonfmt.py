#!/usr/bin/env python

from __future__ import print_function

import json
import os
import sys

def touch(filename, mtime):
  with open(filename, 'a+'):
    pass
  os.utime(filename, (mtime, mtime))
  return 0

file = sys.argv[1]
print('Updating', file)

mtime = os.path.getmtime(file)

with open(file, 'rb') as f:
  json_data = json.load(f)

new_data = json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': '))
with open(file, 'wb') as f:
  f.write(new_data+"\n")

touch(file, mtime)

sys.exit(0)
