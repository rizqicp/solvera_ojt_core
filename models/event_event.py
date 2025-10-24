# -*- coding: utf-8 -*-
from odoo import models, fields, api
import uuid
import base64
from io import BytesIO
import qrcode

class EventEvent(models.Model):
    _inherit = "event.event"

    batch_id = fields.Many2one("ojt.batch", string="OJT Batch", ondelete="cascade", index=True, help="OJT Batch this event belongs to.")
    assignment_id = fields.Many2one("ojt.assignment", string="Linked Assignment", help="Optional assignment related to this event/session.")
    attendance_ids = fields.One2many('ojt.attendance', 'event_id', string="Attendances", readonly=True)
    meeting_url = fields.Char(string="Online Meeting Link", help="URL for online session (Zoom, Google Meet, Microsoft Teams, etc.)")

    qr_token = fields.Char(default=lambda self: str(uuid.uuid4()), readonly=True, copy=False)
    qr_url = fields.Char(compute="_compute_qr_url", store=False)
    qr_image = fields.Binary(string="QR Code", compute="_compute_qr_image", store=False)

    @api.depends("qr_token")
    def _compute_qr_url(self):
        IrConfig = self.env["ir.config_parameter"].sudo()
        base_url = str(IrConfig.get_param("web.base.url") or "").rstrip("/")
        for event in self:
            event.qr_url = f"{base_url}/ojt/attendance/checkin/{event.qr_token}" if event.qr_token else ""

    @api.depends("qr_url")
    def _compute_qr_image(self):
        for event in self:
            if event.qr_url:
                # Generate QR code (use integer 1 instead of qrcode.constants.ERROR_CORRECT_L)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=1,  # ERROR_CORRECT_L
                    box_size=10,
                    border=4,
                )
                qr.add_data(event.qr_url)
                qr.make(fit=True)

                # Convert QR to image in memory
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, "PNG")  # Pyright-safe
                event.qr_image = base64.b64encode(buffer.getvalue())
            else:
                event.qr_image = False

    def regenerate_qr_token(self):
        for event in self:
            event.qr_token = str(uuid.uuid4())
            event._compute_qr_url()
            event._compute_qr_image()