# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class OjtSubmission(models.Model):
    _name = "ojt.submission"
    _description = "OJT Assignment Submission"
    _order = "submitted_on desc"

    assignment_id = fields.Many2one("ojt.assignment", string="Assignment", required=True, ondelete="cascade", index=True)
    participant_id = fields.Many2one("ojt.participant", string="Participant", required=True, ondelete="cascade", index=True)
    submitted_on = fields.Datetime(string="Submitted On", default=fields.Datetime.now)
    attachment_ids = fields.Many2many("ir.attachment", "ojt_assignment_submit_attachment_rel", "submit_id", "attachment_id", string="Attachments", help="Files uploaded as part of this assignment submission.")
    url_link = fields.Char(string="External Link", help="Optional URL for project or online submission (GitHub, Figma, Google Drive, etc.)")
    score = fields.Float(string="Score", help="Score given by mentor/reviewer.")
    reviewer_id = fields.Many2one("res.users", string="Reviewer", help="The user or mentor who evaluated this submission.")
    feedback = fields.Html( string="Feedback / Comments", help="Mentor feedback for this submission.")
    late = fields.Boolean(string="Late Submission", compute="_compute_late", store=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("scored", "Scored"),
    ], string="Status", default="submitted")

    _sql_constraints = [
        (
            "unique_submit_per_participant_assignment",
            "unique(assignment_id, participant_id)",
            "Each participant can only have one submission per assignment!",
        ),
    ]

    @api.depends("submitted_on", "assignment_id.deadline")
    def _compute_late(self):
        for rec in self:
            if rec.submitted_on and rec.assignment_id.deadline:
                rec.late = rec.submitted_on > rec.assignment_id.deadline
            else:
                rec.late = False

    @api.constrains("score")
    def _check_score_limit(self):
        for rec in self:
            if rec.score and rec.assignment_id and rec.score > rec.assignment_id.max_score:
                raise ValidationError(
                    _("Score cannot exceed the assignment maximum score (%s).")
                    % rec.assignment_id.max_score
                )

    def action_submit(self):
        """Mark as submitted."""
        for rec in self:
            rec.state = "submitted"
            if not rec.submitted_on:
                rec.submitted_on = fields.Datetime.now()

    def action_score(self, score=None, feedback=None):
        """Mark as scored and optionally assign a score and feedback."""
        for rec in self:
            if score is not None:
                rec.score = score
            if feedback:
                rec.feedback = feedback
            rec.reviewer_id = self.env.user
            rec.state = "scored"

    @api.model
    def create(self, vals):
        """Auto-set default state and submission time if missing."""
        if not vals.get("submitted_on"):
            vals["submitted_on"] = fields.Datetime.now()
        if not vals.get("state"):
            vals["state"] = "submitted"
        return super().create(vals)
