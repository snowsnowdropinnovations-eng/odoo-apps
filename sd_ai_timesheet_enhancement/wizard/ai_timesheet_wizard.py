from odoo import api, fields, models
from bs4 import BeautifulSoup


class AiTimesheetWizard(models.TransientModel):
    _name = "ai.timesheet.wizard"
    _description = "Ai Timesheet Wizard"


    account_analytic_line_id = fields.Many2one("account.analytic.line")
    html_description = fields.Html(string="Description")

    @api.model
    def default_get(self, fields_list):
        res = super(AiTimesheetWizard, self).default_get(fields_list)
        if self.env.context.get('active_id'):
            timesheet = self.env['account.analytic.line'].browse(self.env.context['active_id'])
            res['account_analytic_line_id'] = timesheet.id
            res['html_description'] = timesheet.name or ''
        return res


    def action_paste_description(self):
        """Clean HTML and write plain text back to timesheet."""
        for wizard in self:
            if wizard.account_analytic_line_id:
                # Remove all HTML tags using BeautifulSoup
                soup = BeautifulSoup(wizard.html_description or '', 'html.parser')
                clean_text = soup.get_text(separator=' ', strip=True)
                wizard.account_analytic_line_id.write({'name': clean_text})
        return {'type': 'ir.actions.act_window_close'}