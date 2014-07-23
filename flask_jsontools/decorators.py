from functools import wraps, update_wrapper, partial

from .response import normalize_response_value, make_json_response


def jsonapi(f):
    """ Declare the view as a JSON API method

        This converts view return value into a :cls:JsonResponse.

        The following return types are supported:
            - tuple: a tuple of (response, status, headers)
            - any other object is converted to JSON
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        rv = f(*args, **kwargs)
        return make_json_response(rv)
    return wrapper
