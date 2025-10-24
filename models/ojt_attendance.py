# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class OjtAttendance(models.Model):
    _name = "ojt.attendance"
    _description = "OJT Attendance Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "event_id, participant_id"

    participant_id = fields.Many2one("ojt.participant", string="Participant", required=True, index=True, tracking=True)
    batch_id = fields.Many2one("ojt.batch", string="Batch", required=True, ondelete="cascade", index=True, tracking=True)
    event_id = fields.Many2one("event.event", string="Event / Session", required=True, index=True, tracking=True)
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    presence = fields.Selection([
        ("present", "Present"),
        ("late", "Late"),
        ("absent", "Absent"),
    ], string="Presence Status", default="present", tracking=True)
    method = fields.Selection([
        ("qr", "QR Scan"),
        ("online", "Online Join"),
        ("manual", "Manual"),
    ], string="Check-in Method", default="online", tracking=True)
    duration_minutes = fields.Float(string="Duration (Minutes)", compute="_compute_duration", store=True, digits=(6, 2))
    notes = fields.Text(string="Notes")
    date = fields.Datetime(string="Date", compute="_compute_date", store=True)
    is_present = fields.Boolean(string="Present", compute="_compute_is_present", store=True)
    remarks = fields.Text(string="Remarks", related="notes")

    _sql_constraints = [
        (
            "unique_attendance_per_event",
            "unique(participant_id, event_id)",
            "Each participant can only have one attendance record per event!",
        ),
    ]

    @api.depends("check_in")
    def _compute_date(self):
        for rec in self:
            rec.date = rec.check_in or rec.event_id.date_begin
    
    @api.depends("check_in", "check_out")
    def _compute_duration(self):
        """Compute total attended minutes between check-in and check-out."""
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                rec.duration_minutes = delta.total_seconds() / 60.0
            else:
                rec.duration_minutes = 0.0
    
    @api.depends("presence")
    def _compute_is_present(self):
        for rec in self:
            rec.is_present = rec.presence == "present"

    

    @api.constrains("check_in", "check_out")
    def _check_time_order(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out < rec.check_in:
                raise ValidationError(_("Check-out time cannot be before check-in."))
    @api.model
    def create(self, vals):
        """Auto-fill batch_id from event if missing."""
        event_id = vals.get("event_id")
        if event_id and not vals.get("batch_id"):
            event = self.env["event.event"].browse(event_id)
            if event.batch_id:
                vals["batch_id"] = event.batch_id.id
        return super().create(vals)