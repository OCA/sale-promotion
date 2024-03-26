# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from random import choice
from string import ascii_lowercase, ascii_uppercase, digits

from odoo import _, api, models
from odoo.exceptions import ValidationError


class Coupon(models.Model):
    _inherit = "coupon.coupon"

    _dedup_max_retries = 20

    def _generate_code_from_mask(self, choices):
        def unmask(char):
            char_collection = choices.get(char)
            if char_collection:
                return choice(char_collection)
            return char

        return "".join(unmask(char) for char in self.program_id.custom_code_mask)

    def _get_choice_collections(self):
        def filter_forbidden_characters(char_collection):
            return [
                char
                for char in char_collection
                if char not in self.program_id.custom_code_forbidden_characters
            ]

        return {
            "X": filter_forbidden_characters(ascii_uppercase),
            "x": filter_forbidden_characters(ascii_lowercase),
            "0": filter_forbidden_characters(digits),
        }

    @api.model
    def _generate_code(self):
        """Generate a more readable coupon code from a custom format."""
        # Inherits https://github.com/odoo/odoo/blob/14.0/addons/coupon/models/coupon.py#L15
        # When used this method doesn't call super since it's only the code generation

        if not self.program_id:
            return super()._generate_code()
        choices = self._get_choice_collections()
        code = self._generate_code_from_mask(choices)
        retries = 0
        while len(self.env["coupon.coupon"].search([("code", "=", code)])):
            if retries > self._dedup_max_retries:
                raise ValidationError(
                    _("Unable to generate a non existing random coupon code.")
                )
            code = self._generate_code_from_mask(choices)
            retries += 1

        return code

    def _affect_custom_code_maybe(self):
        for record in self:
            if self.program_id.custom_code:
                record.code = record._generate_code()

    @api.model
    def create(self, vals):
        rv = super().create(vals)
        rv._affect_custom_code_maybe()
        return rv
