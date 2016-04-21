# -*- coding: utf-8 -*-
# This file is part of aeat_182 module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelSQL, ModelView, fields, Workflow, Unique
from trytond.pool import Pool
from trytond.pyson import And, Bool, Eval, Not
from trytond.transaction import Transaction
import unicodedata

from sql.aggregate import Sum


__all__ = ['Report', 'ReportAccount', 'ReportParty']
KEY = [
    ('A', 'A. Donations not included in the priority activities or '
        'sponsorship programs established by Law on State Budget'),
    ('B', 'B. Donations included in activities or sponsorship '
        'priority programs identified by Law on State Budget'),
    ('C', 'C. Contribution to heritage disabled.'),
    ('D', 'D. Provision of heritage disabled'),
    ]
AUTONOMOUS_COMUNITY = [
    (None, ''),
    ('01', u'01. Andalucía'),
    ('02', u'02. Aragón'),
    ('03', u'03. Principado de Asturias'),
    ('04', u'04. Illes Balears'),
    ('05', u'05. Canarias'),
    ('06', u'06. Cantabria'),
    ('07', u'07. Castilla la Macha'),
    ('08', u'08. Castilla y León'),
    ('09', u'09. Catalunya'),
    ('10', u'10. Extremadura'),
    ('11', u'11. Galicia'),
    ('12', u'12. Comunidad de Madrid'),
    ('13', u'13. Región de Murcia'),
    ('16', u'16. La Rioja'),
    ('17', u'17. Comunidad Valenciana'),
    ]
TYPE_OF_GOOD = [
    (None, ''),
    ('I', 'I. Property'),
    ('V', 'V. Transferable Securities'),
    ('O', 'O. Other'),
    ]
IDENTIFICATION_OF_GOOD = [
    (None, ''),
    ('NRC', 'NCR. Real State'),
    ('ISIN', 'ISIN. transferable securities'),
    ]


def remove_accents(unicode_string):
    if isinstance(unicode_string, str):
        unicode_string_bak = unicode_string
        try:
            unicode_string = unicode_string_bak.decode('iso-8859-1')
        except UnicodeDecodeError:
            try:
                unicode_string = unicode_string_bak.decode('utf-8')
            except UnicodeDecodeError:
                return unicode_string_bak

    if not isinstance(unicode_string, unicode):
        return unicode_string

    unicode_string_nfd = ''.join(
        (c for c in unicodedata.normalize('NFD', unicode_string)
            if (unicodedata.category(c) != 'Mn'
                or c in (u'\u0327', u'\u0303'))  # Avoids normalize ç and ñ
            ))
    # It converts nfd to nfc to allow unicode.decode()
    return unicodedata.normalize('NFC', unicode_string_nfd)


