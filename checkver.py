#!/usr/bin/env python

from __future__ import print_function

import fnmatch
import json
import re
import os
import sys

specs = sys.argv
specs.pop(0)

if len(specs) == 0:
    specs = ['*.json']

for file in os.listdir('.'):
    accept = False
    for spec in specs:
        if fnmatch.fnmatch(file, spec):
            accept = True
            break

    if not accept:
        continue

    with open(file, 'r') as f:
        j = json.load(f)
        row = {}
        (name, ext) = os.path.splitext(os.path.basename(file))
        if re.search('^_', name):
            continue
        if re.search('^schema', name):
            continue
        if 'checkver' in j:
            continue
        if 'homepage' in j:
            url = j['homepage']
        else:
            url = 'https://www.google.com/search?q=' + name
        print("%s: %s" % (name, url))

sys.exit(0)
