from odoo import models

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    def write(self, vals):
        res = super().write(vals)

        if 'stage_id' in vals:
            new_stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
            if new_stage.name == 'On The Job Training':
                ojt_group_trainer = self.env.ref('solvera_ojt_core.ojt_group_trainer')
                for applicant in self:
                    partner = applicant.partner_id
                    if not partner:
                        continue

                    # If partner has no user, create one and prepare signup
                    if not partner.user_ids:
                        try:
                            partner.with_context(no_reset_password=True).signup_prepare()
                        except Exception:
                            continue
                        self.env['res.users'].with_context(no_reset_password=True).sudo().create({
                            'name': partner.name,
                            'login': partner.email,
                            'partner_id': partner.id,
                            'groups_id': [(6, 0, [ojt_group_trainer.id])],
                        })
                    else:
                        # Partner already has user → just add group
                        user = partner.user_ids[0]
                        user.groups_id = [(4, ojt_group_trainer.id)]

            # To Do, handle removal from group if stage changes away from OJT
        return res
