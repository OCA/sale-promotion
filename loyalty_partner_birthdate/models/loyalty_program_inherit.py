# Copyright 2024 Moka Tourisme (https://www.mokatourisme.fr/).
# @author Damien Horvat <ultrarushgame@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    birthday_trigger_enabled = fields.Boolean('Enable Birthday Trigger',
        help="Enable to trigger the discount based on birthday.")

    birthday_trigger_mode = fields.Selection([
            ('before', 'Before Birthday'),
            ('exact', 'Exact Birthday'),
            ('after', 'After Birthday'),
        ], string='Birthday Trigger Mode', default='before',
        help="Trigger the discount before, on, or after the birthday.")

    birthday_check_days = fields.Integer('Birthday Check Days', default=7,
        help="Number of days before or after the birthday to check.")
    
    @api.model
    def _is_partner_birthday_within_range(self, partner):
        """Check if partner's birthday is within the specified range."""
        if not self.birthday_trigger_enabled:
            return False
        
        today = datetime.now().date()
        birthday = partner.birthdate
        if not birthday:
            return False
        
        if self.birthday_trigger_mode == 'before':
            deadline_date = today + timedelta(days=self.birthday_check_days)
        elif self.birthday_trigger_mode == 'exact':
            deadline_date = today
        else: 
            deadline_date = today - timedelta(days=self.birthday_check_days)
        
        return deadline_date

    def _compute_amount(self, currency_to):
        self.ensure_one()
        
        deadline_date = self._is_partner_birthday_within_range(self)
        
        if not deadline_date:
            return super()._compute_amount(currency_to)
        
        if self.birthday_trigger_mode == 'exact':
            valid_partners = self.env['res.partner'].search([('birthdate', '=', deadline_date)])
        elif self.birthday_trigger_mode == 'before':
            valid_partners = self.env['res.partner'].search([('birthdate', '<=', deadline_date)])
        else: 
            valid_partners = self.env['res.partner'].search([('birthdate', '>=', deadline_date)])
        
        valid_amount = super()._compute_amount(currency_to)
        
        if self.program_type == 'birthday' and valid_partners:
            valid_amount *= len(valid_partners)
        
        return valid_amount
    
    @api.model
    def generate_birthday_loyalty_cards(self):
        """Cron method to generate birthday loyalty cards."""
        birthday_rules = self.search([('birthday_trigger_enabled', '=', True)])
        for rule in birthday_rules:
            valid_partners = self.env['res.partner'].search([('birthdate_date', '!=', False)])
            
            today = datetime.now().date()
            if rule.birthday_trigger_mode == 'before':
                target_date = today + relativedelta(days=rule.birthday_check_days)
                valid_partners = valid_partners.filtered(lambda partner: 
                    partner.birthdate_date.month == target_date.month and 
                    partner.birthdate_date.day == target_date.day
                )
            elif rule.birthday_trigger_mode == 'exact':
                valid_partners = valid_partners.filtered(lambda partner: 
                    partner.birthdate_date.month == today.month and 
                    partner.birthdate_date.day == today.day
                )
            elif rule.birthday_trigger_mode == 'after': 
                target_date = today - relativedelta(days=rule.birthday_check_days)
                valid_partners = valid_partners.filtered(lambda partner: 
                    partner.birthdate_date.month == target_date.month and 
                    partner.birthdate_date.day == target_date.day
                )


            for partner in valid_partners:
                try:
                    loyalty_card = self.env['loyalty.card'].create({
                        'program_id': rule.id,
                        'partner_id': partner.id,
                        'points' : 1
                    })
                except Exception as e:
                    logging.error(f"Error creating loyalty card for partner {partner.id}: {e}")



