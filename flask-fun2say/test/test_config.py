import unittest

import flask
from flask.ext.Fun2say import Fun2say

class FlaskFun2sayConfigTest(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask('test')
        self.context = self.app.test_request_context('/')
        self.context.push()

    def tearDown(self):
        self.context.pop()

    def test_default_config_prefix(self):
        self.app.config['FUN2SAY_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['FUN2SAY_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        fun2say = Fun2say(self.app)
        assert fun2say.api is not None

    def test_custom_config_prefix(self):
        self.app.config['CUSTOM_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['CUSTOM_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['CUSTOM_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['CUSTOM_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        fun2say = Fun2say(self.app, config_prefix='CUSTOM')
        assert fun2say.api is not None

    def test_multiple_fun2says(self):
        self.app.config['FUN2SAY_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['FUN2SAY_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        fun2say1 = Fun2say(self.app)
        assert fun2say1.api is not None

        self.app.config['CUSTOM_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['CUSTOM_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['CUSTOM_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['CUSTOM_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        fun2say2 = Fun2say(self.app, config_prefix='CUSTOM')
        assert fun2say2.api is not None

        assert fun2say1.api is not fun2say2.api

    def test_fails_without_required_configs(self):
        self.app.config['FUN2SAY_CONSUMER_KEY'] = 'keykeykey'
        # self.app.config['FUN2SAY_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['FUN2SAY_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        self.assertRaises(Exception, Fun2say, self.app)

    def test_api_is_none_if_unconfigured(self):
        fun2say = Fun2say()

        assert fun2say.api is None

    def test_init_app(self):
        fun2say = Fun2say()

        self.app.config['FUN2SAY_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['FUN2SAY_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        fun2say.init_app(self.app)
        assert fun2say.api is not None

    def test_fails_with_duplicate_config_prefix(self):
        self.app.config['FUN2SAY_CONSUMER_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_CONSUMER_SECRET'] = 'secretsecret'
        self.app.config['FUN2SAY_ACCESS_TOKEN_KEY'] = 'keykeykey'
        self.app.config['FUN2SAY_ACCESS_TOKEN_SECRET'] = 'secretsecret'

        Fun2say(self.app)
        self.assertRaises(Exception, Fun2say, self.app)

