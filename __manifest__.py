{
    'name': 'Duplicate Record Detector | Prevent Duplicate Records in Odoo | Duplicate Warning on Save | Configurable Duplicate Check',
    'version': '19.0.1.0.5',
    'category': 'Extra Tools',
    'summary': 'Warn users when saving an Odoo record that matches an existing one on your configured fields, so duplicates are caught before they enter the database.',
    'author': 'CODEerts',
    'website': 'https://www.codeerts.com',
    'support': 'support@codeerts.com',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'assets': {
        'web.assets_backend': [
            'ma_duplicate_detector/static/src/form_notify.js',
        ],
    },
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/ma_duplicate_rule_views.xml',
        'views/ma_duplicate_menu.xml',
    ],
    'price': 0.00,
    'currency': 'USD',
    'installable': True,
    'application': False,
    'auto_install': False,
}
