from odoo import api, fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    can_reconcile = fields.Boolean(string="Can Reconcile")