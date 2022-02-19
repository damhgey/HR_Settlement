from odoo import api, fields, models, _
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
                'timeoff_request': [('employee_id', '=', rec.employee_id.id), ('is_reconcile', '=', False),
                                    ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120'),
                                    ('state', '=', 'validate')]}}

    settlement_code = fields.Char(string="Settlement No", readonly=True, default='Settlement')
    application_date = fields.Date('Application Date', required=True, default=fields.Date.today(), readonly=True,
                                   states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'submitted'),
                              ('hr_approve', 'HR Approve'),
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
                                       ('both', 'Both')], readonly=True,
                                      states={'draft': [('readonly', False)]},
                                      string="Settlement For", required=True)
    timeoff_request = fields.Many2one(comodel_name="hr.leave", string="Time Off Request",
                                      domain=get_time_off_requests_domain, readonly=True,
                                      states={'draft': [('readonly', False)]}, )
    timeoff_request_days = fields.Float(comodel_name="hr.leave", string="Time Off Request Days",
                                        related='timeoff_request.number_of_days')
    timeoff_balance = fields.Float(string="Time Off Balance", compute='_compute_timeoff_balance')
    days_to_reconcile = fields.Float(string="Days To Reconcile", required=False, readonly=True,
                                     states={'draft': [('readonly', False)]})
    remaining_days = fields.Float(string="Remaining Days", compute='_compute_remaining_days')
    show_timeoff_request = fields.Boolean(string="", )
    show_timeoff_balance = fields.Boolean(string="", )
    show_both = fields.Boolean(string="", )

    # settlement computation
    settlement_days = fields.Float(string="Settlement Days", compute='_compute_settlement_days')
    leave_amount = fields.Float(string="Leave Amount", compute='_compute_leave_amount')
    ticket_amount = fields.Float(string="Ticket Amount", compute='_compute_ticket_amount')
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount')

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

    def button_create_journal(self):
        self.state = 'issued'

    def button_register_payment(self):
        self.state = 'paid'

    def reset_to_draft(self):
        self.state = 'draft'

    def button_cancel(self):
        self.state = 'cancel'

    # onchange settlement information fields visibility
    @api.onchange('settlement_for')
    def onchange_settlement_for(self):
        if self.settlement_for == 'timeoff_request':
            self.show_timeoff_balance = False
            self.show_both = False
            self.show_timeoff_request = True
        if self.settlement_for == 'timeoff_balance':
            self.show_timeoff_request = False
            self.show_both = False
            self.show_timeoff_balance = True
        if self.settlement_for == 'both':
            self.show_both = True

    @api.depends('employee_id', 'settlement_for')
    def _compute_timeoff_balance(self):
        leave_report = self.env['hr.leave.report']
        for rec in self:
            paid_timeoff_days = leave_report.search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120'),
                 ('state', '=', 'validate')]).mapped('number_of_days')
            timeoff_balance = sum(paid_timeoff_days)
            if paid_timeoff_days:
                rec.timeoff_balance = timeoff_balance
            else:
                rec.timeoff_balance = 0

    @api.depends('timeoff_balance', 'days_to_reconcile')
    def _compute_remaining_days(self):
        for rec in self:
            rec.remaining_days = rec.timeoff_balance - rec.days_to_reconcile

    @api.onchange('timeoff_balance', 'days_to_reconcile')
    def check_days_to_reconcile(self):
        if self.days_to_reconcile > self.timeoff_balance:
            raise UserError(_('You cannot reconcile days more than your balance days.'))

    @api.depends('settlement_for', 'timeoff_request_days', 'days_to_reconcile')
    def _compute_settlement_days(self):
        for rec in self:
            if rec.settlement_for == 'timeoff_request':
                rec.settlement_days = rec.timeoff_request_days
            elif rec.settlement_for == 'timeoff_balance':
                rec.settlement_days = rec.days_to_reconcile
            elif rec.settlement_for == 'both':
                rec.settlement_days = rec.timeoff_request_days + rec.days_to_reconcile
            else:
                rec.settlement_days = 0.0

    def _compute_leave_amount(self):
        for rec in self:
            if rec.contract_id:
                total_salary = rec.contract_id.total_salary
                settlement_days = rec.settlement_days
                leave_amount = total_salary / 30 * settlement_days
                rec.leave_amount = leave_amount
            else:
                rec.leave_amount = 0.0

    def _compute_ticket_amount(self):
        for rec in self:
            if rec.contract_id:
                if rec.settlement_for == 'timeoff_request' or rec.settlement_for == 'both':
                    rec.ticket_amount = rec.contract_id.travel_ticket_amount
                else:
                    rec.ticket_amount = 0.0

    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum([rec.leave_amount, rec.ticket_amount])

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
