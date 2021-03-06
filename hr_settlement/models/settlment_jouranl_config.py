from odoo import api, fields, models


class SettlementJournalConfig(models.Model):
    _name = 'settlement.journal.config'
    _rec_name = 'name'
    _description = 'Configuration for settlement journal entry'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True, )
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", required=True, )
    leave_debit_account_id = fields.Many2one(comodel_name="account.account", string="Leave Debit Account",
                                             required=True, )
    ticket_debit_account_it = fields.Many2one(comodel_name="account.account", string="Ticket Debit Account",
                                              required=True, )
    total_credit_account_id = fields.Many2one(comodel_name="account.account", string="Total Credit Account",
                                              required=True,)