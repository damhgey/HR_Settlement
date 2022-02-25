from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    is_reconcile = fields.Boolean(string="Is Reconciled")
    settlement_id = fields.Many2one(comodel_name="hr.settlement", string="Settlement", readonly=True)

    def reconcile_timeoff(self):
        self.ensure_one()

        settlement_data = {
            'employee_id': self.employee_id.id,
            'application_date': fields.Date.today(),
            'settlement_for': 'timeoff_request',
            'timeoff_request': self.id,
            'show_timeoff_request': True,
        }
        settlement = self.env['hr.settlement'].create(settlement_data)
        self.write({'settlement_id': settlement.id})
