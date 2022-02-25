from odoo import api, fields, models


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    _sql_constraints = [
        ('duration_check', "CHECK (1=1)", "The number of days must be greater than 0."),
    ]
