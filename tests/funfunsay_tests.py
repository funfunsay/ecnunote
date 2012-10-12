# -*- coding: utf-8 -*-
"""
    FunFunSay Tests
    ~~~~~~~~~~~~~~

    Tests the FunFunSay application.

    :copyright: (c) 2011 by Armin Ronacher, Jiang Sanyi.
    :license: BSD, see LICENSE for more details.
"""
import os
import funfunsay
import unittest
import tempfile


class FunFunSayTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, funfunsay.app.config['DATABASE'] = tempfile.mkstemp()
        self.app = funfunsay.app.test_client()
        funfunsay.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(funfunsay.app.config['DATABASE'])

    # helper functions

    def register(self, username, password, password2=None, email=None):
        """Helper function to register a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        return self.app.post('/register', data={
            'username':     username,
            'password':     password,
            'password2':    password2,
            'email':        email,
        }, follow_redirects=True)

    def login(self, username, password):
        """Helper function to login"""
        return self.app.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def register_and_login(self, username, password):
        """Registers and logs in in one go"""
        self.register(username, password)
        return self.login(username, password)

    def logout(self):
        """Helper function to logout"""
        return self.app.get('/logout', follow_redirects=True)

    def add_liferule(self, text):
        """Records a liferule"""
        rv = self.app.post('/add_liferule', data={'text': text},
                                    follow_redirects=True)
        if text:
            assert 'Your liferule was recorded' in rv.data
        return rv

    # testing functions

    def test_register(self):
        """Make sure registering works"""
        rv = self.register('user1', 'default')
        assert 'You were successfully registered ' \
               'and can login now' in rv.data
        rv = self.register('user1', 'default')
        assert 'The username is already taken' in rv.data
        rv = self.register('', 'default')
        assert 'You have to enter a username' in rv.data
        rv = self.register('meh', '')
        assert 'You have to enter a password' in rv.data
        rv = self.register('meh', 'x', 'y')
        assert 'The two passwords do not match' in rv.data
        rv = self.register('meh', 'foo', email='broken')
        assert 'You have to enter a valid email address' in rv.data

    def test_login_logout(self):
        """Make sure logging in and logging out works"""
        rv = self.register_and_login('user1', 'default')
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('user1', 'wrongpassword')
        assert 'Invalid password' in rv.data
        rv = self.login('user2', 'wrongpassword')
        assert 'Invalid username' in rv.data

    def test_liferule_recording(self):
        """Check if adding liferules works"""
        self.register_and_login('foo', 'default')
        self.add_liferule('test liferule 1')
        self.add_liferule('<test liferule 2>')
        rv = self.app.get('/')
        assert 'test liferule 1' in rv.data
        assert '&lt;test liferule 2&gt;' in rv.data

    def test_repartees(self):
        """Make sure that repartees work"""
        self.register_and_login('foo', 'default')
        self.add_liferule('the liferule by foo')
        self.logout()
        self.register_and_login('bar', 'default')
        self.add_liferule('the liferule by bar')
        rv = self.app.get('/public')
        assert 'the liferule by foo' in rv.data
        assert 'the liferule by bar' in rv.data

        # bar's repartee should just show bar's liferule
        rv = self.app.get('/')
        assert 'the liferule by foo' not in rv.data
        assert 'the liferule by bar' in rv.data

        # now let's follow foo
        rv = self.app.get('/foo/follow', follow_redirects=True)
        assert 'You are now following &#34;foo&#34;' in rv.data

        # we should now see foo's liferule
        rv = self.app.get('/')
        assert 'the liferule by foo' in rv.data
        assert 'the liferule by bar' in rv.data

        # but on the user's page we only want the user's liferule
        rv = self.app.get('/bar')
        assert 'the liferule by foo' not in rv.data
        assert 'the liferule by bar' in rv.data
        rv = self.app.get('/foo')
        assert 'the liferule by foo' in rv.data
        assert 'the liferule by bar' not in rv.data

        # now unfollow and check if that worked
        rv = self.app.get('/foo/unfollow', follow_redirects=True)
        assert 'You are no longer following &#34;foo&#34;' in rv.data
        rv = self.app.get('/')
        assert 'the liferule by foo' not in rv.data
        assert 'the liferule by bar' in rv.data


if __name__ == '__main__':
    unittest.main()
