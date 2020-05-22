# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest
from gospellibrary.catalogs import get_languages


class Test(unittest.TestCase):
    def test_languages(self):
        languages = get_languages()

        english = next((language for language in languages if language['iso639_3Code'] == 'eng'), None)
        self.assertEquals(english['id'], 1)
        self.assertEquals(english['bcp47Code'], 'en')
        self.assertEquals(english['nativeName'], 'English')
        self.assertEquals(english['ldsCode'], '000')

        spanish = next((language for language in languages if language['iso639_3Code'] == 'spa'), None)
        self.assertEquals(spanish['id'], 3)
        self.assertEquals(spanish['bcp47Code'], 'es')
        self.assertEquals(spanish['nativeName'], 'Español')
        self.assertEquals(spanish['ldsCode'], '002')
