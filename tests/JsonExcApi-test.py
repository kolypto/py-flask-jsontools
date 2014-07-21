import unittest
from flask import Flask
from werkzeug.exceptions import HTTPException, NotFound

from flask.ext.jsontools import JsonClient, JsonExcApi


class jsonapi(JsonExcApi):
    """ Custom @jsonapi with error formatter """
    def exception(self, e):
        if isinstance(e, HTTPException):
            return {'error': dict(
                name=type(e).__name__,
                title=e.name,
                message=e.description
            )}, e.code
        elif isinstance(e, RuntimeError):
            return {'error': dict(
                name=type(e).__name__,
                title=type(e).__name__,
                message=e.message
            )}


class TestJsonExcApi(unittest.TestCase):
    def setUp(self):
        # Init app
        self.app = app = Flask(__name__)
        self.app.debug = self.app.testing = True
        self.app.test_client_class = JsonClient

        @app.route('/e404')
        @jsonapi
        def e404():
            raise NotFound('Nothing')

        @app.route('/eRuntime')
        @jsonapi
        def eRuntime():
            raise RuntimeError('Problem')

        @app.route('/eValue')
        @jsonapi
        def eValue():
            raise ValueError('Value')

    def test_e404(self):
        """ Test: HttpError, formatted """
        with self.app.test_client() as c:
            rv = c.get('/e404')
            self.assertEqual(rv.status_code, 404)
            self.assertEqual(rv['error'], {'name': 'NotFound', 'title': 'Not Found', 'message': 'Nothing'})

    def test_eRuntime(self):
        """ Test: RuntimeError, formatted """
        with self.app.test_client() as c:
            rv = c.get('/eRuntime')
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['error'], {'name': 'RuntimeError', 'title': 'RuntimeError', 'message': 'Problem'})

    def test_eValue(self):
        """ Test: Unknown error, passed by """
        with self.app.test_client() as c:
            self.assertRaises(ValueError, c.get, '/eValue')
