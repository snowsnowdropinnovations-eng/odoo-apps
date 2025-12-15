{
    'name': "Project Task Notification",
    'version': "19.0.1.0",
    'summary': "Project Task Notification | Odoo Task Alerts | Real-Time Team Notifications",
    'description': """
Project Task Notification | Odoo Task Alerts | Real-Time Project Communication

Project Task Notification is a lightweight and efficient Odoo module that sends
instant notifications to all project team members whenever a new task is created.

This module ensures that users linked to a project receive real-time alerts via
Odoo Discuss and on-screen notifications, improving collaboration and task visibility.

Key Features:
• Automatic notification on project task creation
• Real-time alerts for all project team members
• Integrated with Odoo Discuss
• On-screen notification popup support
• Supports multi-user project teams
• No additional configuration required
• Fully compatible with Odoo

Business Benefits:
• Faster awareness of new tasks
• Improved communication across teams
• Better accountability and transparency
• Reduced response delays

Keywords:
project task notification, odoo task alert, odoo project notification,
odoo discuss notification, odoo popup notification, odoo project module,
real time task notification, project team notification
""",
    'author': "Snowdrop Innovations",
    'company': "Snowdrop Innovations",
    'maintainer': "Snowdrop Innovations",
    'category': 'Project',
    'depends': ['base', 'project', 'mail'],
    'data': [
        'views/project_project.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'price': 30,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
        'static/description/icon.png'
    ],
}
