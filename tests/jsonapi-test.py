import unittest
from flask import Flask, request, Response
from werkzeug.exceptions import NotFound
from flask_jsontools import (
    jsonapi,
    FlaskJsonClient,
    JsonResponse,
    make_json_response
)


class TestJsonApi(unittest.TestCase):
    def setUp(self):
        # Database
        users = [
            {'id': 1, 'name': 'a'},
            {'id': 2, 'name': 'b'},
            {'id': 3, 'name': 'c'},
        ]

        # Init app
        self.app = app = Flask(__name__)
        self.app.debug = self.app.testing = True
        self.app.test_client_class = FlaskJsonClient

        # Views
        @app.route('/user', methods=['GET'])
        @jsonapi
        def list_users():
            # Just list users
            return users

        @app.route('/user/<int:id>', methods=['GET'])
        @jsonapi
        def get_user(id):
            # Return a user, or http not found
            # Use list_users()
            try:
                return {'user': list_users()[id-1]}
            except IndexError:
                raise NotFound('User #{} not found'.format(id))

        @app.route('/user/<int:id>', methods=['PATCH'])
        @jsonapi
        def patch_user(id):
            # Try custom http codes
            if id == 1:
                return {'error': 'Denied'}, 403

            # Try PATCH method
            req = request.get_json()
            users[id-1] = req['user']
            return users[id-1]

        @app.route('/user/<int:id>', methods=['DELETE'])
        def delete_user(id):
            # Try returning JsonResponse
            if id == 1:
                return JsonResponse({'error': 'Denied'}, 403)

            # Try DELETE method
            del users[id-1]
            return make_json_response(True)

    def testList(self):
        """ Test GET /user: returning json objects """
        with self.app.test_client() as c:
            rv = c.get('/user')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), [ {'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}, {'id': 3, 'name': 'c'} ])

    def testGet(self):
        """ Test GET /user/<id>: HTTP Errors """
        with self.app.test_client() as c:
            # JSON user
            rv = c.get('/user/1')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), {'user': {'id': 1, 'name': 'a'} })

            # Text HTTP
            rv = c.get('/user/99')
            self.assertEqual(rv.status_code, 404)
            self.assertIsInstance(rv, Response)
            print(rv.get_data())
            self.assertIn(b'User #99 not found', rv.get_data())

    def testUpdate(self):
        """ Test PATCH /user/<id>: custom error codes, exceptions """
        with self.app.test_client() as c:
            # JSON error
            rv = c.patch('/user/1')
            self.assertEqual(rv.status_code, 403)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), {'error': 'Denied'})

            # JSON user
            rv = c.patch('/user/2', {'user': {'id': 2, 'name': 'bbb'}})
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), {'id': 2, 'name': 'bbb'})

            # IndexError
            self.assertRaises(IndexError, c.patch, '/user/99', {'user': {}})

    def testDelete(self):
        """ Test DELETE /user/<id>: using JsonResponse """
        with self.app.test_client() as c:
            # JsonResponse
            rv = c.delete('/user/1')
            self.assertEqual(rv.status_code, 403)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), {'error': 'Denied'})

            # make_json_response
            rv = c.delete('/user/2')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)
            self.assertEqual(rv.get_json(), True)
