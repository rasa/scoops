#!/usr/bin/env python

from __future__ import print_function

import fnmatch
import json
import re
import os
import sys

OSI = [
    'BSD-2-Clause',
    'BSD-3-Clause',
    'AFL-3.0',
    'APL-1.0',
    'Apache-2.0',
    'APSL-2.0',
    'Artistic-2.0',
    'AAL',
    'BSL-1.0',
    'CECILL-2.1',
    'CATOSL-1.1',
    'CDDL-1.0',
    'CPAL-1.0',
    'CUA-OPL-1.0',
    'EUDatagrid',
    'EPL-1.0',
    'eCos-2.0',
    'ECL-2.0',
    'EFL-2.0',
    'Entessa',
    'EUPL-1.1',
    'Fair',
    'Frameworx-1.0',
    'FPL-1.0.0',
    'AGPL-3.0',
    'GPL-2.0',
    'GPL-3.0',
    'LGPL-2.1',
    'LGPL-3.0',
    'HPND',
    'IPL-1.0',
    'IPA',
    'ISC',
    'LPPL-1.3c',
    'LiLiQ-P-1.1',
    'LiLiQ-R-1.1',
    'LiLiQ-Rplus-1.1',
    'LPL-1.02',
    'MirOS',
    'MS-PL',
    'MS-RL',
    'MIT',
    'Motosoto',
    'MPL-1.0',
    'MPL-1.1',
    'MPL-2.0',
    'Multics',
    'NASA-1.3',
    'NTP',
    'Naumen',
    'NGPL',
    'Nokia',
    'NPOSL-3.0',
    'OCLC-2.0',
    'OGTSL',
    'OSL-3.0',
    'OPL-2.1',
    'PHP-3.0',
    'PostgreSQL',
    'Python-2.0',
    'CNRI-Python',
    'QPL-1.0',
    'RPSL-1.0',
    'RPL-1.5',
    'RSCPL',
    'OFL-1.1',
    'SimPL-2.0',
    'Sleepycat',
    'SPL-1.0',
    'Watcom-1.0',
    'NCSA',
    'UPL',
    'VSL-1.0',
    'W3C',
    'WXwindows',
    'Xnet',
    'ZPL-2.0',
    'Zlib',
]

OSImap = {}
for k in OSI:
    OSImap[k.lower()] = 'https://opensource.org/licenses/%s' % k

lmap = {
    'freeware': 'https://en.wikipedia.org/wiki/Freeware',
    'shareware': 'https://en.wikipedia.org/wiki/Shareware',
    'public_domain': 'https://wiki.creativecommons.org/wiki/Public_domain',
    'public domain': 'https://wiki.creativecommons.org/wiki/Public_domain',
    'public-domain': 'https://wiki.creativecommons.org/wiki/Public_domain',
    'publicdomain': 'https://wiki.creativecommons.org/wiki/Public_domain',
}

def do_license(v):
    if re.search('^(http|ftp)', v):
        v = '[%s](%s "%s")' % ('Link', v, v)
        return v

    parts = re.split('[/,\s]+', v)
    v = ''
    for part in parts:
        if v > '':
            v += '/'
        url = ''
        k = part.lower()
        if k in OSImap:
            url = OSImap[k]
        elif k in lmap:
            url = lmap[k]
        if url > '':
            v += '[%s](%s "%s")' % (part, url, url)
        else:
            v += part
    return v

def get_url(js):
    if 'checkver' in js:
        if 'url' in js['checkver']:
            return js['checkver']['url']
    if 'homepage' in js:
        return js['homepage']
    return ''

def do_version(js):
    version = js['version']
    url = get_url(js)
    if url == '':
        return version
    return '[%s](%s "%s")' % (version, url, url)

markdown = 'README.md'
with open(markdown, 'rb') as f:
    lines = f.readlines()

specs = sys.argv
specs.pop(0)

if len(specs) == 0:
    specs = ['*.json']

keys = [
    "description",
    "homepage",
    "license",
    "version",
]

rows = {}

for file in os.listdir('.'):
    accept = False
    for spec in specs:
        if fnmatch.fnmatch(file, spec):
            accept = True
            break

    if not accept:
        continue

    with open(file, 'rb') as f:
        j = json.load(f)
        row = {}
        (name, ext) = os.path.splitext(os.path.basename(file))
        if re.search('^_', name):
            continue
        if re.search('^schema', name):
            continue
        for key in keys:
            if key in j:
                v = j[key].strip()
                if key == 'license':
                    v = do_license(v)
                if key == 'version':
                    v = do_version(j)
                row[key] = v
            else:
                row[key] = ''
        rows[name] = row

table = []

table.append('|Name|Version|Description|License|')
table.append('|----|-------|-----------|-------|')

newlist = [(k,rows[k]) for k in sorted(rows.keys())]

for (name, row) in newlist:
    table.append('|[%s](%s "%s")|%s|%s|%s|' % (name, row['homepage'], row['homepage'], row['version'], row['description'], row['license']))

out = []

found = False
for line in lines:
    line = line.strip()
    if found:
        if re.match(r'^\s*<!--\s+</apps>\s+-->', line):
            found = False
        else:
            continue
    if re.match(r'^\s*<!--\s+<apps>\s+-->', line):
        found = True
        out.append(line)
        out.append('<!-- The following table was inserted by makeindex.py -->')
        out.append('<!-- Your edits will be lost the next time makeindex.py is run -->')
        for row in table:
            out.append(row)
        continue

    out.append(line)

with open(markdown, 'wb') as f:
    f.write("\n".join(out))
    f.write("\n")

sys.exit(0)
