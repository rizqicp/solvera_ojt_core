from odoo import models, api
from odoo.exceptions import UserError

class RecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    # Prevent deletion of the 'On The Job Training' stage
    @api.ondelete(at_uninstall=False)
    def _prevent_delete_ojt_stage(self):
        protected_xmlid = 'solvera_ojt_core.stage_on_the_job_training'
        for record in self:
            if record.get_external_id().get(record.id) == protected_xmlid:
                raise UserError("You cannot delete the 'On The Job Training' stage while the OJT module is installed.")
