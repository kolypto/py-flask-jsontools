|Build Status|

Flask JsonTools
===============

JSON API tools for Flask

Table of Contents
=================

-  View Utilities

   -  @jsonapi

      -  JsonResponse
      -  make\_json\_response()

-  FlaskJsonClient
-  Class-Based Views

   -  MethodView
   -  RestfulView

View Utilities
==============

@jsonapi
--------

Decorate a view function that talks JSON.

Such function can return:

-  tuples of \`(response, status[, headers]): to set custom status code
   and optionally - headers
-  Instances of ```JsonResponse`` <#jsonresponse>`__
-  The result of helper function
   ```make_json_response`` <#make_json_response>`__

Example:

.. code:: python

    from flask.ext.jsontools import jsonapi

    @app.route('/users')
    @jsonapi
    def list_users():
        return [
            {'id': 1, 'login': 'kolypto'},
            #...
        ]
       
    @app.route('/user/<int:id>', methods=['DELETE'])
    def delete_user(id):
        return {'error': 'Access denied'}, 403

JsonResponse
~~~~~~~~~~~~

Extends
```flask.Request`` <http://flask.pocoo.org/docs/api/#incoming-request-data>`__
and encodes the response with JSON. Views decorated with
```@jsonapi`` <#jsonapi>`__ return these objects.

Arguments:

-  ``response``: response data
-  ``status``: status code. Optional, defaults to 200
-  ``headers``: additional headers dict. Optional.
-  ``**kwargs``: additional argumets for
   ```Response`` <http://flask.pocoo.org/docs/api/#response-objects>`__

Methods:

-  ``preprocess_response_data(response)``: Override to get custom
   response behavior.
-  ``get_json()``: Get the original response data.
-  ``__getitem__(key)``: Get an item from the response data

The extra methods allows to reuse views:

.. code:: python

    from flask.ext.jsontools import jsonapi

    @app.route('/user', methods=['GET'])
    @jsonapi
    def list_users():
        return [ { 1: 'first', 2: 'second' } ]
        
    @app.route('/user/<int:id>', methods=['GET'])
    @jsonapi
    def get_user(id):
        return list_users().get_json()[id]  # Long form
        return list_users()[id]  # Shortcut

make\_json\_response()
~~~~~~~~~~~~~~~~~~~~~~

Helper function that actually preprocesses view return value into
```JsonResponse`` <#jsonresponse>`__.

Accepts ``rv`` as any of:

-  tuple of ``(response, status[, headers])``
-  Object to encode as JSON

FlaskJsonClient
===============

FlaskJsonClient is a JSON-aware test client: it can post JSON and parse
JSON responses into ```JsonResponse`` <#jsonresponse>`__.

.. code:: python

    from myapplication import Application
    from flask.ext.jsontools import FlaskJsonClient

    def JsonTest(unittest.TestCase):
        def setUp(self):
            self.app = Application(__name__)
            self.app.test_client_class = FlaskJsonClient
            
        def testCreateUser(self):
            with self.app.test_client() as c:
                rv = c.post('/user/', json={'name': 'kolypto'})
                # rv is JsonResponse
                rv.status_code
                rv.get_json()['user']  # Long form for the previous
                rv['user']  # Shortcut for the previous

Class-Based Views
=================

Module ``flask.ext.jsontools.views`` contains a couple of classes that
allow to build class-based views which dispatch to different methods.

In contrast to
`MethodView <http://flask.pocoo.org/docs/api/#flask.views.MethodView>`__,
this gives much higher flexibility.

MethodView
----------

Using ``MethodView`` class for methods, decorate them with
``@methodview()``, which takes the following arguments:

-  ``methods=()``: Iterable of HTTP methods to use with this method.
-  ``ifnset=None``: Conditional matching. List of route parameter names
   that should *not* be set for this method to match.
-  ``ifset=None``: Conditional matching. List of route parameter names
   that should be set for this method to match.

This allows to map HTTP methods to class methods, and in addition define
when individual methods should match.

Quick example:

.. code:: python

    from flask.ext.jsontools import jsonapi, MethodView, methodview

    class UserView(MethodView):
        # Canonical way to specify decorators for class-based views
        decorators = (jsonapi, )

        @methodview
        def list(self):
            """ List users """
            return db.query(User).all()
           
        @methodview
        def get(self, user_id):
            """ Load a user by id """
            return db.query(User).get(user_id)

    userview = CrudView.as_view('user')
    app.add_url_rule('/user/', view_func=userview)
    app.add_url_rule('/user/<int:user_id>', view_func=userview)

Now, ``GET`` HTTP method is routed to two different methods depending on
conditions. Keep defining more methods to get good routing :)

To simplify the last step of creating the view, there's a helper:

.. code:: python

    UserView.route_as_view(app, 'user', ('/user/', '/user/<int:user_id>'))

RestfulView
-----------

Since ``MethodView`` is mostly useful to expose APIs over collections of
entities, there is a RESTful helper which automatically decorates some
special methods with ``@methodview``.

+---------------+---------------+-------+
| View method   | HTTP method   | URL   |
+===============+===============+=======+
| list()        | GET           | /     |
+---------------+---------------+-------+
| create()      | PUT           | /     |
+---------------+---------------+-------+
| get()         | GET           | /     |
+---------------+---------------+-------+
| replace()     | POST          | /     |
+---------------+---------------+-------+
| update()      | PATCH         | /     |
+---------------+---------------+-------+
| delete()      | DELETE        | /     |
+---------------+---------------+-------+

By subclassing ``RestfulView`` and implementing some of these methods,
you'll get a complete API endpoint with a single class.

It's also required to define the list of primary key fields by defining
the ``primary_key`` property:

.. code:: python

    from flask.ext.jsontools import jsonapi, RestfulView

    class User(RestfulView):
        decorators = (jsonapi, )
        primary_key = ('id',)
        
        #region Operation on the collection
        
        def list():
            return db.query(User).all()
        
        def create():
            db.save(user)
            return user
            
        #endregion
        
        #region Operation on entities
        
        def get(id):
            return db.query(User).get(id)
        
        def replace(id):
            db.save(user, id)
        
        def update(id):
            db.save(user)
           
        def delete(id):
            db.delete(user)
        
        #endregion

When a class like this is defined, its metaclass goes through the
methods and decorates them with ``@methodview``. This way, ``list()``
gets ``@methodview('GET', ifnset=('id',))``, and ``get()`` gets
``@methodview('GET', ifset=('id',))``.

.. |Build Status| image:: https://api.travis-ci.org/kolypto/py-flask-jsontools.png?branch=master
   :target: https://travis-ci.org/kolypto/py-flask-jsontools
