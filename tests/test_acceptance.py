import pytest
import requests
from os import getenv
from bs4 import BeautifulSoup

try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin

class TestAcceptance(object):
    def setup_class(self):
        self.url = getenv('DAFTPUNK_URL', 'http://localhost:5000')
        self.account_exists = False
        self.account = ''

    def setup_method(self):
        self.session = requests.Session()

    def teardown_method(self):
        if self.account_exists:
            self.account = ''
            self.account_exists = False
            self.sign_out()

    def sign_out(self):
        url = urljoin(self.url, '/signout')
        resp = self.session.get(url)
        self.assertRedirect(resp)

    def create_account(self, username, passwd1, passwd2):
        url = urljoin(self.url, '/new/user')
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        token = soup.find(id="csrf_token")['value']
        self.account = username
        return self.session.post(url, data={
            'csrf_token': token,
            'username': username,
            'password': passwd1,
            'password2': passwd2,
            })

    def add_region(self, county, area, property_type):
        self.ensure_account()

        url = urljoin(self.url, '/new/region')
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        token = soup.find(id="csrf_token")['value']
        return self.session.post(url, data={
            'csrf_token': token,
            'county': county,
            'area': area,
            'property_type': property_type,
            })

    def ensure_account(self):
        if not self.account_exists:
            resp = self.create_account(
                    'test_user', 'test_password', 'test_password')
            self.assertRedirect(resp, '/user/test_user', [302, 303])
            self.account_exists = True

    def assertRedirect(self, resp, dest='/', code=302):
        if type(code) != list:
            code = [code]

        assert resp.history[0].status_code in code
        assert resp.status_code == 200
        assert resp.url == urljoin(self.url, dest)

    def assertFlashes(self, resp, expected=None):
        if not expected:
            expected = []

        soup = BeautifulSoup(resp.text, "html.parser")
        flashes = soup.find('ul', **{'class': 'flashes'}).find_all('li')
        assert len(flashes) == len(expected)
        for i, flash in enumerate(flashes):
            assert flash.text == expected[i]

    def test_homepage(self):
        resp = self.session.get(self.url)
        assert resp.status_code == 200

    def test_new_user_different_passwords(self):
        resp = self.create_account(
                'different_passwords', 'abcdefghi123', 'rstuvwxyz321')
        self.assertRedirect(resp, '/new/user', 303)
        self.assertFlashes(resp, ["Passwords don't match!"])

    def test_new_user_taken_username(self):
        self.ensure_account()

        resp = self.create_account(
                'test_user', 'abcdefghi123', 'abcdefghi123')
        self.assertRedirect(resp, '/new/user', 303)
        self.assertFlashes(resp, ["That username is taken"])

    def test_new_region_success(self):
        self.ensure_account()

        resp = self.add_region('ct1', 260, 'Houses for sale')
        self.assertRedirect(resp, '/user/test_user')

    def test_new_region_duplicate(self):
        self.ensure_account()

        resp = self.add_region('ct1', 266, 'Houses for sale')
        #self.assertRedirect(resp, '/new/region', [302, 303]) # TODO: We should be deleting the region entry first!
        resp = self.add_region('ct1', 266, 'Houses for sale')
        self.assertRedirect(resp, '/new/region', 303)
        self.assertFlashes(resp, ["Duplicate region!"])
