#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" @todo docstring me """

from __future__ import (
    absolute_import,
    division,
    print_function,
    # unicode_literals
)

import glob
import hashlib
import io
import logging
import json
import re
import os
# @todo implement progressbar
import ssl
import subprocess
import sys
import urllib2

from six.moves.urllib.parse import urlsplit, urlunsplit  # pylint: disable=import-error

import jsoncomment

import urllib3
import urllib3.contrib.pyopenssl
import certifi

import requests

DOWNLOADER = 'urllib3'

if DOWNLOADER == 'urllib3':
    urllib3.contrib.pyopenssl.inject_into_urllib3()

# UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
# SF_UA = "Scoop/1.0 (+http://scoop.sh/) (Windows NT 6.1; WOW64)"
UA = "Scoop/1.0 (+http://scoop.sh/) (Windows NT 6.1; WOW64)"

# UAS = {'sourceforge.net': SF_UA}
UAS = {}

NO_REFERRERS = ['sourceforge.net']


class CheckURLs(object):
    """ @todo docstring me """

    def __init__(self):
        """ @todo docstring me """

        self.check_https = True
        self.check_hash = True
        self.check_exists = True
        self.dir = ''
        self.file = ''
        self.basename = ''
        self.data = ''
        self.logger = None
        self.tmp_file = None

    def is_https(self, url):
        """ @todo docstring me """

        scheme = self.get_scheme(url).lower()
        return scheme == 'https'

    def is_http_or_https(self, url):
        """ @todo docstring me """

        scheme = self.get_scheme(url).lower()
        return re.search(r'^(https|http)$', scheme, re.I) is not None

    def get_scheme(self, url):
        """ @todo docstring me """

        parts = list(urlsplit(url))
        if parts:
            return parts[0]
        logging.warning('Cannot split %s', url)
        return None

    def get_host(self, url):
        """ @todo docstring me """

        parts = list(urlsplit(url))
        if len(parts) > 1:
            return parts[1]

        logging.warning('Cannot split %s', url)
        return None

    def is_sourceforge(self, url):
        """ @todo docstring me """

        host = self.get_host(url)
        return re.search(r'sourceforge\.net$', host, re.I) is not None

    def get_ua(self, url):
        """ @todo docstring me """

        host = self.get_host(url)
        if not host:
            logging.warning('Cannot split %s', url)
            return UA

        for regex in UAS:
            if re.search(re.escape(regex), host, re.I):
                return UAS[regex]

        return UA

    def change_scheme(self, url, new_scheme='https'):
        """ @todo docstring me """

        if not self.is_http_or_https(url):
            return url
        parts = list(urlsplit(url))
        if not parts:
            logging.warning('Cannot split %s', url)
            return url
        if parts[0] == new_scheme:
            return url
        parts[0] = new_scheme
        return urlunsplit(parts)

    def get_referer(self, url):
        """ @todo docstring me """
        parts = list(urlsplit(url))
        if len(parts) < 2:
            logging.warning('Cannot split %s', url)
            return url
        for referer in NO_REFERRERS:
            if re.search(re.escape(referer), parts[1], re.I):
                return ''
        m = re.search(r'(.*/)[^/]+$', parts[2])
        if m:
            base = m.group(1)
        else:
            base = '/'
        return urlunsplit([parts[0], parts[1], base, '', ''])

    def save(self, url, data, key):
        """ @todo docstring me """

        INVALID_FILE_CHARS = '<>"|?*:/\\%'

        if re.search(r'(autoupdate|checkver|github|homepage|license)', key,
                     re.I):
            return False
        m = re.search(r'/([^/]+)/?$', url)
        if not m:
            logging.warning('%s: no / in url: %s', key, url)
            return False
        dir = 'tmp' + '/' + self.basename
        file = m.group(1)
        for c in INVALID_FILE_CHARS:
            file = file.replace(c, '-')

        try:
            if not os.path.exists(dir):
                os.makedirs(dir)
            self.tmp_file = dir + '/' + file
            logging.debug('%s: Saving %s bytes to %s', key,
                          len(data), self.tmp_file)
            with io.open(self.tmp_file, 'wb') as f:
                f.write(data)
        except Exception as e:
            logging.exception(e)
            return False
        return True

    def download(self, url, headers):
        """ @todo docstring me """

        status = None
        data = None
        if DOWNLOADER == 'urllib3':
            # retries = urllib3.util.retry.Retry(connect=1, read=1)
            http = urllib3.PoolManager(
                # retries=retries,
                cert_reqs=ssl.CERT_REQUIRED,
                ca_certs=certifi.where())
            r = http.request('GET', url, headers=headers)
            status = r.status
            data = r.data
        if DOWNLOADER == 'requests':
            r = requests.get(url, headers=headers)
            status = r.status_code
            data = r.content
        if DOWNLOADER == 'urllib2':
            request = urllib2.Request(url, headers=headers)
            data = urllib2.urlopen(request).read()
            status = request.getcode()
        return (status, data)

    def get(self, url, key='', whine=True):
        """ @todo docstring me """
        ssl_errors = ['MaxRetryError', 'SSLError']

        if re.search(r'(autoupdate|checkver|github|homepage|license)', key,
                     re.I):
            return False

        if not self.is_http_or_https(url):
            logging.debug('%s %s: %s', key, 'not http or https', url)
            return False

        try:
            logging.debug('%s: Retrieving %s', key, url)
            ua = self.get_ua(url)
            headers = {'User-Agent': ua}

            referer = self.get_referer(url)
            if referer:
                headers['Referer'] = referer

            (status, data) = self.download(url, headers)

            if status < 200 or status > 299:
                if whine:
                    logging.error('%s: Error %s: %s', key, status, url)
                return False
            logging.debug('%s: Status %s: %s', key, status, url)
            self.save(url, data, key)
            return data
        except Exception as e:
            reason = ''
            if hasattr(e, 'reason'):
                reason = e.reason
            elif hasattr(e, 'code'):
                reason = e.code
            if type(e).__name__ in ssl_errors:
                logging.debug('%s: Exception %s: %s (%s)', key,
                              type(e).__name__, reason, url)
                return False
            logging.error('%s: Exception %s: %s (%s)', key,
                          type(e).__name__, reason, url)
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
        logging.debug('%s: %s (%s)', key, url, hash)
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
            logging.debug('%s: No content for %s', key, new_url)
            return False

        if self.check_hash and hash:
            logging.debug('%s: Verifying hash %s', key, hash)
            m = re.search(r':([^:]+)$', hash)
            if m:
                hash = m.group(1).strip()
            hashlen = len(hash)
            if hashlen not in hashmap:
                logging.error('%s: Unknown hash type %s: %s', key, hashlen,
                              hash)
            else:
                h = hashlib.new(hashmap[hashlen])
                h.update(content)
                chash = h.hexdigest().lower()
                if chash == hash.lower():
                    logging.debug('%s: Hashes match:  %s', key, chash)
                else:
                    output = subprocess.check_output(['file', self.tmp_file])
                    if re.search(r'html', output, re.I) is None:
                        logging.error('%s: Found %s, expected %s (%s)', key,
                                      chash, hash, url)
                        for line in output.splitlines():
                            line = line.split()
                            if line:
                                logging.error(line)
                        self.data = re.sub(hash, chash, self.data)

        if new_url == url:
            return ''

        old_data = self.data

        logging.error('%s: Changing\n%s to\n%s', key, url, new_url)
        self.data = re.sub(re.escape(url), new_url, self.data)

        if self.data != old_data:
            logging.debug('%s: Returning %s', key, self.get_scheme(new_url))
            return self.get_scheme(new_url)

        logging.debug('%s: Returning ""', key)
        return ''

    def check_urls(self, url_or_list, key, hash='', desc=''):
        """ @todo docstring me """

        if desc:
            key += '.' + desc

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

        if desc:
            key += '.' + desc

        if isinstance(scheme, list):
            logging.info("_fix_scheme: scheme=%s", ",".join(scheme))
            scheme = scheme[0]
            logging.info("_fix_scheme: scheme=%s", scheme)

        new_url = self.change_scheme(url, scheme)

        old_data = self.data

        if new_url != url:
            self.data = re.sub(re.escape(url), new_url, self.data)

        if self.data != old_data:
            logging.debug('%s: Changing %s to %s', key, url, new_url)

        return self.data != old_data

    def _fix_schemes(self, url_or_list, key, scheme='https', desc=''):
        """ @todo docstring me """

        if desc:
            key += '.' + desc

        if isinstance(url_or_list, list):
            updated = False
            for index, url in enumerate(url_or_list):
                if isinstance(scheme, list):
                    logging.info("_fix_schemes: scheme=%s", ",".join(scheme))
                    if index < len(scheme):
                        scheme = scheme[index]
                    else:
                        scheme = scheme[0]
                logging.info("_fix_schemes: scheme=%s", scheme)
                updated |= self._fix_scheme(url, key, scheme, desc)

            return updated

        # logging.debug('scheme=%s', scheme)
        return self._fix_scheme(url_or_list, key, scheme, desc)

    def fix_schemes(self, j, key, scheme='https', desc=''):
        """ @todo docstring me """

        if key not in j:
            return False
        if isinstance(j[key], dict):
            if 'url' not in j[key]:
                return False

            logging.info("fix_schemes: scheme=%s", scheme)
            return self._fix_schemes(j[key]['url'], key, scheme, desc)

        logging.info("fix_schemes: scheme=%s", scheme)
        return self._fix_schemes(j[key], key, scheme, desc)

    def schemes_changed(self, schemes):
        if isinstance(schemes, list):
            for scheme in schemes:
                if scheme:
                    return True
            return False

        return schemes

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

        self.dir = dir_name

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        logger2 = logging.getLogger('urllib3')
        logger2.setLevel(logging.CRITICAL)

        parser = jsoncomment.JsonComment(json)

        mask = dir_name + '/' + filespec
        logging.info("==> Processing dir %s", mask)
        for file in glob.glob(mask):
            self.file = os.path.basename(file)
            self.basename = os.path.splitext(self.file)[0]
            logging.info("--> Processing file %s", file)
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
            if self.schemes_changed(scheme):
                logging.info("run: url: scheme=%s", scheme)
                self.fix_schemes(j, 'autoupdate', scheme)
            scheme = self.process(j, 'checkver')
            if 'checkver' in j:
                if isinstance(j['checkver'], dict):
                    scheme = self.process(j['checkver'], 'github')
            if 'architecture' in j:
                scheme = self.process(j['architecture'], '32bit', '',
                                      'architecture')
                if self.schemes_changed(scheme):
                    logging.info("run: architecture.32bit: scheme=%s", scheme)
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            self.fix_schemes(j['autoupdate']['architecture'],
                                             '32bit', scheme,
                                             'autoupdate.architecture')

                scheme = self.process(j['architecture'], '64bit', '',
                                      'architecture')
                if self.schemes_changed(scheme):
                    logging.info("run: architecture.64bit: scheme=%s", scheme)
                    if 'autoupdate' in j:
                        if 'architecture' in j['autoupdate']:
                            self.fix_schemes(j['autoupdate']['architecture'],
                                             '64bit', scheme,
                                             'autoupdate.architecture')
            if self.data != orig_data:
                logging.info("Updating %s", file)
                if os.path.isfile(file + '.bak'):
                    os.remove(file + '.bak')
                os.rename(file, file + '.bak')
                with io.open(file, 'w', encoding='utf-8') as f:
                    f.write(self.data)


checker = CheckURLs()
checker.run()

sys.exit(0)
