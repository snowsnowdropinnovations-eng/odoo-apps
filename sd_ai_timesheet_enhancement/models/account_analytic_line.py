from odoo import fields, models

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def action_open_ai_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'AI Enhancer',
            'view_mode': 'form',
            'res_model': 'ai.timesheet.wizard',
        }