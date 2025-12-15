from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    team_ids = fields.Many2many('res.users', string='Team',
                                context={'active_test': False},
                                tracking=True,
                                domain="[('active', '=', True)]")


class ProjectTask(models.Model):
    """inherited project task"""
    _inherit = "project.task"

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            # Notify project team members
            if task.project_id and task.project_id.team_ids:
                users = task.project_id.team_ids

                for user in users:
                    if user.partner_id:
                        self.env['bus.bus']._sendone(
                            user.partner_id,
                            'simple_notification',
                            {
                                'type': 'info',
                                'title': _('New Task Created'),
                                'message': _(
                                    'A new task "%s" has been created in project "%s".'
                                ) % (task.name, task.project_id.name),
                                'sticky': True,
                            }
                        )
        return tasks
