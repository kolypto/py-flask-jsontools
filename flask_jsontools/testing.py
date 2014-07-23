import flask.json
from flask.testing import FlaskClient

from .response import JsonResponse


class FlaskJsonClient(FlaskClient):
    """ JSON-aware test client """

    def open(self, path, json=None, **kwargs):
        """ Open an URL, optionally posting JSON data
        :param path: URI to request
        :type path: str
        :param json: JSON data to post
        :param method: HTTP Method to use. 'POST' by default if data is provided
        :param data: Custom data to post, if required
        """
        # Prepare request
        if json:
            kwargs['data'] = flask.json.dumps(json)
            kwargs['content_type'] = 'application/json'
            kwargs.setdefault('method', 'POST')

        # Request
        rv = super(FlaskJsonClient, self).open(path, **kwargs)
        ':type rv: flask.Response'

        # Response: JSON?
        if rv.mimetype == 'application/json':
            response = flask.json.loads(rv.get_data())
            return JsonResponse(response, rv.status_code, rv.headers)
        return rv
