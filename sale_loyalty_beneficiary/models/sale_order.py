# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _get_beneficiary_partner_for_loyalty_program(self, program):
        self.ensure_one()
        beneficiary_partner_type = program.beneficiary_partner_type or "partner"
        if beneficiary_partner_type == "partner":
            return self.partner_id
        if beneficiary_partner_type == "invoiced_partner":
            return self.partner_invoice_id
        if beneficiary_partner_type == "commercial_entity":
            return self.partner_id.commercial_partner_id
        raise ValueError(
            _(
                "Unknown beneficiary partner type %(parnter_type)s",
                partner_type=beneficiary_partner_type,
            )
        )

    def _get_or_create_loyalty_card_for_partner(self, program, partner, status):
        self.ensure_one()
        all_points = [p for p in status["points"] if p]
        result = self.env["loyalty.card"]
        if all_points:
            result = self.env["loyalty.card"].search(
                [("partner_id", "=", partner.id), ("program_id", "=", program.id)],
                limit=1,
            )
            if not result:
                result = (
                    self.env["loyalty.card"]
                    .sudo()
                    .with_context(loyalty_no_mail=True, tracking_disable=True)
                    .create(
                        {
                            "program_id": program.id,
                            "partner_id": partner.id,
                            "points": 0,
                            "order_id": self.id,
                        }
                    )
                )
        return result

    def _SaleOrder__try_apply_program(self, program, coupon, status):
        # The original method __try_apply_program from
        # odoo/addons/sale/models/sale_order.py is designed for internal use only
        # (double underscore prefix) and should not be overridden in custom
        # modules. The python interpreter apply the name mangling to the method
        # name to make it harder to create a method that will override it
        # in a subclass. It's still possible to override it by using the
        # name _ClassName__method_name. This is what we do here even if it's
        # not recommended. We do this because we don't have any other choice
        # to override this method in the context of this module.
        self.ensure_one()
        if program.is_nominative and not coupon:
            beneficiary_partner = self._get_beneficiary_partner_for_loyalty_program(
                program
            )
            coupon = self._get_or_create_loyalty_card_for_partner(
                program, beneficiary_partner, status
            )
        return super(SaleOrder, self)._SaleOrder__try_apply_program(
            program, coupon, status
        )
