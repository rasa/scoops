#!/usr/bin/env python
""" @todo docstring me """

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import fnmatch
import glob
import io
import json
import re
import os
import sys
import pprint
import requests

from jsoncomment import JsonComment
from jsonschema import validate

from six.moves.urllib.parse import urlsplit, urlunsplit

class CheckURLs(object):
    """ @todo docstring me """
    def __init__(self):
        """ @todo docstring me """
        self.file = ''
        self.last = ''
        self.data = ''
        self.orig_data = ''

    def is_https(self, url):
        """ @todo docstring me """
        return re.search(r'^https', url, re.I) is not None

    def httpsify(self, url):
        """ @todo docstring me """
        if self.is_https(url):
            return url
        if re.search(r'^https', url, re.I):
            return url
        parts = list(urlsplit(url))
        parts[0] = 'https'
        return urlunsplit(parts)

    def check_url(self, url, key, get=True, hash='', desc=''):
        """ @todo docstring me """
        if desc:
            key += '.' + desc
        # print("url=%s hash=%s" % (url, hash))
        if self.is_https(url):
            return False
        new_url = self.httpsify(url)
        if get:
            try:
                r = requests.get(new_url)
                if r.status_code < 200 or r.status_code > 299:
                    # print("    %s: %s" % (r.status_code, url))
                    return False
                if self.file != self.last:
                    print("  %s:" % self.file)
                print("    %s: %s: %s" % (r.status_code, key, url))
            except Exception as e:
                #print("    %s: %s: %s" % (500, key, url))
                return False

        old_data = self.data
        self.data = re.sub(re.escape(url), new_url, self.data)
        return self.data != old_data

    def check_urls(self, url_or_list, key, get=True, hash='', desc=''):
        """ @todo docstring me """
        if isinstance(url_or_list, list):
            updated = False
            for index, url in enumerate(url_or_list):
                hash_value = ''
                if isinstance(hash, list):
                    if len(hash) > index:
                        hash_value = hash[index]
                updated += self.check_url(url, key, get, hash_value, desc)

            return updated

        return self.check_url(url_or_list, key, get, desc)
        
    def process(self, j, key, get=True, hash='', desc=''):
        """ @todo docstring me """

        if not key in j:
            return False
        if isinstance(j[key], dict):
            if not 'url' in j[key]:
                return False

            if not hash:
                if 'hash' in j[key]:
                    hash = j[key]['hash']
                
            return self.check_urls(j[key]['url'], key, get, hash, desc)

        return self.check_urls(j[key], key, get, hash, desc)
        
    def run(self, args=None):
        """ @todo docstring me """
        if not args:
            args = sys.argv[1:]
        if not args:
            args = ['.']

        parser = JsonComment(json)

        for arg in args:
            mask = arg + '/*.json'
            print("%s:" % mask)
            for file in glob.glob(mask):
                self.file = file
                print("  %s:" % file)
                with io.open(file, 'r', encoding='utf-8') as f:
                    self.data = f.read()
                self.orig_data = self.data
                j = parser.loads(self.data)
                hash = ''
                if 'hash' in j:
                    hash = j['hash']
                changed = self.process(j, 'homepage')
                changed = self.process(j, 'license')
                changed = self.process(j, 'url', True, hash)
                if changed:
                    changed = self.process(j, 'autoupdate', False)
                changed = self.process(j, 'checkver')
                if 'checkver' in j:
                    if isinstance(j['checkver'], dict):
                        changed = self.process(j['checkver'], 'github')
                if 'architecture' in j:
                    changed = self.process(j['architecture'], '32bit', True, '', 'architecture')
                    if changed:
                        if 'autoupdate' in j:
                            if 'architecture' in j['autoupdate']:
                                changed = self.process(j['autoupdate']['architecture'], '32bit', False, '', 'autoupdate.architecture')
                    changed = self.process(j['architecture'], '64bit', True, '', 'architecture')
                    if changed:
                        if 'autoupdate' in j:
                            if 'architecture' in j['autoupdate']:
                                changed = self.process(j['autoupdate']['architecture'], '64bit', False, '', 'autoupdate.architecture')
                self.last = file
                if self.data != self.orig_data:
                    print("Updating %s" % file)
                    if os.path.isfile(file + '.bak'):
                        os.remove(file + '.bak')
                    os.rename(file, file + '.bak')
                    with io.open(file, 'w', encoding='utf-8') as f:
                        f.write(self.data)

checker = CheckURLs()
checker.run()
                        
sys.exit(0)
