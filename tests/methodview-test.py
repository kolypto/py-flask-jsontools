import unittest
from functools import wraps
from flask import Flask
from flask_jsontools import jsonapi, FlaskJsonClient
from flask_jsontools import MethodView, methodview, RestfulView


def stupid(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


class CrudView(MethodView):

    decorators = (jsonapi,)

    @stupid
    @methodview('GET', ifnset=('id',))
    def list(self):  # listing
        return [1, 2, 3]

    @methodview('GET', ifset='id')
    @stupid
    def get(self, id):
        return id

    @stupid
    @methodview('CUSTOM', ifset='id')
    @stupid
    def custom(self, id):
        return True


class RestView(RestfulView):

    decorators = (jsonapi,)

    def list(self): return [1,2,3]
    def create(self): return 'ok'
    def get(self, id): return id
    def replace(self, id): return 're'
    def update(self, id): return 'up'
    def delete(self, id): return 'del'

    @methodview('CUSTOM', ifset='id')
    def custom(self, id):
        return ':)'

    @methodview('CUSTOM2', ifset='id')
    def custom2(self, id):
        return ':))'


class RestViewSubclass(RestView):
    primary_key = ('id',)
    custom2 = None  # override




class ViewsTest(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.test_client_class = FlaskJsonClient
        app.debug = app.testing = True

        CrudView.route_as_view(app, 'user', ('/user/', '/user/<int:id>'))
        RestViewSubclass.route_as_view(app, 'rest', ('/api/', '/api/<int:id>'))  # subclass should work as well

        self.app = app

    def _testRequest(self, method, path, expected_code, expected_response=None):
        """ Test a request to the app
        :param method: HTTP method
        :param path:
        :type path:
        :param expected_code:
        :type expected_code:
        :param expected_response:
        :type expected_response:
        :return:
        :rtype:
        """
        with self.app.test_client() as c:
            rv = c.open(path, method=method)
            self.assertEqual(rv.status_code, expected_code)
            if expected_response is not None:
                self.assertEqual(rv.get_json(), expected_response)

    def test_method_view(self):
        """ Test MethodView(), low-level testing """
        self.assertTrue(CrudView.list._methodview.matches('GET', {'a'}))
        self.assertFalse(CrudView.list._methodview.matches('GET', {'id', 'a'}))
        self.assertTrue(CrudView.get._methodview.matches('GET', {'id', 'a'}))
        self.assertFalse(CrudView.get._methodview.matches('GET', {'a'}))
        self.assertTrue(CrudView.custom._methodview.matches('CUSTOM', {'id', 'a'}))
        self.assertFalse(CrudView.custom._methodview.matches('CUSTOM', {'a'}))
        self.assertFalse(CrudView.custom._methodview.matches('????', {'a'}))

    def test_method_view_requests(self):
        """ Test MethodView with real requests """
        self._testRequest('GET', '/user/', 200, [1,2,3])
        self._testRequest('GET', '/user/999', 200, 999)
        self._testRequest('CUSTOM', '/user/', 405)  # No method (by us)
        self._testRequest('CUSTOM', '/user/999', 200, True)
        self._testRequest('UNKNOWN', '/user/999', 405)  # No method (by flask)

    def test_restful_view_requests(self):
        """ Test RestfulView with real requests """
        self._testRequest('GET', '/api/', 200, [1, 2, 3])
        self._testRequest('POST', '/api/', 200, 'ok')

        self._testRequest('GET',     '/api/999', 200, 999)
        self._testRequest('PUT',    '/api/999', 200, 're')
        self._testRequest('POST',   '/api/999', 200, 'up')
        self._testRequest('DELETE',  '/api/999', 200, 'del')
        self._testRequest('CUSTOM',  '/api/999', 200, ':)')
        self._testRequest('CUSTOM2', '/api/999', 405)  # it was overridden by `None`

        self._testRequest('PATCH',     '/api/999', 405)
        self._testRequest('PUT',    '/api/', 405)
        self._testRequest('PATCH',   '/api/', 405)
        self._testRequest('DELETE',  '/api/', 405)
        self._testRequest('CUSTOM',  '/api/', 405)
        self._testRequest('CUSTOM2', '/api/', 405)
