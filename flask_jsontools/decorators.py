from functools import wraps, update_wrapper
from werkzeug.exceptions import HTTPException

from .response import make_json_response


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


class JsonExcApi(object):
    """ Declare the view as JSON API method which formats exceptions as JSON """

    def __init__(self, view):
        self._view = view
        update_wrapper(self, self._view)

    # def __getitem__(self, item):
    #     return getattr(self._view, item)

    def exception(self, e):
        """ Format exception into an object to be JSON-encoded.
            :type e: Exception
            :returns: Exception formatted for JSON , or None if it should be raised instead.
                Alternatively, it can be a tuple of (response, code[, headers])
            :rtype: *|None
        """
        pass

    @jsonapi
    def __call__(self, *args, **kwargs):
        try: self._view(*args, **kwargs)
        except Exception as e:
            # Format exception
            exc = self.exception(e)
            # Not formatted -- re-raise
            if exc is None:
                raise
            # Otherwise format it
            return exc
