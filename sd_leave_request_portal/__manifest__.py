# -*- coding: utf-8 -*-
{
    'name': 'Portal Leave Request',
    'summary': 'Portal-based Time Off request system allowing employees to create and track leave requests easily.',
    'description': """
This module enables employees to submit, view, and manage their Time Off / Leave Requests directly through the Odoo Portal.

Key Features:
- Submit Time Off / Leave Requests directly from the portal
- View request history, status, and HR approvals
- User-friendly, mobile responsive employee portal interface
- Reduces HR workload and improves employee experience
- Seamlessly integrated with HR, Attendance, and Holidays modules

Ideal for organizations wanting to streamline HR operations and provide employees with a smooth, self-service Time Off management experience.
""",
    'author': "Snowdrop Innovations",
    'website': "",
    'category': 'portal',
    'version': '19.0.1.0',
    'depends': [
        'base',
        'hr_attendance',
        'hr',
        'hr_holidays',
        'website',
        'portal'
    ],
    "data": [
        'views/time_off_form_inherit.xml',
        'views/time_off_controller_view.xml',
        'views/time_off_create_from_controller.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'price': 85,
    'currency': 'USD',
    'images': ['static/description/banner.png'],

    # SEO Keywords for Apps Store Search Optimization
    'keywords': [
        'portal leave request',
        'odoo portal leave',
        'time off portal',
        'employee leave request',
        'hr leave management',
        'portal time off request',
        'leave application portal',
        'self service leave',
        'odoo hr holidays portal',
        'employee portal'
    ],
}