class Report(Workflow, ModelSQL, ModelView):
    'AEAT 182 Report'
    __name__ = 'aeat.182.report'
    company = fields.Many2One('company.company', 'Company',
        states={
            'required': True,
            'readonly': Eval('state') != 'draft',
            }, depends=['state'])
    company_vat = fields.Char('VAT number', size=9, states={
            'required': True,
            'readonly': Eval('state') == 'done',
            }, depends=['state'])
    company_name = fields.Char('Name')
    company_phone = fields.Char('Phone', size=9,
        states={
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            }, depends=['state'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
            'get_currency_digits')
    currency = fields.Function(fields.Many2One('currency.currency',
        'Currency',
            states={
                'invisible': True,
                }), 'get_currency')
    fiscalyear = fields.Many2One('account.fiscalyear', 'Fiscal Year',
        required=True, states={
            'readonly': Eval('state') != 'draft',
            }, depends=['state'])
    fiscalyear_code = fields.Integer('Fiscal Year Code',
        states={
            'required': True,
            'readonly': Eval('state') != 'draft',
            }, depends=['state'],
        help='The four digits of the calendar year the corresponding '
            'declaration is made.')
    presentation = fields.Selection([
            ('printed', 'Printed'),
            ('support', 'Support'),
            ], 'Presentation',
        states={
            'required': True,
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            }, depends=['state'])
    declarant_nature = fields.Selection([
            ('non_profit_entity', 'Non-profit Entity'),
            ('foundation', 'Foundation'),
            ('protected_heritage', 'Protected Heritage'),
            ], 'Nature of the Declarant',
        states={
            'readonly': Eval('state') != 'draft',
            }, depends=['state'])
    protected_heritage_vat = fields.Char('Protected Heritage VAT', states={
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            'invisible': Eval('declarant_nature') != 'protected_heritage',
            }, depends=['state', 'declarant_nature'])
    protected_heritage_name = fields.Char('Protected Heritage Name', states={
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            'invisible': Eval('declarant_nature') != 'protected_heritage',
            }, depends=['state', 'declarant_nature'])
    type = fields.Selection([
            ('N', 'Normal'),
            ('C', 'Complementary'),
            ('S', 'Substitutive')
            ], 'Type',
        states={
            'required': True,
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            }, depends=['state'])
    previous_number = fields.Char('Previous Declaration Number', size=13,
        states={
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            'invisible': Eval('type') == 'N',
            }, depends=['state', 'type'])
    total_number_of_donor_records = fields.Function(fields.Integer(
        'Total number of donor records'), 'get_totals')
    amount_of_donations = fields.Function(fields.Numeric('Amount of donations',
        digits=(16, 2)), 'get_totals')
    date = fields.Date('Date', readonly=True)
    contact_name = fields.Char('Name And Surname Contact', size=40,
        states={
            'readonly': ~Eval('state').in_(['draft', 'calculated']),
            }, depends=['state'])
    report_parties = fields.One2Many('aeat.182.report.party', 'report',
        'Party Donations', states={
            'readonly': Eval('state') != 'calculated',
            }, depends=['state'])
    total_sheets = fields.Function(fields.Integer('Total Sheets'),
        'get_total_sheets')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('calculated', 'Calculated'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
            ], 'State', readonly=True)
    file_ = fields.Binary('File', filename='filename', states={
            'invisible': Eval('state') != 'done',
            })
    filename = fields.Function(fields.Char("File Name"),
        'get_filename')
    accounts = fields.Many2Many('aeat.182.report.account', 'report', 'account',
        'Accounts')
    years_for_pluriannual_donation = fields.Integer(
        'Minimal Number of Years for Pluriannual Donation')
    donation_amount_threshold = fields.Numeric('Donation Amount Threshold for '
        'the Applying of the Second Scale of Deduction',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    first_less_physical = fields.Numeric('Deductible Percentage of First '
        'Donation of Less Amount of Physical Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    first_greater_physical = fields.Numeric('Deductible Percentage of First '
        'Donation of Greater Amount of Physical Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    pluriannual_physical = fields.Numeric('Deductible Percentage of '
        'Pluriannual Donation of Physical Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    first_less_artificial = fields.Numeric('Deductible Percentage of First '
        'Donation of Less Amount of Artificial Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    first_greater_artificial = fields.Numeric('Deductible Percentage of First '
        'Donation of Greater Amount of Artificial Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    pluriannual_artificial = fields.Numeric('Deductible Percentage of '
        'Pluriannual Donation of Artificial Person',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])

    @classmethod
    def __setup__(cls):
        super(cls, Report).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('code_uniq', Unique(t, t.fiscalyear, t.company),
                'Report must be unique by fiscalyear and company'),
        ]
        cls._error_messages.update({
                'invalid_currency': ('Currency in AEAT 182 report "%s" must be'
                    ' Euro.')
                })
        cls._buttons.update({
                'draft': {
                    'invisible': ~Eval('state').in_(['calculated',
                            'cancelled']),
                    'icon': 'tryton-go-previous',
                    },
                'calculate': {
                    'invisible': ~Eval('state').in_(['draft']),
                    'icon': 'tryton-go-next',
                    },
                'process': {
                    'invisible': ~Eval('state').in_(['calculated']),
                    'icon': 'tryton-ok',
                    },
                'cancel': {
                    'invisible': Eval('state').in_(['cancelled']),
                    'icon': 'tryton-cancel',
                    },
                })
        cls._transitions |= set((
                ('draft', 'calculated'),
                ('draft', 'cancelled'),
                ('calculated', 'draft'),
                ('calculated', 'done'),
                ('calculated', 'cancelled'),
                ('done', 'cancelled'),
                ('cancelled', 'draft'),
                ))

    @classmethod
    def validate(cls, reports):
        for report in reports:
            report.check_euro()

    def check_euro(self):
        if self.currency.code != 'EUR':
            self.raise_user_error('invalid_currency', self.rec_name)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def get_currency_digits(cls, records, name=None):
        res = {r.id: r.currency.digits for r in records}
        return res

    @classmethod
    def get_total_sheets(cls, reports, name=None):
        res = {r.id: len(r.report_parties) / 6 + 1 for r in reports}
        return res

    @staticmethod
    def default_declarant_nature():
        return 'foundation'

    @staticmethod
    def default_fiscalyear():
        FiscalYear = Pool().get('account.fiscalyear')
        return FiscalYear.find(
            Transaction().context.get('company'), exception=False)

    @staticmethod
    def default_type():
        return 'N'

    @staticmethod
    def default_presentation():
        return 'printed'

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_periods_for_pluriannual_donation():
        return 2

    @staticmethod
    def default_donation_amount_threshold():
        return Decimal('150')

    @staticmethod
    def default_first_less_physical():
        return Decimal('75')

    @staticmethod
    def default_first_greater_physical():
        return Decimal('30')

    @staticmethod
    def default_pluriannual_physical():
        return Decimal('35')

    @staticmethod
    def default_first_less_artificial():
        return Decimal('35')

    @staticmethod
    def default_first_greater_artificial():
        return Decimal('35')

    @staticmethod
    def default_pluriannual_artificial():
        return Decimal('40')

    def get_rec_name(self, name):
        return '%s - %s' % (self.company.rec_name, self.fiscalyear.name)

    @classmethod
    def get_totals(cls, reports, names):
        res = {
            'total_number_of_donor_records':
                {r.id: len(r.report_parties) for r in reports},
            'amount_of_donations':
                {r.id: Decimal(sum([l.amount for l in r.report_parties]))
                    if r.report_parties else Decimal('0.0')
                    for r in reports},
            }
        for key in res.keys():
            if key not in names:
                del res[key]
        return res

    def get_currency(self, name):
        return self.company.currency.id

    def get_filename(self, name):
        return 'aeat182-%s.txt' % self.fiscalyear_code

    @fields.depends('fiscalyear')
    def on_change_with_fiscalyear_code(self):
        code = None
        if self.fiscalyear:
            code = self.fiscalyear.start_date.year
        return code

    @fields.depends('company')
    def on_change_company(self):
        if self.company:
            party = self.company.party
            company_vat = getattr(party, 'vat_code', None)
            phone = getattr(party, 'phone', None)
            self.company_vat = company_vat and company_vat[-9:] or ''
            self.company_name = party.name
            self.company_phone = phone or ''

    def pluriannual_applicable(self, report_party):
        previous_years = []
        number_of_previous_years = self.years_for_pluriannual_donation - 1
        for count in range(number_of_previous_years):
            year = report_party['fiscalyear_code'] - (count + 1)
            previous_years.append(year)
        report_parties = ReportParty.search([
                ('party_vat', '=', report_party['party_vat']),
                ('fiscalyear_code', 'in', previous_years)
                ])
        applicable = len(report_parties) == number_of_previous_years
        if applicable:
            amount = report_party['amount']
            for r_party in sorted(report_parties,
                    key=lambda x: x.fiscalyear_code,
                    reverse=True):
                applicable &= r_party.amount <= amount
                amount = r_party.amount
        return applicable

    def get_report_parties(self, fiscalyear):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        Party = pool.get('party.party')
        Account = pool.get('account.account')
        Move = pool.get('account.move')
        Period = pool.get('account.period')
        cursor = Transaction().connection.cursor()

        line = MoveLine.__table__()
        party = Party.__table__()
        account = Account.__table__()
        move = Move.__table__()
        period = Period.__table__()
        map_party_type = {
            'organization': 'J',
            'person': 'F',
            }
        query = (line
            .join(account, 'LEFT', condition=(line.account == account.id))
            .join(move, 'LEFT', condition=(line.move == move.id))
            .join(period, 'LEFT', condition=(move.period == period.id))
            .select(
                line.party,
                (Sum(line.credit) - Sum(line.debit)),
                where=(
                        (period.fiscalyear == fiscalyear.id)
                    &
                        (account.id.in_(
                                [a.id for a in self.accounts]))
                    ),
                group_by=(
                    account.code,
                    line.party,
                    ),
                )
            )
        cursor.execute(*query)
        report_parties = []
        report_id = self.id
        companty_id = self.company.id
        fiscalyear_code = self.fiscalyear_code
        for record in cursor.fetchall():
            party = Party(record[0])
            address = party.address_get()
            subdivision_code = (address and address.subdivision
                    and address.subdivision.code or None)
            report_party = {
                'party_vat': party.vat_code,
                'party_name': party.name,
                'nature': map_party_type.get(party.party_type),
                'party_subdivision_code': subdivision_code,
                'amount': record[1],
                'key': 'A',
                'report': report_id,
                'company': companty_id,
                'fiscalyear_code': fiscalyear_code,
                }
            report_parties.append(report_party)
        return report_parties

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, reports):
        cls._delete_lines(reports)

    @classmethod
    @ModelView.button
    @Workflow.transition('calculated')
    def calculate(cls, reports):
        pool = Pool()
        ReportParty = pool.get('aeat.182.report.party')
        Date = pool.get('ir.date')

        cls._delete_lines(reports)
        today = Date.today()

        vlist = []
        for report in reports:
            if not report.accounts or not report.fiscalyear:
                continue
            report.date = today

            report_parties = report.get_report_parties(report.fiscalyear)

            for report_party in report_parties:
                percentage_deduction = None
                if report_party['nature'] == 'F':  # [F]. Physical person
                    if (report_party['amount']
                            <= report.donation_amount_threshold):
                        percentage_deduction = report.first_less_physical
                    elif report.pluriannual_applicable(report_party):
                        percentage_deduction = (
                            report.pluriannual_physical)
                    else:
                        percentage_deduction = report.first_greater_physical

                elif report_party['nature'] == 'J':  # [J]. Artificial person
                    if report.pluriannual_applicable(report_party):
                        percentage_deduction = (
                            report.pluriannual_artificial)
                    elif (report_party['amount']
                            <= report.donation_amount_threshold):
                        percentage_deduction = report.first_less_artificial
                    else:
                        percentage_deduction = report.first_greater_artificial
                report_party['percentage_deduction'] = percentage_deduction
                vlist.append(report_party)

        if vlist:
            ReportParty.create(vlist)
            cls.save(reports)

    @classmethod
    def _delete_lines(cls, reports):
        pool = Pool()
        Line = pool.get('aeat.182.report.party')
        Line.delete(Line.search([
                    ('report', 'in', [r.id for r in reports]),
                    ]))

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def process(cls, reports):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, reports):
        pass


