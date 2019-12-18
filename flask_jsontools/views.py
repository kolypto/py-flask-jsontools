from __future__ import absolute_import
from builtins import object

import inspect
from collections import defaultdict
from functools import wraps

from flask.views import View, with_metaclass
from flask import request
from werkzeug.exceptions import MethodNotAllowed
from future.utils import string_types


def methodview(methods=(), ifnset=None, ifset=None):
    """ Decorator to mark a method as a view.

    NOTE: This should be a top-level decorator!

    :param methods: List of HTTP verbs it works with
    :type methods: str|Iterable[str]
    :param ifnset: Conditional matching: only if the route param is not set (or is None)
    :type  ifnset: str|Iterable[str]|None
    :param ifset:  Conditional matching: only if the route param is     set (and is not None)
    :type  ifset:  str|Iterable[str]|None
    """
    return _MethodViewInfo(methods, ifnset, ifset).decorator


class _MethodViewInfo(object):
    """ Method view info object """

    def decorator(self, func):
        """ Wrapper function to decorate a function """
        # This wrapper seems useless, but in fact is serves the purpose
        # of being a clean namespace for setting custom attributes
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Put the sign
        wrapper._methodview = self

        return wrapper

    @classmethod
    def get_info(cls, func):
        """ :rtype: _MethodViewInfo|None """
        try: return func._methodview
        except AttributeError: return None

    def __init__(self, methods=None, ifnset=None, ifset=None):
        if isinstance(methods, string_types):
            methods = (methods,)
        if isinstance(ifnset, string_types):
            ifnset = (ifnset,)
        if isinstance(ifset, string_types):
            ifset = (ifset,)

        #: Method verbs, uppercase
        self.methods = frozenset([m.upper() for m in methods]) if methods else None

        #: Conditional matching: route params that should not be set
        self.ifnset = frozenset(ifnset) if ifnset else None

        # : Conditional matching: route params that should be set
        self.ifset  = frozenset(ifset ) if ifset  else None

    def matches(self, verb, params):
        """ Test if the method matches the provided set of arguments

        :param verb: HTTP verb. Uppercase
        :type verb: str
        :param params: Existing route parameters
        :type params: set
        :returns: Whether this view matches
        :rtype: bool
        """
        return (self.ifset   is None or self.ifset          <= params) and \
               (self.ifnset  is None or self.ifnset.isdisjoint(params)) and \
               (self.methods is None or verb in self.methods)

    def __repr__(self):
        return '<{cls}: methods={methods} ifset={ifset} ifnset={ifnset}>'.format(
            cls=self.__class__.__name__,
            methods=set(self.methods),
            ifset=set(self.ifset) if self.ifset else '-',
            ifnset=set(self.ifnset) if self.ifnset else '-',
        )

class MethodViewType(type):
    """ Metaclass that collects methods decorated with @methodview """

    def __init__(cls, name, bases, d):
        # Prepare
        methods = set(cls.methods or [])
        methods_map = defaultdict(dict)
        # Methods
        for view_name, func in inspect.getmembers(cls):
            # Collect methods decorated with methodview()
            info = _MethodViewInfo.get_info(func)
            if info is not None:
                # @methodview-decorated view
                for method in info.methods:
                    methods_map[method][view_name] = info
                    methods.add(method)

        # Finish
        cls.methods = tuple(sorted(methods_map.keys()))  # ('GET', ... )
        cls.methods_map = dict(methods_map)  # { 'GET': {'get': _MethodViewInfo } }
        super(MethodViewType, cls).__init__(name, bases, d)


class MethodView(with_metaclass(MethodViewType, View)):
    """ Class-based view that dispatches requests to methods decorated with @methodview """

    def _match_view(self, method, route_params):
        """ Detect a view matching the query

        :param method: HTTP method
        :param route_params: Route parameters dict
        :return: Method
        :rtype: Callable|None
        """
        method = method.upper()
        route_params = frozenset(k for k, v in route_params.items() if v is not None)

        for view_name, info in self.methods_map[method].items():
            if info.matches(method, route_params):
                return getattr(self, view_name)
        else:
            return None

    def dispatch_request(self, *args, **kwargs):
        view = self._match_view(request.method, kwargs)
        if view is None:
            raise MethodNotAllowed(description='No view implemented for {}({})'.format(request.method, ', '.join(kwargs.keys())))
        return view(*args, **kwargs)

    @classmethod
    def route_as_view(cls, app, name, rules, *class_args, **class_kwargs):
        """ Register the view with an URL route
        :param app: Flask application
        :type app: flask.Flask|flask.Blueprint
        :param name: Unique view name
        :type name: str
        :param rules: List of route rules to use
        :type rules: Iterable[str|werkzeug.routing.Rule]
        :param class_args: Args to pass to object constructor
        :param class_kwargs: KwArgs to pass to object constructor
        :return: View callable
        :rtype: Callable
        """
        view = super(MethodView, cls).as_view(name, *class_args, **class_kwargs)
        for rule in rules:
            app.add_url_rule(rule, view_func=view)
        return view


class RestfulViewType(MethodViewType):
    """ Metaclass that automatically defines REST methods """
    methods_map = {
        # view-name: (needs-primary-key, http-method)
        # Collection methods
        'list':    (False, 'GET'),
        'create':  (False, 'POST'),
        # Item methods
        'get':     (True,  'GET'),
        'replace': (True,  'PUT'),
        'update':  (True,  'POST'),
        'delete':  (True,  'DELETE'),
    }

    def __init__(cls, name, bases, d):
        pk = getattr(cls, 'primary_key', ())
        mcs = type(cls)

        # Do not do anything with this class unless the primary key is set
        if pk:
            # Walk through known REST methods
            # list() is used to make sure we have a copy and do not re-wrap the same method twice
            for view_name, (needs_pk, method) in list(mcs.methods_map.items()):
                # Get the view func
                view = getattr(cls, view_name, None)
                if callable(view):  # method exists and is callable
                    # Automatically decorate it with @methodview() and conditions on PK
                    view = methodview(
                        method,
                        ifnset=None if needs_pk else pk,
                        ifset=pk if needs_pk else None,
                    )(view)
                    setattr(cls, view_name, view)

        # Proceed
        super(RestfulViewType, cls).__init__(name, bases, d)


class RestfulView(with_metaclass(RestfulViewType, MethodView)):
    """ Method View that automatically defines the following methods:

        Collection:
            GET /    -> list()
            POST /   -> create()
        Individual item:
            GET /<pk>     -> get()
            PUT /<pk>     -> replace()
            POST /<pk>    -> update()
            DELETE /<pk>  -> delete()

        You just need to specify PK fields
    """

    #: List of route parameters used as a primary key.
    #: If specified -- then we're working with an individual entry, and if not -- with the whole collection
    primary_key = ()


__all__ = ('methodview', 'MethodView', 'RestfulView')
