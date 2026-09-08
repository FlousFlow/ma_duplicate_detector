from odoo import api, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools.sql import table_exists
from odoo import _


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
            if rule and rule.field_ids and rule.action != 'notify':
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
            if rule and rule.field_ids and rule.action != 'notify':
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

    @api.model
    def ma_check_duplicate(self, vals):
        """Called from the web client before saving (notify mode).

        Returns {'id': int, 'name': str} if a rule matches the given values,
        False otherwise. Never raises.
        """
        if self.env.context.get('duplicate_skip') or not self._ma_rule_available():
            return False
        rule = self._ma_get_duplicate_rule()
        if not rule or not rule.field_ids:
            return False
        merged = {}
        for field in rule.field_ids:
            if field.name in vals:
                merged[field.name] = vals[field.name]
            elif self.id:
                v = self[field.name]
                merged[field.name] = v.id if hasattr(v, 'id') else v
        duplicate = self._ma_find_duplicate(rule, merged, exclude_id=self.id or None)
        if duplicate:
            return {'id': duplicate.id, 'name': duplicate.display_name}
        return False

    def _ma_find_duplicate(self, rule, vals, exclude_id):
        domain = []
        for field in rule.field_ids:
            value = vals.get(field.name)
            if value in (False, None, '', 0):
                return None  # skip check if any field is empty/unset

            domain.append((field.name, '=', value))

        if not domain:
            return None

        if exclude_id:
            domain.append(('id', '!=', exclude_id))

        return self.env[self._name].sudo().search(domain, limit=1)

    def _ma_check_duplicate_vals(self, rule, vals, exclude_id):
        duplicate = self._ma_find_duplicate(rule, vals, exclude_id)
        if not duplicate:
            return

        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', ''
        )
        url = f"{base_url}/web#id={duplicate.id}&model={self._name}&view_type=form"
        field_labels = ', '.join(f.field_description for f in rule.field_ids)
        message = _(
            "Duplicate Detected\n\n"
            "A record with the same %(fields)s already exists:\n"
            "\"%(name)s\"\n\n"
            "Open it here:\n%(url)s",
            fields=field_labels,
            name=duplicate.display_name,
            url=url,
        )

        if rule.action == 'warn':
            open_action = {
                'type': 'ir.actions.act_window',
                'name': duplicate.display_name,
                'res_model': self._name,
                'res_id': duplicate.id,
                'view_mode': 'form',
                'target': 'current',
            }
            raise RedirectWarning(
                message, open_action, _("Open Duplicate"),
            )

        raise UserError(message)
