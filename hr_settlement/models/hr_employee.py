from odoo import api, fields, models


class NewModule(models.Model):
    _inherit = 'hr.employee'

    settlement_ids = fields.One2many(comodel_name="hr.settlement", inverse_name="employee_id")

    def open_settlement_ids(self):
        return {
            'name': 'Employee Settlements',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.settlement',
            'domain': [('id', 'in', self.settlement_ids.ids)],
            'type': 'ir.actions.act_window',
        }
