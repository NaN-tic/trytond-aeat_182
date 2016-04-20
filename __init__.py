# This file is part of aeat_182 module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .aeat import *


def register():
    Pool.register(
        Report,
        ReportAccount,
        ReportParty,
        module='aeat_182', type_='model')
