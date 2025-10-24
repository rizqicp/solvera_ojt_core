# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class OjtBatch(models.Model):
    _name = "ojt.batch"
    _description = "OJT Batch"
    _order = "start_date desc, id desc"

    company_id = fields.Many2one("res.company", string="Company", required=True, readonly=True, default=lambda self: self.env.company)
    department_id = fields.Many2one("hr.department",string="Department")
    job_id = fields.Many2one("hr.job", domain=[('department_id', '=', department_id)], string="Job Position", help="Only jobs from the selected department can be selected")
    name = fields.Char(string="Batch Name",required=True, index=True)
    code = fields.Char(string="Batch Code",required=True, index=True, readonly=True, copy=False, default=lambda self: _('New'))
    description = fields.Html(string="Description")
    capacity = fields.Integer(string="Capacity (Target Participants)")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    mode = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    ], string="Mode", default='online')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('recruit', 'Recruitment'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string="Status", default='draft')
    mentor_ids = fields.Many2many('hr.employee', string="Mentors", domain=[('user_id', '!=', False)], help="Internal users assigned as mentors for this batch")
    participant_ids = fields.One2many("ojt.participant", "batch_id", string="Participants")

    # Constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_("The start date cannot be later than the end date."))

    # Onchange / Create / Write
    @api.onchange("department_id")
    def _onchange_department_id(self):
        if self.department_id:
            self.job_id = False
            self.mentor_ids = [(5, 0, 0)]

    @api.onchange("job_id")
    def _onchange_job_id(self):
        if self.job_id:
            self.mentor_ids = [(5, 0, 0)]

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            job = self.env['hr.job'].browse(vals.get('job_id'))
            job_code = job.name[:3].upper() if job else 'JOB'
            year = datetime.now().year
            seq = self.env['ir.sequence'].next_by_code('ojt.batch') or '0000'
            vals['code'] = f"OJTBATCH/{job_code}/{year}/{seq}"
        return super(OjtBatch, self).create(vals)
    
    @api.model
    def write(self, vals):
        for rec in self:
            if rec.state in ('ongoing', 'done') and any(f not in ('state',) for f in vals.keys()):
                raise ValidationError(_("You cannot modify this batch once it is ongoing or done."))
        return super(OjtBatch, self).write(vals)

    def write(self, vals):
        res = super().write(vals)
        # When batch state changes to 'done', issue certificates automatically
        if 'state' in vals and vals['state'] == 'done':
            for batch in self:
                batch._action_issue_certificates_for_participants()
        return res

    def _action_issue_certificates_for_participants(self):
        """Issue certificates automatically when batch is done."""
        Certificate = self.env['ojt.certificate']
        for batch in self:
            for participant in batch.participant_ids:
                existing = Certificate.search([
                    ('participant_id', '=', participant.id),
                    ('batch_id', '=', batch.id)
                ], limit=1)

                if existing:
                    continue  # skip if already has a certificate

                cert = Certificate.create({
                    'participant_id': participant.id,
                    'batch_id': batch.id,
                })
                cert.action_issue_certificate()