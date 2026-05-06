from unittest import TestCase

from src.util import asBool

class TestUtil(TestCase):
    def test_asBool(self):
        assert asBool("TrUe")
        assert asBool("1")
        assert not asBool("FalsE")
        assert not asBool("0")

        self.assertRaises(Exception, asBool, "thing")
        self.assertRaises(Exception, asBool, 1)