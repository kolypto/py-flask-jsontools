import unittest
import datetime
from flask import Flask, jsonify, json
from flask_jsontools import (
    jsonapi,
    JsonResponse,
    FlaskJsonClient,
    JsonSerializableBase,
    DynamicJSONEncoder,
    SqlAlchemyResponse
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



Base = declarative_base(cls=(JsonSerializableBase,))


class Person(Base):
    __tablename__ = 'person'
    _json_exclude = ['id', 'birth']
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    birth = Column(DateTime)

    def __init__(self, name):
        self.name = name
        self.birth = datetime.datetime.utcnow()


class ModelTest(unittest.TestCase):

    def setUp(self):
        #config flask
        self.app = app = Flask(__name__)
        #self.json_encoder = DynamicJSONEncoder
        self.app.test_client_class = FlaskJsonClient
        self.app.debug = self.app.testing = True

        #config sqlalchemy
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

        #add some data
        self.session.add(Person('oman'))
        self.session.add(Person('twoman'))
        self.session.commit()

        # Views
        @app.route('/person', methods=['GET'])
        def list_persons():
            rs = self.session.query(Person).all()
            return SqlAlchemyResponse(rs)

    def test_model(self):

        rs_first = self.session.query(Person).first()
        x = json.dumps(rs_first, cls=DynamicJSONEncoder)
        self.assertSequenceEqual(x, '{"name": "oman"}')

        rs_all = self.session.query(Person).all()
        y = json.dumps(rs_all, cls=DynamicJSONEncoder)
        self.assertSequenceEqual(y, '[{"name": "oman"}, {"name": "twoman"}]')

    def test_request(self):
        with self.app.test_client() as c:
            rv = c.get('/person')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)
