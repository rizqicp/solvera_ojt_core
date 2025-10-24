# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import uuid
import base64
from io import BytesIO
import qrcode

class OjtCertificate(models.Model):
    _name = "ojt.certificate"
    _description = "OJT Certificate"
    _rec_name = "display_name"

    display_name = fields.Char(string="Title", compute="_compute_display_name", store=True)
    participant_id = fields.Many2one("ojt.participant", string="Participant", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Partner", related="participant_id.partner_id", store=True)
    batch_id = fields.Many2one("ojt.batch", string="Batch", required=True, ondelete="cascade", index=True)
    issued_date = fields.Datetime(string="Issued Date", default=fields.Datetime.now)
    total_assignments = fields.Integer(string="Total Assignments", compute="_compute_stats", store=True)
    average_score = fields.Float(string="Average Score", digits=(6,2), compute="_compute_stats", store=True)
    qr_token = fields.Char(string="QR Token", readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))
    qr_url = fields.Char(string="Verification URL", compute="_compute_qr_url", store=False)
    pdf_attachment_id = fields.Many2one("ir.attachment", string="PDF Attachment", readonly=True)
    state = fields.Selection([('draft','Draft'),('issued','Issued')], default='draft', string='State')

    _sql_constraints = [
        (
            'unique_participant_batch',
            'unique(participant_id, batch_id)',
            'This participant already has a certificate for this batch.'
        )
    ]

    @api.constrains('participant_id', 'batch_id')
    def _check_duplicate_certificate(self):
        for rec in self:
            if rec.participant_id and rec.batch_id:
                duplicate = self.search([
                    ('participant_id', '=', rec.participant_id.id),
                    ('batch_id', '=', rec.batch_id.id),
                    ('id', '!=', rec.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        f"Certificate already exists for participant {rec.partner_id.name} in batch {rec.batch_id.name}."
                    ))

    @api.constrains('participant_id', 'batch_id')
    def _check_participant_batch_match(self):
        for rec in self:
            if rec.participant_id and rec.batch_id and rec.participant_id.batch_id != rec.batch_id:
                raise ValidationError(_("Participant does not belong to the selected batch."))

    @api.depends('participant_id','batch_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s - %s" % (
                rec.batch_id.name or '',
                rec.partner_id.name or ''
            )

    @api.depends('participant_id','batch_id')
    def _compute_stats(self):
        Submission = self.env['ojt.submission']
        for rec in self:
            rec.total_assignments = 0
            rec.average_score = 0.0
            if rec.participant_id and rec.batch_id:
                subs = Submission.search([
                    ('participant_id','=', rec.participant_id.id),
                    ('assignment_id.batch_id','=', rec.batch_id.id),
                    ('state','=', 'scored'),
                ])
                rec.total_assignments = len(subs)
                if subs:
                    rec.average_score = sum(subs.mapped('score')) / len(subs)

    @api.depends('qr_token')
    def _compute_qr_url(self):
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.qr_url = (base.rstrip('/') + '/ojt/certificate/verify/%s' % rec.qr_token) if rec.qr_token else ''

    def action_generate_pdf_attachment(self):
        self.ensure_one()
        report_obj = self.env["ir.actions.report"]
        report_xml_id = "solvera_ojt_core.action_report_ojt_certificate"

        # Generate the PDF content
        pdf_content, _ = report_obj._render_qweb_pdf(report_xml_id, res_ids=self.ids)

        # Create attachment
        attachment = self.env["ir.attachment"].create({
            # "name": f"Certificate_{self.name}.pdf",
            "name": f"Certificate_{self.partner_id.name}.pdf",
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
        })
        return attachment


    def _generate_qr_png_base64(self):
        """Return png image base64 for the QR (for embedding in report)."""
        self.ensure_one()
        if not self.qr_url:
            return False
        qr = qrcode.QRCode(box_size=6, border=1)
        qr.add_data(self.qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()

    def action_issue_certificate(self):
        """Generate certificate PDF, mark issued, and return download link."""
        self.ensure_one()
        self._compute_stats()
        self._compute_qr_url()

        # Mark as issued
        self.write({'state': 'issued'})

        # Generate and link attachment
        attach = self.action_generate_pdf_attachment()
        self.write({'pdf_attachment_id': attach.id})

        # Return action to download/open PDF
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attach.id}?download=true",
            "target": "self",
        }

