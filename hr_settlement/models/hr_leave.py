from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    is_reconcile = fields.Boolean(string="Is Reconciled")
