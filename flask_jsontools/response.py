from functools import partial
from flask import current_app, request, Response, json


class JsonResponse(Response):
    """ Response from a JSON API view """

    @staticmethod
    def _lazy_json(data):
        """ Lazy iterable: jsonify() only when iterated """
        yield ''
        # CHECKME: This hack prevents Flask from providing the correct 'Content-Length' header. is it ok?
        # Prepare response
        indent = 2 if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr else None
        response_str = json.dumps(data, indent=indent)
        yield response_str

    def __init__(self, response, status=None, headers=None, **kwargs):
        """ Init a JSON response
        :param response: Response data
        :type response: *
        :param status: Status code
        :type status: int|None
        :param headers: Additional headers
        :type headers: dict|None
        """
        # Store response
        self._response_data = self.preprocess_response_data(response)

        # Init super
        super(JsonResponse, self).__init__(self._lazy_json(self._response_data), headers=headers, status=status, mimetype='application/json', direct_passthrough=True, **kwargs)

    def preprocess_response_data(self, response):
        """ Preprocess the response data.

        Override this method to have custom handling of the response

        :param response: Return value from the view function
        :type response: *
        :return: Preprocessed value
        """
        return response

    def get_json(self):
        """ Get the response data object (preprocessed) """
        return self._response_data

    def __getitem__(self, item):
        """ Proxy method to get items from the underlying object """
        return self._response_data[item]


def make_json_response(rv):
    """ Make JsonResponse
    :param rv: Response: the object to encode, or tuple (response, status, headers)
    :type rv: tuple|*
    :rtype: JsonResponse
    """
    # Tuple of (response, status, headers)
    status = headers = None
    if isinstance(rv, tuple):
        rv, status, headers = rv + (None,) * (3 - len(rv))

    # JsonResponse
    if isinstance(rv, JsonResponse):
        return rv

    # Data
    return JsonResponse(rv, status, headers)
