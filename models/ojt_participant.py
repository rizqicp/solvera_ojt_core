# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class OjtParticipant(models.Model):
    _name = "ojt.participant"
    _description = "OJT Participant"
    _order = "batch_id, partner_id"
    _rec_name = "partner_id"

    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    batch_id = fields.Many2one("ojt.batch", string="OJT Batch", required=True, ondelete="cascade", index=True)
    user_id = fields.Many2one("res.users", string="Participant User")
    partner_id = fields.Many2one('res.partner', string="Participant", store=True)
    applicant_id = fields.Many2one("hr.applicant", string="Recruitment Applicant")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('left', 'Left'),
    ], string="Status", default="active")

    _sql_constraints = [(
        "unique_participant_batch",
        "unique(batch_id, partner_id)",
        "Participant already exists in this batch!",
    )]