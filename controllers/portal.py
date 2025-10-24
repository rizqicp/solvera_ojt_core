from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import base64


class CustomerPortal(CustomerPortal):

    # OJT Batches and Dashboard
    @http.route(['/ojt', '/ojt/page/<int:page>'], type='http', auth='user', website=True)
    def portal_batches(self, page=1, **kw):
        user = request.env.user
        if not user.has_group('solvera_ojt_core.ojt_group_trainer'):
            return request.redirect('/my')

        batch_env = request.env['ojt.batch'].sudo()
        participant_env = request.env['ojt.participant'].sudo()

        batches = batch_env.search([('state', '=', 'recruit')], order='create_date desc')
        applied_batch_ids = participant_env.search([('user_id', '=', user.id)]).mapped('batch_id.id')
        my_batches = participant_env.search([('partner_id', '=', user.partner_id.id)]).mapped('batch_id')

        return request.render('solvera_ojt_core.portal_batches', {
            'batches': batches,
            'applied_batch_ids': applied_batch_ids,
            'my_batches': my_batches,
            'page_name': 'ojt',
        })

    @http.route(['/ojt/apply/<int:batch_id>'], type='http', auth='user', website=True)
    def apply_to_batch(self, batch_id, **kw):
        user = request.env.user
        batch = request.env['ojt.batch'].sudo().browse(batch_id)
        if not batch.exists():
            return request.not_found()

        participant_env = request.env['ojt.participant'].sudo()
        existing = participant_env.search([('user_id', '=', user.id), ('batch_id', '=', batch_id)], limit=1)
        if not existing:
            participant_env.create({
                'user_id': user.id,
                'partner_id': user.partner_id.id,
                'batch_id': batch_id,
            })
        return request.redirect('/ojt')

    @http.route(['/ojt/batch/<int:batch_id>'], type='http', auth='user', website=True)
    def portal_batch_dashboard(self, batch_id, **kw):
        user = request.env.user
        if not user.has_group('solvera_ojt_core.ojt_group_trainer'):
            return request.redirect('/my')

        batch = request.env['ojt.batch'].sudo().browse(batch_id)
        if not batch.exists():
            return request.not_found()

        partner = user.partner_id
        participant = request.env['ojt.participant'].sudo().search([
            ('batch_id', '=', batch.id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        event_env = request.env['event.event'].sudo()
        attendance_env = request.env['ojt.attendance'].sudo()
        submission_env = request.env['ojt.submission'].sudo()
        assignment_env = request.env['ojt.assignment'].sudo()

        events = event_env.search([('batch_id', '=', batch.id)])
        attendances = attendance_env.search([
            ('participant_id', '=', participant.id),
            ('event_id', 'in', events.ids),
        ])
        total_events = len(events)
        attended = len(attendances.filtered(lambda a: a.is_present))
        attendance_rate = attended / total_events * 100 if total_events else 0

        submissions = submission_env.search([
            ('participant_id', '=', participant.id),
            ('assignment_id.batch_id', '=', batch.id),
            ('state', '=', 'scored'),
        ])
        overall_score = sum(submissions.mapped('score')) / len(submissions) if submissions else 0

        assignments = assignment_env.search([
            ('batch_id', '=', batch.id),
            ('state', '=', 'open')
        ], order='deadline asc')

        now = fields.Datetime.now()
        batch_events = event_env.search([('batch_id', '=', batch.id)], order='date_begin asc')
        ongoing = batch_events.filtered(lambda e: e.date_begin <= now <= (e.date_end or e.date_begin))
        upcoming = batch_events.filtered(lambda e: e.date_begin > now)

        Certificate = request.env['ojt.certificate'].sudo()
        certificate = Certificate.search([
            ('participant_id','=', participant.id),
            ('batch_id','=', batch.id),
            ('state','=','issued')
        ], limit=1)

        return request.render('solvera_ojt_core.portal_batch_dashboard', {
            'batch': batch,
            'participant': participant,
            'assignments': assignments,
            'attendance_rate': attendance_rate,
            'overall_score': overall_score,
            'ongoing_events': ongoing,
            'upcoming_events': upcoming,
            'certificate': certificate,
        })

    # OJT Assignments and Submissions
    @http.route(['/ojt/assignment/<int:assignment_id>'], type='http', auth='user', website=True)
    def portal_assignment_detail(self, assignment_id, **kw):
        assignment = request.env['ojt.assignment'].sudo().browse(assignment_id)
        if not assignment.exists():
            return request.not_found()

        participant = request.env['ojt.participant'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        submission = request.env['ojt.submission'].sudo().search([
            ('assignment_id', '=', assignment.id),
            ('participant_id', '=', participant.id)
        ], limit=1)

        assignment.submit_ids.attachment_ids.generate_access_token()
        return request.render('solvera_ojt_core.portal_assignment_detail', {
            'assignment': assignment,
            'participant': participant,
            'submission': submission,
            'page_name': 'ojt_assignment_detail',
        })

    @http.route(['/ojt/assignment/submit'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_assignment_submit(self, **post):
        participant = request.env['ojt.participant'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        assignment_id = int(post.get('assignment_id') or 0)
        if not participant or not assignment_id:
            return request.not_found()

        attachments = []
        for f in request.httprequest.files.getlist('attachment'):
            attachments.append(request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': base64.b64encode(f.read()).decode(),
                'res_model': 'ojt.submission',
                'type': 'binary',
                'mimetype': f.content_type,
            }).id)

        submission_env = request.env['ojt.submission'].sudo()
        existing = submission_env.search([
            ('assignment_id', '=', assignment_id),
            ('participant_id', '=', participant.id),
        ], limit=1)

        vals = {
            'url_link': post.get('url_link'),
            'attachment_ids': [(6, 0, attachments)],
            'submitted_on': fields.Datetime.now(),
            'state': 'submitted',
        }
        if existing:
            existing.write(vals)
        else:
            vals.update({'assignment_id': assignment_id, 'participant_id': participant.id})
            submission_env.create(vals)

        return request.redirect(f'/ojt/assignment/{assignment_id}')
