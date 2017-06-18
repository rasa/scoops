#!/usr/bin/env python
""" @todo docstring me """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import glob
import hashlib
import io
import logging
import json
import re
import os
import sys
import requests

from jsoncomment import JsonComment

from six.moves.urllib.parse import urlsplit, urlunsplit # pylint: disable=import-error

class CheckURLs(object):
    """ @todo docstring me """

    def __init__(self):
        """ @todo docstring me """
        self.file = ''
        self.file_displayed = False
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
        if not re.search('^(http|ftp)$', parts[0], re.I):
            return url
        parts[0] = 'https'
        return urlunsplit(parts)

    def get(self, url, key=''):
        """ @todo docstring me """

        if not re.search('^(https|http|ftp):', url, re.I):
            if not self.file_displayed:
                self.file_displayed = True
                logging.debug("  %s:", self.file)
            logging.debug("    %-6s: %s", 'noturl', url)
            return False

        try:
            logging.debug("    %-6s: Retrieving %s", 'geturl', url)
            r = requests.get(url)
            if r.status_code < 200 or r.status_code > 299:
                if not self.file_displayed:
                    self.file_displayed = True
                    logging.warning("  %s:", self.file)
                logging.warning("    %-6s: %s", r.status_code, url)
                return False
            if not self.file_displayed:
                self.file_displayed = True
                logging.info("  %s:", self.file)
            logging.info("    %-6s: %s: %s", r.status_code, key, url)
            return r.content
        except Exception:
            # logging.exception(e)
            if not self.file_displayed:
                self.file_displayed = True
                logging.debug("  %s:", self.file)
            logging.debug("    %-6s: %s: %s", '!https', key, url)
            return False

    def check_url(self, url, key, get=True, hash='', desc=''):
        """ @todo docstring me """

        hashmap = {
            32: 'md5',
            40: 'sha1',
            64: 'sha256',
            128: 'sha512',
        }

        if desc:
            key += '.' + desc
        logging.debug("    url=%s key=%s hash=%s", url, key, hash)
        if not hash and self.is_https(url):
            return False

        if get and not self.is_https(url):
            new_url = self.httpsify(url)
        else:
            new_url = url

        content = False
        if get or hash:
            content = self.get(new_url, key)
            if not content and new_url != url and hash:
                new_url = url
                content = self.get(url, key)

        if not content:
            logging.debug("    No content for %s", new_url)
            return False

        old_data = self.data

        if hash:
            logging.debug("    Verifying hash %s", hash)
            m = re.search(r':([^:]+)$', hash)
            if m:
                hash = m.group(1).strip()
            hashlen = len(hash)
            if hashlen not in hashmap:
                logging.error("    Unknown hash type %s: %s", hashlen, hash)
            else:
                h = hashlib.new(hashmap[hashlen])
                h.update(content)
                chash = h.hexdigest().lower()
                if chash == hash.lower():
                    logging.debug("    Hashes match: %s", chash)
                else:
                    logging.warning(
                        "    Hashes mismatch: found %s, expected %s", chash, hash)
                    self.data = re.sub(hash, chash, self.data)

        if new_url != url:
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

        return self.check_url(url_or_list, key, get, hash, desc)

    def process(self, j, key, get=True, hash='', desc=''):
        """ @todo docstring me """

        if key not in j:
            return False
        if isinstance(j[key], dict):
            if 'url' not in j[key]:
                return False

            if not hash:
                if 'hash' in j[key]:
                    hash = j[key]['hash']

            return self.check_urls(j[key]['url'], key, get, hash, desc)

        return self.check_urls(j[key], key, get, hash, desc)

    def run(self):
        """ @todo docstring me """
        if len(sys.argv) >= 3:
            filespec = sys.argv[2]
        else:
            filespec = '*.json'

        if len(sys.argv) >= 2:
            dir_name = sys.argv[1]
        else:
            dir_name = '.'

        logger = logging.getLogger()
        # required, must be set lower than all possible levels:
        logger.setLevel(logging.INFO)

        logger2 = logging.getLogger('urllib3')
        logger2.setLevel(logging.CRITICAL)

        parser = JsonComment(json)
        
        # for arg in args:
        mask = dir_name + '/' + filespec
        logging.info("%s:", mask)
        for file in glob.glob(mask):
            self.file = file
            self.file_displayed = logger.isEnabledFor(logging.DEBUG)
            #if self.file_displayed:
            logging.info("  %s:", file)
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
                changed = self.process(j['architecture'], '32bit', True,
                                       '', 'architecture')
                if changed:
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            changed = self.process(
                                j['autoupdate']['architecture'], '32bit',
                                False, '', 'autoupdate.architecture')
                changed = self.process(j['architecture'], '64bit', True,
                                       '', 'architecture')
                if changed:
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            changed = self.process(
                                j['autoupdate']['architecture'], '64bit',
                                False, '', 'autoupdate.architecture')
            if self.data != self.orig_data:
                logging.info("Updating %s" % file)
                if os.path.isfile(file + '.bak'):
                    os.remove(file + '.bak')
                os.rename(file, file + '.bak')
                with io.open(file, 'w', encoding='utf-8') as f:
                    f.write(self.data)


checker = CheckURLs()
checker.run()

sys.exit(0)
