from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TimeOffFormInherit(models.Model):
    _inherit = 'hr.leave'

    cancel_reason = fields.Char(string='Cancel Reason')
    medical_attachment_ids = fields.Many2many(
        'ir.attachment',
        relation='hrl_leave_request_medical_relation',
        string="Medical",
        store=True, index=True
    )
    leave_type = fields.Selection([
        ('hajj', 'Hajj'),
        ('sick', 'Sick'),
        ('unpaid', 'Unpaid'),
        ('annual', 'Annual'),
        ('casual', 'Casual'),
        ('compensatory', 'Compensatory'),
        ('half_day', 'Half Day'),
    ], string='Leave Type', tracking=True, index=True, related='holiday_status_id.leave_type')


class TImeOffTypeInherit(models.Model):
    _inherit = 'hr.leave.type'

    leave_type = fields.Selection([
        ('hajj', 'Hajj'),
        ('sick', 'Sick'),
        ('unpaid', 'Unpaid'),
        ('annual', 'Annual'),
        ('casual', 'Casual'),
        ('compensatory', 'Compensatory'),
        ('half_day', 'Half Day'),
    ], string='Leave Type', tracking=True, index=True)

    @api.constrains('leave_type')
    def _check_unique_leave_type(self):
        for record in self:
            if record.leave_type:
                # Search for another record with same type
                existing = self.env['hr.leave.type'].search([
                    ('leave_type', '=', record.leave_type),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        f"The leave type '{dict(self._fields['leave_type'].selection).get(record.leave_type)}' "
                        f"is already assigned to another record.")


