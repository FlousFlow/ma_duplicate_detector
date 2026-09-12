{
    'name': 'FlousFlow Duplicate Detector',
    'version': '19.0.2.0.2',
    'category': 'Extra Tools',
    'summary': 'Configurable duplicate detection for Odoo records with warnings before duplicate data is saved.',
    'author': 'FlousFlow',
    'website': 'https://flousflow.com',
    'support': 'support@flousflow.com',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'assets': {
        'web.assets_backend': [
            'flousflow_duplicate_detector/static/src/form_notify.js',
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
