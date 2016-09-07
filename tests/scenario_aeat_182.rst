=======================
AEAT 182 Model Scenario
=======================

Imports::
    >>> import datetime
    >>> import os
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import install_modules
    >>> from trytond.modules.currency.tests.tools import get_currency
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()
    >>> last_year = today - relativedelta(years=1)
    >>> two_years_ago = last_year - relativedelta(years=1)
    >>> three_years_ago = two_years_ago - relativedelta(years=1)

Install aeat_182 module::

    >>> config = install_modules('aeat_182')

Create company::

    >>> eur = get_currency('EUR')
    >>> _ = create_company(currency=eur)
    >>> company = get_company()
    >>> identifier = company.party.identifiers.new()
    >>> identifier.code = 'ES00000000T'
    >>> identifier.type = 'eu_vat'
    >>> identifier.save()

Create fiscal year::

    >>> fiscalyear1 = create_fiscalyear(company, three_years_ago)
    >>> fiscalyear1.click('create_period')
    >>> period1 = fiscalyear1.periods[0]
    >>> fiscalyear2 = create_fiscalyear(company, two_years_ago)
    >>> fiscalyear2.click('create_period')
    >>> period2 = fiscalyear2.periods[0]
    >>> fiscalyear3 = create_fiscalyear(company, last_year)
    >>> fiscalyear3.click('create_period')
    >>> period3 = fiscalyear3.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> revenue.party_required = True
    >>> revenue.save()
    >>> revenue.reload()

Create tax::

    >>> Tax = Model.get('account.tax')
    >>> tax = set_tax_code(create_tax(Decimal('.10')))
    >>> tax.save()

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.party_type = 'person'
    >>> identifier = party.identifiers.new()
    >>> identifier.type = 'eu_vat'
    >>> identifier.code = 'ES00000001R'
    >>> party.save()
    >>> party2 = Party(name='Party2')
    >>> party2.party_type = 'organization'
    >>> identifier = party2.identifiers.new()
    >>> identifier.type = 'eu_vat'
    >>> identifier.code = 'ES00000002W'
    >>> party2.save()
    >>> party3 = Party(name='Party3')
    >>> party3.party_type = 'person'
    >>> identifier = party3.identifiers.new()
    >>> identifier.type = 'eu_vat'
    >>> identifier.code = 'ES00000003A'
    >>> party3.save()

Create First Year Move Line Donations::

    >>> Journal = Model.get('account.journal')
    >>> Move = Model.get('account.move')
    >>> journal_revenue, = Journal.find([
    ...         ('code', '=', 'REV'),
    ...         ])
    >>> move = Move()
    >>> move.period = period1
    >>> move.journal = journal_revenue
    >>> move.date = period1.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(50)
    >>> line.party = party
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(50)
    >>> line.party = party
    >>> move.save()

    >>> move = Move()
    >>> move.period = period1
    >>> move.journal = journal_revenue
    >>> move.date = period1.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(50)
    >>> line.party = party
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(50)
    >>> line.party = party
    >>> move.save()

    >>> move = Move()
    >>> move.period = period1
    >>> move.journal = journal_revenue
    >>> move.date = period1.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(100)
    >>> line.party = party2
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(100)
    >>> line.party = party2
    >>> move.save()

    >>> move = Move()
    >>> move.period = period1
    >>> move.journal = journal_revenue
    >>> move.date = period1.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(250)
    >>> line.party = party3
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(250)
    >>> line.party = party3
    >>> move.save()

Generate First Year 182 Report::

    >>> Report = Model.get('aeat.182.report')
    >>> ReportParty = Model.get('aeat.182.report.party')
    >>> report = Report()
    >>> report.company = company
    >>> report.fiscalyear = fiscalyear1
    >>> report.fiscalyear_code = fiscalyear1.end_date.year
    >>> report.presentation = 'printed'
    >>> report.declarant_nature = '1'
    >>> report.type = 'N'
    >>> report.accounts.append(revenue)
    >>> report.click('calculate')
    >>> report.reload()
    >>> report.total_number_of_donor_records
    3
    >>> report.amount_of_donations
    Decimal('450.0')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000001R'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('100.0')
    >>> report_party.percentage_deduction
    Decimal('75')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000002W'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('100.0')
    >>> report_party.percentage_deduction
    Decimal('35')

