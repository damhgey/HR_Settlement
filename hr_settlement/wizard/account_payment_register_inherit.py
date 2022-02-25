from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        if self._context.get('settlement'):
            settlement_id = self._context.get('settlement_id')
            settlement = self.env['hr.settlement'].browse(settlement_id)
            if settlement:
                settlement.write({'state': 'paid', 'payment_id': res['res_id']})
