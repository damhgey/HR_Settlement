# -*- coding: utf-8 -*-
{
    'name': "HR Settlements",

    'summary': """Settlement for Employees """,

    'description': """Settlement for Employees """,

    'author': "Ahmed Elsayed Eldamhogy",

    'category': 'hr',

    'version': '0.1',

    'depends': ['base', 'hr'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/settlement.xml',
        'views/hr_leave_view.xml',
        'data/hr_settlement_sequence.xml',
        'report/settlement_report.xml',
    ],

}