# -*- coding: utf-8 -*-
{
    'name': 'Portal Attendance',
    'summary': 'Employee Attendance Management through the Odoo Portal.',
    'description': """
This module allows employees to view and manage their attendance directly from the Odoo Portal.

Key Features:
- View attendance history from the employee portal
- Check-in and check-out from the portal interface
- Mobile-friendly and responsive portal UI
- Seamless integration with HR and Attendance modules
- Improves transparency and reduces HR manual effort

Ideal for organizations that want to empower employees with self-service attendance tracking via the Odoo Portal.
""",
    'author': 'Snowdrop Innovations',
    'website': '',
    'category': 'portal',
    'version': '19.0.1.0',
    'depends': ['base', 'hr_attendance', 'hr', 'hr_holidays', 'website', 'portal'],
    'data': [
        'views/attendance_history_fetcher_controller_view.xml',
        'views/attendance_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sd_attendance_portal/static/src/js/attendance.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'price': 60,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
        'static/description/icon.png'
    ],
    'keywords': [
        'portal attendance',
        'odoo attendance portal',
        'employee attendance portal',
        'check in check out portal',
        'hr attendance portal',
        'self service attendance',
        'odoo hr attendance',
        'employee portal attendance'
    ],
}
