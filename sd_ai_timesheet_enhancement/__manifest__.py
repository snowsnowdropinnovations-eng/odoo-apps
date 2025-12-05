# -*- coding: utf-8 -*-
{
    'name': 'AI Timesheet Enhancement',
    'summary': 'Add a custom context menu in text input with AI features.',
    'description': """add a custom context menu in text input with AI features.""",
    'author': "Snowdrop Innovations",
    'website': "",
    'category': 'Tools',
    'version': '17.0.1.0',
    'depends': ['web', 'sale_timesheet', 'web_editor'],
    "external_dependencies": {"python": ["requests"]},
    "data" : [
        'security/ir.model.access.csv',
        'views/account_analytic_line.xml',
        'wizard/ai_timesheet_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sd_ai_timesheet_enhancement/static/src/xml/ai_text_enhancer.xml',
            'sd_ai_timesheet_enhancement/static/src/js/input_context.js',
            'sd_ai_timesheet_enhancement/static/src/css/input_context.css',
        ],
    },

    'license': 'OPL-1',
    'installable': True,
    'application': True
    'price': 50,
    'currency': 'USD',
    'images': ['static/description/banner.png'],
}