class ReportAccount(ModelSQL):
    'AEAT 182 Report Account'
    __name__ = 'aeat.182.report.account'
    report = fields.Many2One('aeat.182.report', 'Report', required=True,
        ondelete='CASCADE')
    account = fields.Many2One('account.account', 'Account', required=True,
        ondelete='CASCADE')


class ReportParty(ModelSQL, ModelView):
    'AEAT 182 Report Party'
    __name__ = 'aeat.182.report.party'
    report = fields.Many2One('aeat.182.report', 'Report', required=True,
        ondelete='CASCADE')
    company = fields.Function(fields.Many2One('company.company', 'Company'),
        'get_report_field', searcher='search_report_field')
    company_vat = fields.Function(fields.Char('Company VAT'),
        'get_report_field', searcher='search_report_field')
    fiscalyear_code = fields.Function(fields.Integer('Fiscal Year'),
        'get_report_field', searcher='search_report_field')
    party_vat = fields.Char('Party VAT')
    representative_nif = fields.Char('Representative VAT')
    party_name = fields.Char('Party Name')
    nature = fields.Selection([
            ('F', '[F]. Physical person'),
            ('J', '[J]. Artificial person'),
            ('E', '[E]. Entity under the income allocation'),
        ], 'Nature')
    party_subdivision_code = fields.Char('Party Subdivision Code')
    key = fields.Selection(KEY, 'Key',
        states={
            'required': True,
            })
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
            'get_currency_digits')
    percentage_deduction = fields.Numeric('% Deduction',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        required=True, depends=['currency_digits'])
    donation_in_kind = fields.Boolean('Donation in kind')
    deduction_autonomous_community = fields.Selection(AUTONOMOUS_COMUNITY,
        'Deduction Autonomous Community')
    percentage_deduction_autonomous_community = fields.Numeric(
        'Percentage Deduction Autonomous Community', digits=(14, 10),
        states={
            'required': Bool(Eval('deduction_autonomous_community')),
            'invisible': Not(Bool(Eval('deduction_autonomous_community'))),
            }, depends=['deduction_autonomous_community'])
    revocation = fields.Boolean('Revocation',
        states={
            'invisible': Not(Eval('key').in_(['A', 'B'])),
            }, depends=['key'])
    exercise_of_the_revoked_donation = fields.Integer(
        'Exercise of the revoked donation',
        states={
            'invisible': Not(Bool(Eval('revocation'))),
            }, depends=['revocation'])
    type_of_good = fields.Selection(TYPE_OF_GOOD, 'Type of good',
        states={
            'invisible': And(Not(Eval('key').in_(['C', 'D'])),
                Not(Bool(Eval('donation_in_kind')))),
            }, depends=['key', 'donation_in_kind'''])
    identification_of_good = fields.Selection(IDENTIFICATION_OF_GOOD,
        'Identification of good',
        states={
            'invisible': Not(Bool(Eval('type_of_good'))),
            }, depends=['type_of_good'])

    def get_rec_name(self, name):
        report = self.report.rec_name + ':' if self.report else ''
        return "%s %s-%s" % (report, self.party_name, self.key)

    @classmethod
    def get_currency_digits(cls, records, name=None):
        res = {r.id: r.report.currency.digits for r in records}
        return res

    @classmethod
    def get_report_field(cls, records, names):
        res = {n: {r.id: getattr(r.report, n) for r in records} for n in names}
        return res

    @classmethod
    def search_report_field(cls, name, clause):
        return [('report.' + name,) + tuple(clause[1:])]
