#!/usr/bin/env python

from __future__ import print_function
from jsoncomment import JsonComment
from jsonschema import validate

import glob
import json
import os
import sys


def decode(s):
    for encoding in 'utf-8-sig', 'utf-16':
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            continue
    return s.decode('latin-1')


scoop_root = 'C:/Users/ross/scoop'
buckets_root = scoop_root + '/buckets'

buckets = [
    scoop_root + '/apps/scoop/current/bucket',
    # buckets_root + '/extras',
    # buckets_root + '/nirsoft',
    # buckets_root + '/rasa'
]

parser = JsonComment(json)

map = {}

for bucket in buckets:
    for json in glob.glob(bucket + '/*.json'):
        with open(json, 'rb') as f:
            jstr = f.read()
            jstr_no_bom = decode(jstr)
            json_data = parser.loads(jstr_no_bom)
            if 'bin' not in json_data:
                continue
            base = os.path.basename(json)
            base = os.path.splitext(base)[0]
            dir = os.path.basename(os.path.dirname(json))
            repo = dir + '/' + base
            bins = json_data['bin']
            if len(bins) == 0:
                continue
            if type(bins).__name__ != 'list':
                bins = [bins]
            if len(bins) == 0:
                continue
            if type(bins).__name__ != 'list':
                bins = [bins]
            for bin in bins:
                if type(bin).__name__ == 'list':
                    if len(bin) > 1:
                        file = str(bin[1])
                    else:
                        file = str(bin[0])
                else:
                    file = bin
                file = os.path.basename(file)
                file = os.path.splitext(file)[0]
                file = file.lower()
                if file not in map:
                    map[file] = {}
                map[file][repo] = 1
                # print("%s: %s" % (repo, bin))

sfile = sorted(map.keys())

for file in sfile:
    if len(map[file]) > 1:
        for repo in map[file]:
            print("%s: %s" % (file, repo))

sys.exit(0)
