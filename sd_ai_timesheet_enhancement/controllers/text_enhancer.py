import requests
import json

from odoo import http, _
from odoo.http import request


class TextEnhancerController(http.Controller):
    @http.route('/web/text-enhancer/languages', type='json', auth='user')
    def get_languages(self):
        # Get active languages in the system
        lang_obj = request.env['res.lang']
        active_langs = lang_obj.sudo().search([('active', '=', True)])
        return [{'code': lang.code, 'name': lang.name} for lang in active_langs]

    @http.route('/web/text-enhancer/process', type='json', auth='user')
    def process_text(self, text, action, options=None):
        api_endpoint = request.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        api_key = request.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        if not api_key:
            return [False, "settings", _("Your API key is invalid. This may be due to an input error, deletion or deactivation of the key. Please check your Otoolkit settings."), ""]
        payload = json.dumps({
            "text": text,
            "action": action,
            "options": options,
            "odoo_user_id": request.env.user.id
        })
        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/text-enhancer/process/"

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
        except Exception as e:
            return [False, "replace", _("An error has occurred, please try again later.")]

        if response.status_code == 200:
            return [True, "replace" if action in ["translate", "fix_grammar", "improve", "summarize", "elaborate", "paraphrase"] else "insert", response.json()]

        if response.status_code == 401:
            return [False, "settings", _("Your API key is invalid. This may be due to an input error, deletion or deactivation of the key. Please check your Otoolkit settings.")]

        if response.status_code == 400:
            error = response.json()
            if error["type"] == "insufficient_funds":
                return [False, "credit", _("You do not have enough credits to translate. Please add credits to your balance to use this function.")]

        return [False, "replace", _("An error has occurred, please try again later.")]


