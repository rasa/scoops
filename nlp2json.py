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

import io
import json
import os
import re
import subprocess
import sys

if len(sys.argv) > 1:
    nirsoft_dir = sys.argv[1]
else:
    nirsoft_dir = os.path.join(os.environ['USERPROFILE'],
                               'scoop/apps/nirlauncher/current/NirSoft')

nirsoft_dir = re.sub(r'\\', '/', nirsoft_dir)
nirsoft_nlp = os.path.join(nirsoft_dir, 'nirsoft.nlp')

if len(sys.argv) > 2:
    nirlauncher_json = sys.argv[2]
else:
    nirlauncher_json = os.path.join(
        os.path.dirname(nirsoft_dir), 'manifest.json')

nirlauncher_json = re.sub(r'\\', '/', nirlauncher_json)

with io.open(nirlauncher_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

with io.open(nirsoft_nlp, 'r', encoding='utf-8') as f:
    lines = f.readlines()

exes = {}

h = {}

for line in lines:
    if re.match(r'\[', line):
        if 'exe' in h:
            if h['exe']:
                exes[os.path.basename(h['exe'])] = h
        h = {}
        continue
    m = re.match(r'([^=]+)=(.*)', line)
    if not m:
        continue
    k = m.group(1).strip()
    v = m.group(2).strip()
    h[k] = v

data['architecture']['32bit']['bin'] = ["Nirlauncher.exe"]
data['architecture']['32bit']['shortcuts'] = [[
    "Nirlauncher.exe",
    "Nirlauncher - Run over 200 freeware utilities from nirsoft.net"
]]
data['architecture']['64bit']['bin'] = ["Nirlauncher.exe"]
data['architecture']['64bit']['shortcuts'] = [[
    "Nirlauncher.exe",
    "Nirlauncher - Run over 200 freeware utilities from nirsoft.net"
]]

for base in sorted(exes, key=unicode.lower):
    h = exes[base]
    desc = h['ShortDesc']
    desc = re.sub(r'"', "'", desc)
    desc = re.sub(r'[/\\]', ",", desc)
    desc = re.sub(r'[<>\|\?\*:/]', "", desc)

    desc = desc.rstrip('.')
    if desc:
        desc = desc[0].upper() + desc[1:]
    print("%-25s %s" % (os.path.splitext(base)[0], desc))
    path = 'NirSoft/' + h['exe']
    path = re.sub(r'\\', '/', path)
    data['architecture']['32bit']['bin'].append(path)
    fullpath = nirsoft_dir + '/' + h['exe']
    stdout = subprocess.check_output(["exetype", fullpath])
    if re.search('GUI', stdout):
        if 'AppName' in h and h['AppName']:
            appname = h['AppName']
        else:
            appname = os.path.splitext(base)[0]
        name = '%s/%s' % ('NirSoft', appname)
        if desc:
            name += ' - ' + desc
        data['architecture']['32bit']['shortcuts'].append([path, name])
    if 'exe64' not in h or not h['exe64']:
        data['architecture']['64bit']['bin'].append(path)
        if re.search('GUI', stdout):
            data['architecture']['64bit']['shortcuts'].append([path, name])
        continue

    path = 'NirSoft/' + h['exe64']
    path = re.sub(r'\\', '/', path)
    data['architecture']['64bit']['bin'].append(path)
    if re.search('GUI', stdout):
        data['architecture']['64bit']['shortcuts'].append([path, name])

jsons = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

utf8 = jsons.decode('utf-8')
utf8 += "\n"

nirlauncher_tmp = nirlauncher_json + '.tmp'

with io.open(nirlauncher_tmp, 'w', newline='\n') as f:
    written = f.write(utf8)

os.remove(nirlauncher_json)
os.rename(nirlauncher_tmp, nirlauncher_json)
