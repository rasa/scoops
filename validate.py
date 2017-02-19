#!/usr/bin/env python

from __future__ import print_function
from jsoncomment import JsonComment
from jsonschema import validate

import json
import os
import pprint
import re
import sys
import traceback

def decode(s):
    for encoding in 'utf-8-sig', 'utf-16':
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            continue
    return s.decode('latin-1')

schema_name = 'schema.json'

file = sys.argv[1]
if re.match('^schema', file):
    sys.exit(0)

print('Validating', file)

with open(schema_name, 'r') as f:
    schema_data = json.load(f)

with open(file, 'r') as f:
    jstr = f.read(os.path.getsize(file))

jstr_no_bom = decode(jstr)
failed = file + '.failed'
if os.path.exists(failed):
    os.remove(failed)

try:
    parser = JsonComment(json)
    json_data = parser.loads(jstr_no_bom)

    validate(json_data, schema_data)

except Exception as e:
    trace = traceback.format_exc()
    print(trace)
    with open(failed, 'a+') as f:
        f.write(trace)
    sys.exit(1)

sys.exit(0)
