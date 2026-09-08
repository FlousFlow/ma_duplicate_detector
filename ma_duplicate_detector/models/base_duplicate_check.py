from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.sql import table_exists


class Base(models.AbstractModel):
    _inherit = 'base'

    def _ma_rule_available(self):
        return (
            'ma.duplicate.rule' in self.env
            and table_exists(self.env.cr, 'ma_duplicate_rule')
        )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('duplicate_skip') and self._ma_rule_available():
            rule = self._ma_get_duplicate_rule()
            if rule and rule.field_ids:
                for vals in vals_list:
                    self._ma_check_duplicate_vals(rule, vals, exclude_id=None)
        return super().create(vals_list)

    def write(self, vals):
        if (
            not self.env.context.get('duplicate_skip')
            and len(self) == 1
            and self._ma_rule_available()
        ):
            rule = self._ma_get_duplicate_rule()
            if rule and rule.field_ids:
                rule_field_names = rule.field_ids.mapped('name')
                if any(fname in vals for fname in rule_field_names):
                    merged = {}
                    for fname in rule_field_names:
                        if fname in vals:
                            merged[fname] = vals[fname]
                        else:
                            v = self[fname]
                            merged[fname] = v.id if hasattr(v, 'id') else v
                    self._ma_check_duplicate_vals(rule, merged, exclude_id=self.id)
        return super().write(vals)

    def _ma_get_duplicate_rule(self):
        return self.env['ma.duplicate.rule'].sudo().search(
            [('model_name', '=', self._name), ('active', '=', True)],
            limit=1,
        )

    def _ma_check_duplicate_vals(self, rule, vals, exclude_id):
        domain = []
        for field in rule.field_ids:
            value = vals.get(field.name)
            if value in (False, None, '', 0):
                return  # skip check if any field is empty/unset

            domain.append((field.name, '=', value))

        if not domain:
            return

        if exclude_id:
            domain.append(('id', '!=', exclude_id))

        duplicate = self.env[self._name].sudo().search(domain, limit=1)
        if not duplicate:
            return

        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', ''
        )
        url = f"{base_url}/web#id={duplicate.id}&model={self._name}&view_type=form"
        field_labels = ', '.join(f.field_description for f in rule.field_ids)

        raise UserError(
            f"Duplicate Detected\n\n"
            f"A record with the same {field_labels} already exists:\n"
            f'"{duplicate.display_name}"\n\n'
            f"Open it here:\n{url}"
        )
