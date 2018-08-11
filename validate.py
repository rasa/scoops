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
from jsonschema import validate

import json
import os
# import pprint
import re
import sys
import traceback


def decode(s):
    if sys.version_info >= (3, 0):
        return s

    for encoding in 'utf-8-sig', 'utf-16':
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            continue
    return s.decode('latin-1')


schema_name = 'D:/github/rasa/scoop/schema.json'

if not os.path.isfile(schema_name):
    schema_name = '%s/scoop/apps/scoop/current/schema.json' % os.environ[
        'USERPROFILE']

file = sys.argv[1]
if re.match('^schema', file):
    sys.exit(0)

print('Validating %s via %s' % (file, schema_name))

with open(schema_name, 'r') as f:
    schema_data = json.load(f)

with open(file, 'r') as f:
    jstr = f.read()

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
