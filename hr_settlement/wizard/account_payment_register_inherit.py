from odoo import api, fields, models
from lxml import etree


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        if self._context.get('settlement'):
            settlement_id = self._context.get('settlement_id')
            settlement = self.env['hr.settlement'].browse(settlement_id)
            if settlement:
                settlement.write({'state': 'paid', 'payment_id': res['res_id']})

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountPaymentRegister, self)._fields_view_get(view_id=view_id, view_type=view_type,                                                      toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            if self._context.get('settlement'):
                for node in doc.xpath("//field[@name='amount']"):
                    node.set('readonly', '1')
                for node in doc.xpath("//field[@name='communication']"):
                    node.set('readonly', '1')
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result
