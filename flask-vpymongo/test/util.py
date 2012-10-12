import flask
import flask.ext.vpymongo
import unittest

class FlaskRequestTest(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask('test')
        self.context = self.app.test_request_context('/')
        self.context.push()

    def tearDown(self):
        self.context.pop()

class FlaskVPyMongoTest(FlaskRequestTest):

    def setUp(self):
        super(FlaskVPyMongoTest, self).setUp()

        self.dbname = self.__class__.__name__
        self.mongo = flask.ext.vpymongo.PyMongoV(self.app)
        self.mongo.cx.drop_database(self.dbname)

    def tearDown(self):
        self.mongo.cx.drop_database(self.dbname)

        super(FlaskVPyMongoTest, self).tearDown()

