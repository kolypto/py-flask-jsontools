import unittest
import datetime
import json
from flask import Flask, jsonify
from flask_jsontools import (
    FlaskJsonClient,
    JsonSerializableBase,
    DynamicJSONEncoder
)
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import (
        Table,
        Column,
        Integer,
        String,
        ForeignKey,
        Text,
        DateTime,
        SmallInteger,
        PrimaryKeyConstraint
)


class ApiJSONEncoder(DynamicJSONEncoder):
    def default(self, o):
        # Custom formats
        if isinstance(o, datetime.datetime):
            return o.isoformat(' ')
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        return super(DynamicJSONEncoder, self).default(o)


Base = declarative_base(cls=(JsonSerializableBase,))


class Person(Base):
    __tablename__ = 'person'
    __excluded_keys__ = ['id', 'birth']
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    birth = Column(DateTime)

    def __init__(self, name):
        self.name = name
        self.birth = datetime.datetime.utcnow()


class ModelTest(unittest.TestCase):

    def setUp(self):
        #config
        self.app = Flask(__name__)
        #self.json_encoder = ApiJSONEncoder
        self.app.test_client_class = FlaskJsonClient
        self.app.debug = self.app.testing = True

        #app.

        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def test_model(self):
        person = Person('oman')
        self.session.add(person)
        self.session.commit()
        rs = self.session.query(Person).one()
        print(rs.as_dict())

        with self.app.test_request_context():
            #return jsonify(persons=[])
            print( jsonify(dict(json_list = rs.as_dict())) )
