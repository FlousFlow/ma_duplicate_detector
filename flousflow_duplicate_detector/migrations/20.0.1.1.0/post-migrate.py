from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Disable the required-field rules seeded by older module releases."""
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in (
        'flousflow_duplicate_detector.required_rule_res_partner',
        'flousflow_duplicate_detector.required_rule_product_template',
    ):
        rule = env.ref(xmlid, raise_if_not_found=False)
        if rule and rule._name == 'ma.required.field.rule' and rule.active:
            rule.write({'active': False})
