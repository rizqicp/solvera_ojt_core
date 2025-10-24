# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OjtAssignment(models.Model):
    _name = "ojt.assignment"
    _description = "OJT Assignment"
    _order = "batch_id, deadline desc"

    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    batch_id = fields.Many2one("ojt.batch", string="Batch", required=True, ondelete="cascade")
    name = fields.Char(string="Assignment Title", required=True, index=True)
    assignment_type = fields.Selection([
        ("task", "Task / Project"),
        ("quiz", "Quiz (Survey/Slides)"),
        ("presentation", "Presentation"),
    ], string="Assignment_Type", default="task", required=True)
    attachment_required = fields.Boolean(string="Attachment Required", default=True)
    deadline = fields.Datetime(string="Deadline")
    state = fields.Selection([
        ("draft", "Draft"),
        ("open", "Open"),
        ("closed", "Closed"),
    ], string="Status", default="open")
    description = fields.Html(string="Description")
    max_score = fields.Float(string="Maximum Score", default=100.0)
    submit_ids = fields.One2many("ojt.submission", "assignment_id", string="Submissions")
    submission_count = fields.Integer(string="Submission Count", compute="_compute_submission_stats", store=True)

    @api.depends("submit_ids.score")
    def _compute_submission_stats(self):
        for rec in self:
            total = len(rec.submit_ids)
            rec.submission_count = total

    @api.constrains("deadline", "batch_id")
    def _check_deadline(self):
        for rec in self:
            if rec.deadline and rec.batch_id.end_date and rec.deadline.date() > rec.batch_id.end_date:
                raise ValidationError(_("Deadline cannot exceed batch end date."))
