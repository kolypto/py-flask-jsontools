[![Build Status](https://api.travis-ci.org/kolypto/py-flask-jsontools.png?branch=master)](https://travis-ci.org/kolypto/py-flask-jsontools)
[![Pythons](https://img.shields.io/badge/python-2.7%20%7C%203.4%E2%80%933.8%20%7C%20pypy-blue.svg)](.travis.yml)


Flask JsonTools
===============

JSON API tools for Flask

Table of Contents
=================

* <a href="#view-utilities">View Utilities</a>
    * <a href="#jsonapi">@jsonapi</a>
        * <a href="#jsonresponse">JsonResponse</a>
        * <a href="#make_json_response">make_json_response()</a>
* <a href="#flaskjsonclient">FlaskJsonClient</a>
* <a href="#class-based-views">Class-Based Views</a>
    * <a href="#methodview">MethodView</a>
    * <a href="#restfulview">RestfulView</a> 



View Utilities
==============

@jsonapi
--------

Decorate a view function that talks JSON.

Such function can return:
    
* tuples of `(response, status[, headers])`: to set custom status code and optionally - headers
* Instances of [`JsonResponse`](#jsonresponse)
* The result of helper function [`make_json_response`](#make_json_response)

Example:

```python
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
```

### JsonResponse

Extends [`flask.Request`](http://flask.pocoo.org/docs/api/#incoming-request-data) and encodes the response with JSON.
Views decorated with [`@jsonapi`](#jsonapi) return these objects.

Arguments:

* `response`: response data
* `status`: status code. Optional, defaults to 200
* `headers`: additional headers dict. Optional.
* `**kwargs`: additional argumets for [`Response`](http://flask.pocoo.org/docs/api/#response-objects)

Methods:

* `preprocess_response_data(response)`: Override to get custom response behavior.
* `get_json()`: Get the original response data.
* `__getitem__(key)`: Get an item from the response data

The extra methods allows to reuse views:

```python
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
```

### make_json_response()
Helper function that actually preprocesses view return value into [`JsonResponse`](#jsonresponse).

Accepts `rv` as any of:

* tuple of `(response, status[, headers])`
* Object to encode as JSON






FlaskJsonClient
===============

FlaskJsonClient is a JSON-aware test client: it can post JSON and parse JSON responses into [`JsonResponse`](#jsonresponse).

```python
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
```





Formatting Utils
================

DynamicJSONEncoder
-----------

In python, de-facto standard for encoding objects of custom classes is the `__json__()` method which returns 
the representation of the object.

`DynamicJSONEncoder` is the implementation of this protocol: if an object has the `__json__()` method, its result if used for
the representation.

You'll definitely want to subclass it to support other types, e.g. dates and times:

```python
from flask.ext.jsontools import DynamicJSONEncoder

class ApiJSONEncoder(DynamicJSONEncoder):
    def default(self, o):
        # Custom formats
        if isinstance(o, datetime.datetime):
            return o.isoformat(' ')
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        
        # Fallback
        return super(ApiJSONEncoder, self).default(o)
```

Now, just install the encoder to your Flask:

```python
from flask import Flask

app = Flask(__name__)
app.json_encoder = DynamicJSONEncoder
```



JsonSerializableBase
--------------------

Serializing SqlAlchemy models to JSON is a headache: if an attribute is present on an instance, this does not mean
it's loaded from the database.

`JsonSerializableBase` is a mixin for SqlAlchemy Declarative Base that adds a magic `__json__()` method, compatible with
[`DynamicJSONEncoder`](#dynamicjsonencoder). When serializing, it makes sure that entity serialization will *never* issue additional requests.

Example:

```python
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.jsontools import JsonSerializableBase

Base = declarative_base(cls=(JsonSerializableBase,))

class User(Base):
    #...
```

Now, you can safely respond with SqlAlchemy models in your JSON views, and jsontools will handle the rest :)






Class-Based Views
=================

Module `flask.ext.jsontools.views` contains a couple of classes that allow to build class-based views
which dispatch to different methods.

In contrast to [MethodView](http://flask.pocoo.org/docs/api/#flask.views.MethodView), this gives much higher flexibility.

MethodView
----------

Using `MethodView` class for methods, decorate them with `@methodview()`, which takes the following arguments:

* `methods=()`: Iterable of HTTP methods to use with this method.
* `ifnset=None`: Conditional matching. List of route parameter names that should *not* be set for this method to match.
* `ifset=None`: Conditional matching. List of route parameter names that should be set for this method to match.

This allows to map HTTP methods to class methods, and in addition define when individual methods should match.

Quick example:

```python
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
```

Now, `GET` HTTP method is routed to two different methods depending on conditions.
Keep defining more methods to get good routing :)

To simplify the last step of creating the view, there's a helper:

```python
UserView.route_as_view(app, 'user', ('/user/', '/user/<int:user_id>'))
```

RestfulView
-----------

Since `MethodView` is mostly useful to expose APIs over collections of entities, there is a RESTful helper which
automatically decorates some special methods with `@methodview`.

| View method | HTTP method | URL     |
|-------------|-------------|---------|
| list()      | GET         | `/`     |
| create()    | POST        | `/`     |
| get()       | GET         | `/<pk>` |
| replace()   | PUT         | `/<pk>` |
| update()    | POST        | `/<pk>` |
| delete()    | DELETE      | `/<pk>` |

By subclassing `RestfulView` and implementing some of these methods, 
you'll get a complete API endpoint with a single class.

It's also required to define the list of primary key fields by defining the `primary_key` property:

```python
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
```

When a class like this is defined, its metaclass goes through the methods and decorates them with `@methodview`.
This way, `list()` gets `@methodview('GET', ifnset=('id',))`, and `get()` gets `@methodview('GET', ifset=('id',))`.
