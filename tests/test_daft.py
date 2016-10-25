import unittest

from daftpunk.daft import DaftProperty

class TestDaftProperty(unittest.TestCase):
    EXAMPLE = "http://www.daft.ie/sales/50-hansted-crescent-lucan-dublin/983840/"

    def setUp(self):
        self.prop = DaftProperty.from_url(self.EXAMPLE)

    def test_host(self):
        self.assertEqual(
                "www.daft.ie",
                self.prop.host
                )

    def test_path(self):
        self.assertEqual(
                "/sales/50-hansted-crescent-lucan-dublin/983840/",
                self.prop.path
                )

    def test_category(self):
        self.assertEqual(
                "sales",
                self.prop.category
                )

    def test_tag(self):
        self.assertEqual(
                "50-hansted-crescent-lucan-dublin",
                self.prop.tag
                )

    def test_prop_id(self):
        self.assertEqual(
                "983840",
                self.prop.prop_id
                )
