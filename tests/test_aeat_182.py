# This file is part of aeat_182 module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import doctest
import unittest

from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import doctest_checker
from trytond.tests.test_tryton import doctest_teardown
from trytond.tests.test_tryton import suite as test_suite


class Aeat182TestCase(ModuleTestCase):
    'Test Aeat 182 module'
    module = 'aeat_182'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            Aeat182TestCase))
    suite.addTests(doctest.DocFileSuite('scenario_aeat_182.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            checker=doctest_checker,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
