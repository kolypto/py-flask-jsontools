from __future__ import absolute_import
from builtins import object

from flask.json import JSONEncoder


class DynamicJSONEncoder(JSONEncoder):
    """ JSON encoder for custom classes:

        Uses __json__() method if available to prepare the object.
        Especially useful for SQLAlchemy models
    """

    def default(self, o):
        # Custom JSON-encodeable objects
        if hasattr(o, '__json__'):
            return o.__json__()

        # Default
        return super(DynamicJSONEncoder, self).default(o)


#region SqlAlchemy Tools

try:
    from sqlalchemy import inspect
    from sqlalchemy.orm.state import InstanceState
except ImportError as e:
    def __nomodule(*args, **kwargs): raise e
    inspect = __nomodule
    InstanceState = __nomodule


class JsonSerializableBase(object):
    """ Declarative Base mixin to allow objects serialization

        Defines interfaces utilized by :cls:ApiJSONEncoder

        In particular, it defines the __json__() method that converts the
        SQLAlchemy model to a dictionary. It iterates over model fields
        (DB columns and relationships) and collects them in the dictionary.

        The important aspect here is that it collects only loaded attributes.
        For example, all relationships are lazy-loaded by default, so they will
        not be present in the output JSON unless you use eager loading.
        So if you want to include nested objects into the JSON output, then
        you should use eager loading.

        Beside the __json__() method, this base defines two properties:
          _json_include = []
          _json_exclude = []

        They both are needed to customize this loaded-only-fields serialization.

          - _json_include is the list of strings (DB columns and relationship
           names) that should be present in JSON, even if they are not loaded.
           Useful for hybrid properties and relationships that cannot be loaded
           eagerly. Just put their names to the _json_include list.

          - _json_exclude is the black-list that actually removes fields from
            the output JSON representation. It is applied last, so it beats all
            other things like _json_include.
            Useful for hiding sensitive data, like password hashes stored in DB.
    """

    _json_include = []
    _json_exclude = []

    def __json__(self, excluded_keys=set()):
        ins = inspect(self)

        columns = set(ins.mapper.column_attrs.keys())
        relationships = set(ins.mapper.relationships.keys())
        unloaded = ins.unloaded
        expired = ins.expired_attributes
        include = set(self._json_include)
        exclude = set(self._json_exclude) | excluded_keys

        # This set of keys determines which fields will be present in
        # the resulting JSON object.
        # Here we initialize it with properties defined by the model class,
        # and then add/delete some columns below in a tricky way.
        keys = columns | relationships


        # 1. Remove not yet loaded properties.
        # Basically this is needed to serialize only .join()'ed relationships
        # and omit all other lazy-loaded things.
        if not ins.transient:
            # If the entity is not transient -- exclude unloaded keys
            # Transient entities won't load these anyway, so it's safe to
            # include all columns and get defaults
            keys -= unloaded

        # 2. Re-load expired attributes.
        # At the previous step (1) we substracted unloaded keys, and usually
        # that includes all expired keys. Actually we don't want to remove the
        # expired keys, we want to refresh them, so here we have to re-add them
        # back. And they will be refreshed later, upon first read.
        if ins.expired:
            keys |= expired

        # 3. Add keys explicitly specified in _json_include list.
        # That allows you to override those attributes unloaded above.
        # For example, you may include some lazy-loaded relationship() there
        # (which is usually removed at the step 1).
        keys |= include

        # 4. For objects in `deleted` or `detached` state, remove all
        # relationships and lazy-loaded attributes, because they require
        # refreshing data from the DB, but this cannot be done in these states.
        # That is:
        #  - if the object is deleted, you can't refresh data from the DB
        #    because there is no data in the DB, everything is deleted
        #  - if the object is detached, then there is no DB session associated
        #    with the object, so you don't have a DB connection to send a query
        # So in both cases you get an error if you try to read such attributes.
        if ins.deleted or ins.detached:
            keys -= relationships
            keys -= unloaded

        # 5. Delete all explicitly black-listed keys.
        # That should be done last, since that may be used to hide some
        # sensitive data from JSON representation.
        keys -= exclude

        return { key: getattr(self, key)  for key in keys }

#endregion
