from collections import defaultdict
from flask.views import View, with_metaclass
from flask import request
from werkzeug.exceptions import MethodNotAllowed


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
        func._methodview = self
        return func

    @classmethod
    def get_info(cls, func):
        """ :rtype: _MethodViewInfo|None """
        try: return func._methodview
        except AttributeError: return None

    def __init__(self, methods=None, ifnset=None, ifset=None):
        if isinstance(methods, basestring):
            methods = (methods,)
        if isinstance(ifnset, basestring):
            ifnset = (ifnset,)
        if isinstance(ifset, basestring):
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


class MethodViewType(type):
    """ Metaclass that collects methods decorated with @methodview """

    def __new__(cls, name, bases, d):
        rv = type.__new__(cls, name, bases, d)

        # Methods
        view_methods = set(rv.methods or [])
        methods_map = defaultdict(dict)
        for name, func in d.items():
            # Collect methods decorated with method()
            info = _MethodViewInfo.get_info(func)
            if name.startswith('_') or info is None:
                continue
            for method in info.methods:
                methods_map[method][name] = info
                view_methods.add(method)

        # Finish
        rv.methods = tuple(sorted(view_methods))  # ('GET', ... )
        rv.methods_map = dict(methods_map)  # { 'GET': {'get': _MethodViewInfo } }
        return rv


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

        for name, info in self.methods_map[method].items():
            if info.matches(method, route_params):
                return getattr(self, name)
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
        :type app: flask.Flask
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
        'create':  (False, 'PUT'),
        # Item methods
        'get':     (True,  'GET'),
        'replace': (True,  'POST'),
        'update':  (True,  'PATCH'),
        'delete':  (True,  'DELETE'),
    }

    def __new__(cls, name, bases, d):
        pk = d.get('primary_key', ())

        # Automatically decorate the existing methods
        found_methods = False
        for view_name, (needs_pk, method) in cls.methods_map.items():
            if view_name in d:
                found_methods = True
                d[view_name] = methodview(
                    method,
                    ifnset=None if needs_pk else pk,
                    ifset=pk if needs_pk else None,
                )(d[view_name])

        if found_methods:
            assert pk, 'Primary key for RestfulView "{}" should be defined'.format(name)
            assert isinstance(pk, (list, tuple)), 'Primary key for RestfulView "{}" should be iterable'.format(name)

        # Proceed
        return super(RestfulViewType, cls).__new__(cls, name, bases, d)


class RestfulView(with_metaclass(RestfulViewType, MethodView)):
    """ Method View that automatically defines the following methods:

        Collection:
            GET /   -> list()
            PUT /   -> create()
        Individual item:
            GET /<pk>    -> get()
            POST /<pk>   -> replace()
            PATCH /<pk>  -> update()
            DELETE /<pk> -> delete()

        You just need to specify PK fields
    """

    #: List of route parameters used as a primary key.
    #: If specified -- then we're working with an individual entry, and if not -- with the whole collection
    #: HTTP methods mostly do not intersect, but 'GET' is special here
    primary_key = ()


__all__ = ('methodview', 'MethodView', 'RestfulView')
