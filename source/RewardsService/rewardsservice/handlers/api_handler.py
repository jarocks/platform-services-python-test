import json
import math
import re

from pymongo import MongoClient, ASCENDING
from tornado.gen import coroutine
from tornado.web import RequestHandler, HTTPError


class ApiHandler(RequestHandler):
    def initialize(self):
        class_name = self.__class__.__name__
        self.slug = className

        self.client = MongoClient("mongodb", 27017)

    def on_finish(self):
        self.client.close()

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code, kwargs.get('reason', self._reason))
        self.set_header('Content-Type', 'application/json')

        # Allow overwriting the error message for custom errors
        if 'reason' in kwargs:
            message = kwargs['reason']

        # Only show additional details for HTTP errors
        elif 'exc_info' in kwargs and isinstance(kwargs['exc_info'][1], HTTPError):
            message = str(kwargs['exc_info'][1])

        else:
            message = self._reason

        self.finish(json.dumps({'error': {'code': status_code, 'message': message}}))

        raise HTTPError(status_code, message)
