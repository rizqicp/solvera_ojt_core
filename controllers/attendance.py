# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request


class OjtAttendanceController(http.Controller):

    @http.route("/ojt/attendance/checkin/<string:token>", type="http", auth="user", website=True)
    def ojt_attendance_checkin(self, token, **kwargs):
        """QR Code check-in endpoint."""
        user = request.env.user
        participant = request.env["ojt.participant"].sudo().search([("user_id", "=", user.id)], limit=1)
        if not participant:
            return request.render("solvera_ojt_core.portal_batch_dashboard", {
                "error_title": "Access Denied",
                "error_message": "You are not registered as an OJT participant."
            })

        event = request.env["event.event"].sudo().search([("qr_token", "=", token)], limit=1)
        if not event:
            return request.render("solvera_ojt_core.portal_batch_dashboard", {
                "error_title": "Invalid QR Code",
                "error_message": "This QR code does not match any valid OJT session."
            })

        Attendance = request.env["ojt.attendance"].sudo()
        now = fields.Datetime.now()

        attendance = Attendance.search([
            ("participant_id", "=", participant.id),
            ("event_id", "=", event.id)
        ], limit=1)

        if not attendance:
            # create new attendance record
            Attendance.create({
                "participant_id": participant.id,
                "event_id": event.id,
                "batch_id": event.batch_id.id,
                "check_in": now,
                "method": "qr",
                "presence": "present",
            })
        else:
            # update existing attendance with check-out
            attendance.write({
                "check_out": now,
                "method": "qr",
            })

        # Redirect to batch dashboard
        batch_id = event.batch_id.id if event.batch_id else 0
        return request.redirect(f"/ojt/batch/{batch_id}")
    
    @http.route(['/ojt/event/<int:event_id>'], type='http', auth='user', website=True)
    def portal_event_detail(self, event_id, **kw):
        event = request.env['event.event'].sudo().browse(event_id)
        if not event.exists():
            return request.not_found()
        return request.render('solvera_ojt_core.portal_event_detail', {'event': event})

    @http.route(['/ojt/event/join/<int:event_id>'], type='http', auth='user', website=True)
    def portal_event_join(self, event_id, **kw):
        """Online check-in: create attendance record with method='online' then redirect to meeting_url"""
        user = request.env.user
        participant = request.env['ojt.participant'].sudo().search([('user_id', '=', user.id)], limit=1)
        event = request.env['event.event'].sudo().browse(event_id)

        if not participant or not event.exists() or not event.meeting_url:
            return request.redirect('/ojt')  # fallback

        Attendance = request.env['ojt.attendance'].sudo()
        now = fields.Datetime.now()

        attendance = Attendance.search([
            ('participant_id', '=', participant.id),
            ('event_id', '=', event.id)
        ], limit=1)

        if not attendance:
            Attendance.create({
                'participant_id': participant.id,
                'event_id': event.id,
                'batch_id': event.batch_id.id,
                'check_in': now,
                'method': 'online',
                'presence': 'present',
            })
        else:
            attendance.write({
                'check_out': now,
                'method': 'online',
            })
        
        return request.redirect(event.meeting_url, local=False)
