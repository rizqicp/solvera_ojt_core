# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request

class OjtCertificateController(http.Controller):

    @http.route(['/ojt/certificate/verify/<string:token>'], type='http', auth='public', website=True)
    def certificate_verify(self, token, **kw):
        cert = request.env['ojt.certificate'].sudo().search([('qr_token','=', token)], limit=1)
        if not cert:
            return request.render('solvera_ojt_core.certificate_verify_invalid', {})
        # show a simple page with details and a link to download pdf if available
        return request.render('solvera_ojt_core.certificate_verify', {
            'certificate': cert
        })

    @http.route(['/ojt/certificate/download/<int:certificate_id>'], type='http', auth='user', website=True)
    def portal_download_certificate(self, certificate_id, **kwargs):
        """Allow participant or mentor to download their issued certificate."""
        certificate = request.env['ojt.certificate'].sudo().browse(certificate_id)
        if not certificate.exists():
            return request.not_found()

        # Only allow access to the participant or authorized mentor/admin
        user = request.env.user
        if not (user.has_group('solvera_ojt_core.group_ojt_mentor') or
                user.has_group('base.group_system') or
                certificate.partner_id.id == user.partner_id.id):
            return request.redirect('/my')  # deny access

        # Must have issued state and pdf
        if certificate.state != 'issued' or not certificate.pdf_attachment_id:
            return request.redirect('/my')  # not available yet

        # Return PDF as download
        pdf = certificate.pdf_attachment_id
        pdf_data = base64.b64decode(pdf.datas)
        filename = pdf.name or "certificate.pdf"

        return request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
