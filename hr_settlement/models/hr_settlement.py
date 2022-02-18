from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrSettlement(models.Model):
    _name = 'hr.settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'settlement_code'

    # domain for employee_id field based on user group and contract running
    def get_employee_id_domain(self):
        if self.user_has_groups('hr_settlement.settlement_manager_group'):
            employees = self.env['hr.employee'].search(
                [('contract_id', '!=', False), ('contract_id.state', '=', 'open')]).ids
            return [('id', 'in', employees)]
        else:
            return [('id', 'in', self.env.user.employee_ids.ids), ('contract_id', '!=', False),
                    ('contract_id.state', '=', 'open')]

    # domain for time off based on employee
    @api.onchange('employee_id')
    def get_time_off_requests_domain(self):
        for rec in self:
            rec.timeoff_request = False
            return {'domain': {
                'timeoff_request': [('employee_id', '=', rec.employee_id.id), ('is_reconcile', '=', False)]}}

    settlement_code = fields.Char(string="Settlement No", readonly=True, default='Settlement')
    application_date = fields.Date('Application Date', required=True, default=fields.Date.today(), readonly=True,
                                   states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'submitted'),
                              ('hr_approve', 'HR Approve'),
                              ('finance_approve', 'Finance Approve'),
                              ('issued', 'Issued'),
                              ('paid', 'Paid'),
                              ('cancel', 'Cancelled')],
                             string="Status", readonly=True, default='draft', track_visibility='onchange', select=True)

    # Employee information
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True, readonly=True,
                                  domain=get_employee_id_domain, track_visibility='onchange',
                                  states={'draft': [('readonly', False)]})
    employee_code = fields.Char(string='Employee Code', related='employee_id.barcode')
    contract_id = fields.Many2one('hr.contract', 'Contract', related='employee_id.contract_id',
                                  track_visibility='onchange', required=True)
    company_id = fields.Many2one('res.company', 'Company', track_visibility='onchange',
                                 related='employee_id.company_id')
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id',
                                    track_visibility='onchange')
    job_id = fields.Many2one('hr.job', 'Job Position', related='employee_id.job_id', track_visibility='onchange')

    # settlements information
    settlement_for = fields.Selection([('timeoff_request', 'Time Off Request'),
                                       ('timeoff_balance', 'Time Off Balance'),
                                       ('both', 'Both'), ],
                                      string="Settlement For")
    timeoff_request = fields.Many2one(comodel_name="hr.leave", string="Time Off Request",
                                      domain=get_time_off_requests_domain)
    timeoff_request_days = fields.Float(comodel_name="hr.leave", string="Time Off Request Days",
                                        related='timeoff_request.number_of_days')
    timeoff_balance = fields.Float(string="Time Off Balance", required=False)
    days_to_reconcile = fields.Float(string="Days To Reconcile", required=False, )
    reconcile_date = fields.Date(string="Reconcile Date", required=True, default=fields.Date.today())

    # settlement computation
    settlement_days = fields.Float(string="Settlement Days", readonly=True, )
    leave_amount = fields.Float(string="Leave Amount", readonly=True, )
    ticket_amount = fields.Float(string="Ticket Amount", readonly=True, )
    total_amount = fields.Float(string="Ticket Amount", readonly=True, )

    # approved data
    approved_by = fields.Many2one(comodel_name="res.users", string="Approved By", required=False)
    approved_date = fields.Date(string="Approved Date", required=False, )
    note = fields.Text(string="Note", required=False)

    journal_entry_id = fields.Many2one('account.move', string='Journal Entry')
    payment_id = fields.Many2one('account.payment', string='Payment')

    @api.model
    def create(self, vals):
        settlement_code = self.env['ir.sequence'].get('hr.settlement.code')
        vals['settlement_code'] = settlement_code
        return super(HrSettlement, self).create(vals)

    def button_submit(self):
        self.state = 'submit'

    def button_hr_approve(self):
        self.state = 'hr_approve'

    def button_finance_approve(self):
        self.state = 'finance_approve'

    def button_cancel(self):
        self.state = 'cancel'

    def open_settlement_journal_entry(self):
        return {
            'name': 'Settlement Journal Entry',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', '=', self.journal_entry_id.id)],
            'type': 'ir.actions.act_window',
        }

    def open_settlement_payment(self):
        return {
            'name': 'Settlement Payment',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('id', '=', self.payment_id.id)],
            'type': 'ir.actions.act_window',
        }
