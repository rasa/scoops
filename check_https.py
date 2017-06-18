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

    def is_https(self, url):
        return re.search(r'^https', url, re.I) is not None

    def httpsify(self, url):
        if self.is_https(url):
            return url
        if re.search(r'^https', url, re.I):
            return url
        parts = list(urlsplit(url))
        parts[0] = 'https'
        # newparts = parts._replace(scheme='https')
        parts[0] = 'https'
        return urlunsplit(parts)

    def check_url(self, url, key, data, get=True, hash='', desc=''):
        """ @todo docstring me """
        if desc:
            key += '.' + desc
        # print("url=%s hash=%s" % (url, hash))
        if self.is_https(url):
            return (data, False)
        new_url = self.httpsify(url)
        if get:
            try:
                r = requests.get(new_url)
                if r.status_code < 200 or r.status_code > 299:
                    # print("    %s: %s" % (r.status_code, url))
                    return (data, False)
                if self.file != self.last:
                    print("  %s:" % self.file)
                print("    %s: %s: %s" % (r.status_code, key, url))
            except Exception as e:
                #print("    %s: %s: %s" % (500, key, url))
                return (data, False)

        new_data = re.sub(re.escape(url), new_url, data)
        return (new_data, new_data != data)

        return (data, False)

    def check_urls(self, url_or_list, key, data, get=True, hash='', desc=''):
        """ @todo docstring me """
        if isinstance(url_or_list, list):
            updated = False
            for index, url in enumerate(url_or_list):
                if isinstance(hash, list):
                    hash_value = hash[index]
                else:
                    hash_value = ''
                (data, changed) = self.check_url(url, key, data, get, hash_value, desc)
                if changed:
                    updated = True
            return (data, updated)

        return self.check_url(url_or_list, key, data, get, desc)
        
    def process(self, j, key, data, get=True, hash='', desc=''):
        """ @todo docstring me """

        if not key in j:
            return (data, False)
        if isinstance(j[key], dict):
            if not 'url' in j[key]:
                return (data, False)

            if not hash:
                if 'hash' in j[key]:
                    hash = j[key]['hash']
                
            return self.check_urls(j[key]['url'], key, data, get, hash, desc)

        return self.check_urls(j[key], key, data, get, hash, desc)
        
    def run(self, args=None):
        """ @todo docstring me """
        if not args:
            args = sys.argv[1:]
        if not args:
            args = ['.']

        for arg in args:
            mask = arg + '/*.json'
            print("%s:" % mask)
            parser = JsonComment(json)
            for file in glob.glob(mask):
                self.file = file
                #print("  %s:" % file)
                with io.open(file, 'r', encoding='utf-8') as f:
                    data = f.read()
                    orig_data = data
                with io.open(file, 'r', encoding='utf-8') as f:
                    j = parser.load(f)
                    hash = ''
                    if 'hash' in j:
                        hash = j['hash']
                    # (data, changed) = self.process(j, 'homepage', data)
                    (data, changed) = self.process(j, 'license', data)
                    # (data, changed) = self.process(j, 'url', data, True, hash)
                    # if changed:
                        # (data, changed) = self.process(j, 'autoupdate', data, False)
                    # (data, changed) = self.process(j, 'checkver', data)
                    # if 'checkver' in j:
                        # if isinstance(j['checkver'], dict):
                            # (data, changed) = self.process(j['checkver'], 'github', data)
                    # if 'architecture' in j:
                        # (data, changed) = self.process(j['architecture'], '32bit', data, True, '', 'architecture')
                        # if changed:
                            # if 'autoupdate' in j:
                                # if 'architecture' in j['autoupdate']:
                                    # (data, changed) = self.process(j['autoupdate']['architecture'], '32bit', data, False, '', 'autoupdate.architecture')
                        # (data, changed) = self.process(j['architecture'], '64bit', data, True, '', 'architecture')
                        # if changed:
                            # if 'autoupdate' in j:
                                # if 'architecture' in j['autoupdate']:
                                    # (data, changed) = self.process(j['autoupdate']['architecture'], '32bit', data, False, '', 'autoupdate.architecture')
                self.last = file
                if data != orig_data:
                    print("Updating %s" % file)
                    os.rename(file, file + '.bak')
                    with io.open(file, 'w', encoding='utf-8') as f:
                        f.write(data)

checker = CheckURLs()
checker.run()
                        
sys.exit(0)
