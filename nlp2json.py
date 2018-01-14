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
# import pprint
import re
import subprocess
import sys

if len(sys.argv) > 1:
    nirlauncher_json = sys.argv[1]
else:
    nirlauncher_json = 'd:/github/rasa/scoop-extras/nirlauncher.json'

if len(sys.argv) > 2:
    nirsoft_nlp = sys.argv[2]
else:
    # c:\scoop\apps\nirlauncher\current\NirSoft\nirsoft.nlp
    nirsoft_nlp = 'c:/scoop/apps/nirlauncher/current/NirSoft/nirsoft.nlp'

with io.open(nirlauncher_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

with io.open(nirsoft_nlp, 'r', encoding='utf-8') as f:
    lines = f.readlines()

exes = {'32bit': {}, '64bit': {}}

h = {}

for line in lines:
    if re.match('\[', line):
        if 'exe64' in h:
            if h['exe64']:
                h['path'] = re.sub(r'\\', '/', h['exe64'])
                exes['64bit'][os.path.basename(h['path'])] = h
            else:
                h['path'] = re.sub(r'\\', '/', h['exe'])
                exes['32bit'][os.path.basename(h['path'])] = h
        h = {}
        continue
    m = re.match('([^=]+)=(.*)', line)
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

for arch, files in exes.items():
    for file in sorted(files, key=unicode.lower):
        h = files[file]
        desc = h['ShortDesc']
        desc = re.sub(r'"', "'", desc)
        desc = re.sub(r'[/\\]', ",", desc)
        desc = re.sub(r'[<>\|\?\*:/]', "", desc)

        desc = desc.rstrip('.')
        print("%-25s %s" % (os.path.splitext(file)[0], desc))
        fullpath = os.path.dirname(nirsoft_nlp) + '/' + h['path']
        stdout = subprocess.check_output(["exetype", fullpath])
        path = 'NirSoft/' + h['path']
        data['architecture'][arch]['bin'].append(path)
        if file not in exes['64bit']:
            data['architecture']['64bit']['bin'].append(path)
        if re.search('GUI', stdout):
            if 'AppName' in h and h['AppName']:
                appname = h['AppName']
            else:
                appname = os.path.splitext(file)[0]
            name = '%s/%s' % ('NirSoft', appname)
            if desc:
                name += ' - ' + desc
            data['architecture'][arch]['shortcuts'].append([path, name])
            if file not in exes['64bit']:
                data['architecture']['64bit']['shortcuts'].append([path, name])

jsons = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

utf8 = jsons.decode('utf-8')
utf8 += "\n"

nirlauncher_tmp = nirlauncher_json + '.tmp'

with io.open(nirlauncher_tmp, 'w', newline='\n') as f:
    written = f.write(utf8)

os.remove(nirlauncher_json)
os.rename(nirlauncher_tmp, nirlauncher_json)
