#!/usr/bin/env python
import json

from urllib.parse import urlencode

import tornado.testing
from tornado.test.util import unittest
from tornado.web import Application, HTTPError
from tornado.httpclient import HTTPResponse

from tornado.testing import AsyncHTTPTestCase, gen_test

from rewardsservice.settings import settings
from rewardsservice.url_patterns import url_patterns

TEST_MODULES = [
    'rewardsservice.test.customers_test'
]


def all():
    print('Starting unit tests')
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)


class BaseTestCases:
    class APITestCase(AsyncHTTPTestCase):
        _http_method = 'GET'
        _api_endpoint = '/customers'

        def get_app(self):
            return Application(url_patterns, **settings)

        def assertResponse(self, response, expected_code, expected_body, msg=''):
            self.assertIsInstance(response, HTTPResponse, 'Not a valid response')
            self.assertEqual(expected_code, response.code)
            self.assertDictEqual(expected_body, self.fetch_body(response))

        @staticmethod
        def fetch_body(response, k='', default=None):
            try:
                body = response.body

                if isinstance(body, bytes):
                    body = body.decode('utf-8')

                content = json.loads(body)

            except json.JSONDecodeError:
                content = {}

            return content.get(k, default) if k else content

        def fetch(self, params=None, **kwargs):

            if 'method' not in kwargs:
                kwargs['method'] = self._http_method

            path = self._api_endpoint

            if params:
                if kwargs['method'] in ('GET', 'DELETE'):
                    path += '?%s' % urlencode(params)
                else:
                    kwargs['headers'] = {'Content-Type': 'application/x-www-form-urlencoded'}
                    kwargs['body'] = urlencode(params)

            self.http_client.fetch(self.get_url(path), self.stop, **kwargs)
            return self.wait()

    class APIResponseTestCase(APITestCase):
        _tests = None

        @gen_test()
        def test_requests(self, tests=None):
            tests = tests or self._tests
            for (msg, test) in tests.items():
                self._test_request(name='test_%s' % msg, **test)

        def _test_request(self, code=200, params=None, method=None, msg=None, name=None, **kwargs):
            response = self.fetch(params, method=method)

            with self.subTest(msg=name):
                self.assertResponse(response, code, msg)

    class APIErrorTestCase(APIResponseTestCase):
        def _test_request(self, code=None, params=None, msg=None, **kwargs):
            # Allow for substituting params into the expected message
            if msg and params:
                msg = msg.format(**params)

            msg = {'error': {'code': code, 'message': str(HTTPError(code, msg))}}

            super()._test_request(params=params, code=code, msg=msg, **kwargs)


if __name__ == "__main__":
    tornado.testing.main()
