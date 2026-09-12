from odoo import api, fields, models, _


class MaDuplicateRule(models.Model):
    _name = 'ma.duplicate.rule'
    _description = 'Duplicate Detection Rule'
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(
        related='model_id.model',
        store=True,
        string='Technical Name',
        index=True,
    )
    field_ids = fields.Many2many(
        'ir.model.fields',
        string='Fields to Check',
        domain="[('model_id', '=', model_id), ('store', '=', True), "
               "('ttype', 'not in', ['one2many', 'many2many', 'binary'])]",
    )
    action = fields.Selection(
        [('warn', 'Warning dialog (choose to open the existing record)'),
         ('block', 'Block Save (hard stop)'),
         ('notify', 'Notification only — saves anyway')],
        string='On Duplicate Found', default='block', required=True,
        help="Warn: interrupts the save with a button to open the existing "
             "record.\nBlock: raises a blocking error.\nNotify: saves the "
             "record and shows a non-blocking notification with a link.",
    )
    enforce_on_import = fields.Boolean(
        string='Apply During Imports', default=False,
        help="If enabled, records imported from CSV/XLSX that match this "
             "rule are rejected too. If disabled (default), imports bypass "
             "the check.",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_model_id', 'UNIQUE(model_id)',
         'A duplicate detection rule already exists for this model.'),
    ]

    @api.depends('model_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.model_id.name or ''

    @api.model
    def get_notify_models(self):
        """Technical names of models having an active 'notify' rule.

        Called once per web-client session by the form controller patch so
        that saves on models without rules cost zero extra RPC.
        """
        return self.sudo().search(
            [('active', '=', True), ('action', '=', 'notify')]
        ).mapped('model_name')


class MaRequiredFieldRule(models.Model):
    _name = 'ma.required.field.rule'
    _description = 'Required Field Rule (data completeness on save)'
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(
        related='model_id.model',
        store=True,
        string='Technical Name',
        index=True,
    )
    field_ids = fields.Many2many(
        'ir.model.fields',
        string='Required Fields',
        domain="[('model_id', '=', model_id), ('store', '=', True), "
               "('ttype', 'not in', ['one2many', 'many2many', 'binary'])]",
        required=True,
    )
    exempt_group_id = fields.Many2one(
        'res.groups',
        string='Exempt Group',
        help="Members of this group can save records without these fields "
             "(e.g. administrators doing cleanups). Empty = applies to "
             "everyone.",
    )
    enforce_on_import = fields.Boolean(
        string='Apply During Imports', default=False,
        help="If enabled, CSV/XLSX imports are also rejected when a record "
             "is missing a required field. Keep it off while you are still "
             "back-filling historical data.",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_model_id', 'UNIQUE(model_id)',
         'A required-field rule already exists for this model.'),
    ]

    @api.depends('model_id')
    def _compute_name(self):
        for rec in self:
            rec.name = _('%(model)s: required fields', model=rec.model_id.name or '')

    @api.model
    def get_required_field_names(self, model_name):
        """Return active required fields for the web client's pre-save check.

        The method is intentionally sudo-backed: the rule is technical
        configuration, while the resulting validation must apply to normal
        users without granting them access to edit or browse the rule model.
        """
        rule = self.sudo().search(
            [('model_name', '=', model_name), ('active', '=', True)],
            limit=1,
        )
        return rule.field_ids.mapped('name') if rule else []
