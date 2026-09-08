from odoo import api, fields, models


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
        [('warn', 'Warning with link (still requires a decision)'),
         ('block', 'Block Save (hard stop)')],
        string='On Duplicate Found', default='block', required=True,
        help="Warn: interrupts the save with a direct button to open the "
             "existing record.\nBlock: raises a blocking error.",
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
