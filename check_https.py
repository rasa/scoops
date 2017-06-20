#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import ssl
import sys
# buggy!
import requests
import certifi
import urllib3
import urllib3.contrib.pyopenssl

USE_URLLIB3 = True

from jsoncomment import JsonComment

from six.moves.urllib.parse import urlsplit, urlunsplit # pylint: disable=import-error

urllib3.contrib.pyopenssl.inject_into_urllib3()

UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
UAS = {
    'sourceforge.net': 'Wget/1.19.1 (mingw32)'
}

class CheckURLs(object):
    """ @todo docstring me """

    def __init__(self):
        """ @todo docstring me """
        self.check_https = True
        self.check_hash = True
        self.check_exists = True
        self.file = ''
        self.data = ''
        self.logger = None

    def is_https(self, url):
        """ @todo docstring me """
        scheme = self.get_scheme(url).lower()
        return scheme == 'https'

    def is_http_or_https(self, url):
        """ @todo docstring me """
        scheme = self.get_scheme(url).lower()
        return re.search('^(https|http)$', scheme, re.I) is not None

    def get_scheme(self, url):
        """ @todo docstring me """
        parts = list(urlsplit(url))
        return parts[0]

    def get_ua(self, url):
        parts = list(urlsplit(url))
        logging.debug('parts=%s', parts)
        for regex in UAS:
            if re.search(re.escape(regex), parts[1], re.I):
                return UAS[regex]
        return UA

    def change_scheme(self, url, new_scheme='https'):
        """ @todo docstring me """
        if not self.is_http_or_https(url):
            return url
        parts = list(urlsplit(url))
        if parts[0] == new_scheme:
            return url
        parts[0] = new_scheme
        return urlunsplit(parts)

    def get(self, url, key='', whine=True):
        """ @todo docstring me """
        ssl_errors = ['MaxRetryError', 'SSLError']
        retries = urllib3.util.retry.Retry(connect=1, read=1)
        http = urllib3.PoolManager(
            retries=retries,
            cert_reqs=ssl.CERT_REQUIRED, 
            ca_certs=certifi.where())

        if not self.is_http_or_https(url):
            logging.debug('%s: %s: %s', self.file, 'not_httpx', url)
            return False

        try:
            data = None
            logging.debug('%s: Retrieving %s', self.file, url)
            ua = self.get_ua(url)
            headers={'User-Agent': ua}
            if USE_URLLIB3:
                r = http.request('GET', url, headers=headers)
                status = r.status
                data = r.data
            else:
                r = requests.get(url)
                status = r.status_code
                data = r.content
            if whine and status < 200 or status > 299:
                logging.warning('%s: %s: %s', self.file, status, url)
                return False
            if not self.check_exists:
                logging.info('%s: %s: %s: %s', self.file, status, key, url)
            return data
        except Exception as e:
            logging.debug('%s: %s: %s: %s', self.file, type(e).__name__, key, url)
            if type(e).__name__ in ssl_errors:
                return False
            logging.exception(e)
            return False

    def check_url(self, url, key, hash='', desc=''):
        """ @todo docstring me """

        hashmap = {
            32: 'md5',
            40: 'sha1',
            64: 'sha256',
            128: 'sha512',
        }

        if desc:
            key += '.' + desc
        logging.debug('%s: key=%s hash=%s url=%s', self.file, key, hash, url)
        if not hash and self.is_https(url) and not self.check_exists:
            return False

        if self.check_https and not self.is_https(url):
            new_url = self.change_scheme(url)
        else:
            new_url = url

        content = False
        if self.check_exists:
            retry = self.is_https(new_url)
        else:
            retry = new_url != url and hash
        content = self.get(new_url, key, not retry)
        if retry and not content:
            if self.check_exists:
                new_url = self.change_scheme(url, 'http')
            else:
                new_url = url
            content = self.get(new_url, key)

        if not content:
            logging.debug('%s: No content for %s', self.file, new_url)
            return False

        if self.check_hash and hash:
            logging.debug('%s: Verifying hash %s', self.file, hash)
            m = re.search(r':([^:]+)$', hash)
            if m:
                hash = m.group(1).strip()
            hashlen = len(hash)
            if hashlen not in hashmap:
                logging.error('%s: Unknown hash type %s: %s', self.file, hashlen, hash)
            else:
                h = hashlib.new(hashmap[hashlen])
                h.update(content)
                chash = h.hexdigest().lower()
                if chash == hash.lower():
                    logging.debug('%s: Hashes match:  %s', self.file, chash)
                else:
                    logging.warning(
                        '%s: Found %s, expected %s', self.file, chash, hash)
                    self.data = re.sub(hash, chash, self.data)

        if new_url == url:
            return ''

        old_data = self.data

        logging.debug('%s: Changing\n%s to\n%s', self.file, url, new_url)
        self.data = re.sub(re.escape(url), new_url, self.data)

        if self.data != old_data:
            logging.debug('%s: Returning %s', self.file, self.get_scheme(new_url))
            return self.get_scheme(new_url)

        logging.debug('%s: Returning %s', self.file, '')
        return ''

    def check_urls(self, url_or_list, key, hash='', desc=''):
        """ @todo docstring me """
        if isinstance(url_or_list, list):
            schemes = []
            for index, url in enumerate(url_or_list):
                hash_value = ''
                if isinstance(hash, list):
                    if len(hash) > index:
                        hash_value = hash[index]
                schemes.append(self.check_url(url, key, hash_value, desc))

            return schemes

        return self.check_url(url_or_list, key, hash, desc)

    def process(self, j, key, hash='', desc=''):
        """ @todo docstring me """

        if key not in j:
            return False
        if isinstance(j[key], dict):
            if 'url' not in j[key]:
                return False

            if not hash and self.check_hash and 'hash' in j[key]:
                hash = j[key]['hash']

            return self.check_urls(j[key]['url'], key, hash, desc)

        return self.check_urls(j[key], key, hash, desc)

    def _fix_scheme(self, url, key, scheme='https', desc=''):
        """ @todo docstring me """

        new_url = self.change_scheme(url, scheme)

        old_data = self.data

        if new_url != url:
            self.data = re.sub(re.escape(url), new_url, self.data)

        return self.data != old_data

    def _fix_schemes(self, url_or_list, key, scheme='https', desc=''):
        """ @todo docstring me """
        if isinstance(url_or_list, list):
            updated = False
            for index, url in enumerate(url_or_list):
                _scheme = scheme[index]
                updated |= self._fix_scheme(url, key, _scheme, desc)

            return updated

        logging.debug('scheme=%s', scheme)
        return self._fix_scheme(url_or_list, key, scheme, desc)

    def fix_schemes(self, j, key, scheme='https', desc=''):
        """ @todo docstring me """

        if key not in j:
            return False
        if isinstance(j[key], dict):
            if 'url' not in j[key]:
                return False

            return self._fix_schemes(j[key]['url'], key, scheme, desc)

        return self._fix_schemes(j[key], key, scheme, desc)

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

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        logger2 = logging.getLogger('urllib3')
        logger2.setLevel(logging.CRITICAL)

        parser = JsonComment(json)
        
        mask = dir_name + '/' + filespec
        logging.info("==> Processing dir %s", mask)
        for file in glob.glob(mask):
            self.file = os.path.basename(file)
            logging.debug("--> Processing file %s", file)
            with io.open(file, 'r', encoding='utf-8') as f:
                self.data = f.read()
            orig_data = self.data
            j = parser.loads(self.data)
            hash = ''
            if self.check_hash and 'hash' in j:
                hash = j['hash']
            scheme = self.process(j, 'homepage')
            scheme = self.process(j, 'license')
            scheme = self.process(j, 'url', hash)
            if scheme:
                self.fix_schemes(j, 'autoupdate', scheme)
            scheme = self.process(j, 'checkver')
            if 'checkver' in j:
                if isinstance(j['checkver'], dict):
                    scheme = self.process(j['checkver'], 'github')
            if 'architecture' in j:
                scheme = self.process(j['architecture'], '32bit',
                                       '', 'architecture')
                if isinstance(scheme, list):
                    scheme = scheme[0]
                if scheme:
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            self.fix_schemes(
                                j['autoupdate']['architecture'], '32bit',
                                scheme, 'autoupdate.architecture')

                scheme = self.process(j['architecture'], '64bit',
                                       '', 'architecture')
                if isinstance(scheme, list):
                    scheme = scheme[0]
                if scheme:
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            self.fix_schemes(
                                j['autoupdate']['architecture'], '64bit',
                                scheme, 'autoupdate.architecture')
            if self.data != orig_data:
                logging.info("Updating %s" % file)
                if os.path.isfile(file + '.bak'):
                    os.remove(file + '.bak')
                os.rename(file, file + '.bak')
                with io.open(file, 'w', encoding='utf-8') as f:
                    f.write(self.data)


checker = CheckURLs()
checker.run()

sys.exit(0)