Create Second Year Move Line Donations::

    >>> move = Move()
    >>> move.period = period2
    >>> move.journal = journal_revenue
    >>> move.date = period2.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(160)
    >>> line.party = party
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(160)
    >>> line.party = party
    >>> move.save()

    >>> move = Move()
    >>> move.period = period2
    >>> move.journal = journal_revenue
    >>> move.date = period2.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(100)
    >>> line.party = party2
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(100)
    >>> line.party = party2
    >>> move.save()

    >>> move = Move()
    >>> move.period = period2
    >>> move.journal = journal_revenue
    >>> move.date = period2.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(200)
    >>> line.party = party3
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(200)
    >>> line.party = party3
    >>> move.save()

Generate Second Year 182 Report::

    >>> Account = Model.get('account.account')
    >>> revenue = Account(revenue.id)
    >>> report = Report()
    >>> report.company = company
    >>> report.fiscalyear = fiscalyear2
    >>> report.fiscalyear_code = fiscalyear2.end_date.year
    >>> report.presentation = 'printed'
    >>> report.declarant_nature = '1'
    >>> report.type = 'N'
    >>> report.accounts.append(revenue)
    >>> report.click('calculate')
    >>> report.reload()
    >>> report.total_number_of_donor_records
    3
    >>> report.amount_of_donations
    Decimal('460.0')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000001R'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('160.0')
    >>> report_party.percentage_deduction
    Decimal('30')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000002W'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('100.0')
    >>> report_party.percentage_deduction
    Decimal('35')

Create Third Year Move Line Donations::

    >>> move = Move()
    >>> move.period = period3
    >>> move.journal = journal_revenue
    >>> move.date = period3.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(160)
    >>> line.party = party
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(160)
    >>> line.party = party
    >>> move.save()

    >>> move = Move()
    >>> move.period = period3
    >>> move.journal = journal_revenue
    >>> move.date = period3.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(100)
    >>> line.party = party2
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(100)
    >>> line.party = party2
    >>> move.save()

    >>> move = Move()
    >>> move.period = period3
    >>> move.journal = journal_revenue
    >>> move.date = period2.start_date
    >>> line = move.lines.new()
    >>> line.account = revenue
    >>> line.credit = Decimal(200)
    >>> line.party = party3
    >>> line = move.lines.new()
    >>> line.account = receivable
    >>> line.debit = Decimal(200)
    >>> line.party = party3
    >>> move.save()

Generate Third Year 182 Report::

    >>> revenue = Account(revenue.id)
    >>> report = Report()
    >>> report.company = company
    >>> report.fiscalyear = fiscalyear3
    >>> report.fiscalyear_code = fiscalyear3.end_date.year
    >>> report.presentation = 'printed'
    >>> report.declarant_nature = '1'
    >>> report.type = 'N'
    >>> report.accounts.append(revenue)
    >>> report.click('calculate')
    >>> report.reload()
    >>> report.total_number_of_donor_records
    3
    >>> report.amount_of_donations
    Decimal('460.0')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000001R'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('160.0')
    >>> report_party.percentage_deduction
    Decimal('35')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000002W'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('100.0')
    >>> report_party.percentage_deduction
    Decimal('40')
    >>> report_party, = ReportParty.find([
    ...         ('party_vat', '=', '00000003A'),
    ...         ('report', '=', report.id),
    ...         ])
    >>> report_party.amount
    Decimal('200.0')
    >>> report_party.percentage_deduction
    Decimal('30')

Generate AEAT 182 Model File::

    >>> report.click('process')
    >>> bool(report.file_)
    True
