# This file is part of aeat_182 module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import aeat


def register():
    Pool.register(
        aeat.Report,
        aeat.ReportAccount,
        aeat.ReportParty,
        module='aeat_182', type_='model')
