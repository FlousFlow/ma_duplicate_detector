{
    'name': 'Duplicate Record Detector | Prevent Duplicate Records in Odoo | Duplicate Warning on Save | Configurable Duplicate Check',
    'version': '19.0.2.0.0',
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
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/ma_required_rule_data.xml',
        'views/ma_duplicate_rule_views.xml',
        'views/ma_duplicate_menu.xml',
    ],
    'price': 0.00,
    'currency': 'USD',
    'installable': True,
    'application': False,
    'auto_install': False,
}
