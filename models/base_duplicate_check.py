import re

from lxml import etree
from odoo import api, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools.sql import table_exists
from odoo import _

PHONE_FIELDS = {'phone', 'mobile', 'whatsapp', 'whatsapp_number'}


class Base(models.AbstractModel):
    _inherit = 'base'

    def _ma_rule_available(self):
        return (
            'ma.duplicate.rule' in self.env
            and table_exists(self.env.cr, 'ma_duplicate_rule')
        )

    def _ma_required_rule_available(self):
        return (
            'ma.required.field.rule' in self.env
            and table_exists(self.env.cr, 'ma_required_field_rule')
        )

    def _ma_skip_check(self):
        """True when the check is bypassed: explicit duplicate_skip key,
        or a CSV/XLSX import (context import_file) unless the active rule
        is configured to enforce during imports."""
        if self.env.context.get('duplicate_skip'):
            return True
        if not self.env.context.get('import_file'):
            return False
        rule = self._ma_get_duplicate_rule()
        return bool(rule) and not rule.enforce_on_import

    # ------------------------------------------------------------------
    # Required field rules (data completeness)
    # ------------------------------------------------------------------
    def _ma_get_required_rule(self):
        return self.env['ma.required.field.rule'].sudo().search(
            [('model_name', '=', self._name), ('active', '=', True)],
            limit=1,
        )

    def get_view(self, view_id=None, view_type='form', **options):
        """Mark required-rule fields with required="1" in form views so they
        render with the standard red asterisk and the web client validates
        them like native required fields. The Base create/write checks stay
        as the server-side authority."""
        result = super().get_view(view_id, view_type, **options)
        if view_type == 'form' and self._ma_required_rule_available() \
                and not self._ma_required_skip():
            rule = self._ma_get_required_rule()
            if rule and rule.field_ids:
                names = set(rule.field_ids.mapped('name'))
                try:
                    root = etree.fromstring(result['arch'])
                    changed = False
                    for node in root.iter('field'):
                        if node.get('name') in names \
                                and not node.get('required') \
                                and not node.get('readonly'):
                            node.set('required', '1')
                            changed = True
                    if changed:
                        result['arch'] = etree.tostring(
                            root, encoding='unicode')
                except etree.XMLSyntaxError:
                    pass
        return result

    def _ma_required_skip(self):
        """Bypass cases: explicit context key, system (sudo) writes done by
        server automation (crons, website flows), or a member of the rule's
        exempt group. Imports follow the rule's enforce_on_import flag."""
        if self.env.context.get('duplicate_skip'):
            return True
        if self.env.su and not self.env.context.get('import_file'):
            return True
        rule = self._ma_get_required_rule()
        if not rule:
            return True
        if self.env.context.get('import_file') and not rule.enforce_on_import:
            return True
        if rule.exempt_group_id and \
                rule.exempt_group_id in self.env.user.group_ids:
            return True
        return False

    def _ma_check_required_vals(self, rule, vals):
        missing = []
        for field in rule.field_ids:
            if field.name not in vals:
                continue
            value = vals[field.name]
            if value in (False, None, '', 0):
                missing.append(field.field_description)
        if missing:
            raise UserError(_(
                "%(title)s\n\n"
                "%(intro)s %(fields)s.\n\n"
                "%(hint)s",
                title=_("Required data is missing"),
                intro=_("This record cannot be saved without:"),
                fields=', '.join(missing),
                hint=_("Please fill in the highlighted fields, or capture the "
                       "customer's location to fill the address "
                       "automatically."),
            ))

    def _ma_check_required_merged(self, rule, vals=None):
        """Check the state the record WILL have after this write: merge the
        incoming vals over the current values and reject if a required field
        ends up empty."""
        missing = []
        for field in rule.field_ids:
            if vals and field.name in vals:
                v = vals[field.name]
            else:
                v = self[field.name]
                v = v.id if hasattr(v, 'id') else v
            if v in (False, None, '', 0):
                missing.append(field.field_description)
        if missing:
            raise UserError(_(
                "%(title)s\n\n%(record)s is missing: %(fields)s.\n\n"
                "%(hint)s",
                title=_("Required data is missing"),
                record=self.display_name,
                fields=', '.join(missing),
                hint=_("Please fill in the highlighted fields, or capture the "
                       "customer's location to fill the address "
                       "automatically."),
            ))


    @api.model_create_multi
    def create(self, vals_list):
        if self._ma_rule_available() and not self._ma_skip_check():
            rule = self._ma_get_duplicate_rule()
            if rule and rule.field_ids and rule.action != 'notify':
                for vals in vals_list:
                    self._ma_check_duplicate_vals(rule, vals, exclude_id=None)
        records = super().create(vals_list)
        # Validate the FINAL state of the new records: a field absent from
        # vals still ends up empty when it has no default. Raising here rolls
        # the whole create back, so nothing partial is persisted.
        if self._ma_required_rule_available() and not self._ma_required_skip():
            req_rule = self._ma_get_required_rule()
            if req_rule and req_rule.field_ids:
                for record, vals in zip(records, vals_list):
                    record._ma_check_required_merged(req_rule, vals)
        return records

    def write(self, vals):
        if (
            not self._ma_skip_check()
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
        if (
            not self._ma_required_skip()
            and len(self) == 1
            and self._ma_required_rule_available()
        ):
            req_rule = self._ma_get_required_rule()
            if req_rule and req_rule.field_ids:
                rule_field_names = req_rule.field_ids.mapped('name')
                if any(fname in vals for fname in rule_field_names):
                    self._ma_check_required_merged(req_rule, vals)
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

    @api.model
    def _ma_field_leafs(self, field, value):
        """Domain leaves matching a field value, phone-number aware.

        Phone fields match the exact value OR any stored variant sharing the
        last 8 digits (covers +20/0020 prefixes, spaces, dashes), e.g.
        '01009560007' matches '+20 100 956 0007'.
        """
        leafs = [(field.name, '=', value)]
        if field.name in PHONE_FIELDS and isinstance(value, str):
            digits = re.sub(r'\D', '', value)
            tail = digits[-8:]
            if len(digits) >= 8 and tail != value:
                leafs.append((field.name, 'ilike', tail))
        return leafs

    def _ma_find_duplicate(self, rule, vals, exclude_id):
        domain = None
        for field in rule.field_ids:
            value = vals.get(field.name)
            if value in (False, None, '', 0):
                return None  # skip check if any field is empty/unset

            leafs = self._ma_field_leafs(field, value)
            group = leafs[0] if len(leafs) == 1 else ['|'] + leafs
            domain = group if domain is None else ['&', domain, group]

        if domain is None:
            return None

        if exclude_id:
            domain = ['&', domain, ('id', '!=', exclude_id)]

        return self.env[self._name].sudo().search(domain, limit=1)

    def _ma_check_duplicate_vals(self, rule, vals, exclude_id):
        duplicate = self._ma_find_duplicate(rule, vals, exclude_id)
        if not duplicate:
            return

        field_labels = ', '.join(f.field_description for f in rule.field_ids)
        # Error dialogs escape HTML, so keep the message plain text; the
        # RedirectWarning button below is the clickable path to the record.
        message = _(
            "%(title)s\n\n%(intro)s:\n\"%(name)s\"",
            title=_("Duplicate Detected"),
            intro=_("A record with the same %(fields)s already exists",
                    fields=field_labels),
            name=duplicate.display_name,
        )

        if rule.action == 'warn':
            open_action = {
                'type': 'ir.actions.act_window',
                'name': duplicate.display_name,
                'res_model': self._name,
                'res_id': duplicate.id,
                'view_mode': 'form',
                'views': [[False, 'form']],
                'target': 'current',
            }
            raise RedirectWarning(
                message, open_action,
                _("Open \"%s\"", duplicate.display_name),
            )

        raise UserError(message)
