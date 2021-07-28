# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _available_multi_criteria_multi_gift_programs(self):
        """
        Programs that are multi-criteria and multi-gift
        Programs wich filter applies to our order customer or no customer filter
        Programs not applied already
        Programs that aren't due
        Only auto-applied and no coupon programs
        Only programs applicable on current order
        If a global program is already applied, discard it
        """
        self.ensure_one()
        programs_applied = self.no_code_promo_program_ids | self.code_promo_program_id
        domain = [
            ("id", "not in", programs_applied.ids),
            ("sale_coupon_criteria", "=", "multi_product"),
            ("promo_applicability", "=", "on_current_order"),
            ("coupon_ids", "=", False),
            ("reward_type", "=", "multi_gift"),
        ]
        # We can't apply two promo codes in one single order
        if self.code_promo_program_id:
            domain += [("promo_code_usage", "=", "no_code_needed")]
        product_id = self.env.context.get("product_id")
        if product_id:
            domain += [
                "|",
                ("sale_coupon_criteria_ids.product_ids", "in", [product_id]),
                ("coupon_multi_gift_ids.reward_product_ids", "in", [product_id]),
            ]
        programs = self.env["sale.coupon.program"].search(domain)
        programs = programs._filter_programs_on_partners(self)
        programs = programs._filter_unexpired_programs(self)
        return programs

    def _get_applicable_no_code_promo_program(self):
        """We'll only apply our program and we'll discard other candidates"""
        programs = super()._get_applicable_no_code_promo_program()
        if self.env.context.get("selection_wizard_program"):
            selection_wizard_program = programs.browse(
                self.env.context.get("selection_wizard_program")
            )
            programs = selection_wizard_program
        return programs

    def _remove_invalid_reward_lines(self):
        """Avoid updating other promotions in the context of promo apply"""
        if self.env.context.get("selection_wizard_program"):
            return
        super()._remove_invalid_reward_lines()

    def _update_existing_reward_lines(self):
        """Avoid updating other promotions in the context of promo apply"""
        if self.env.context.get("selection_wizard_program"):
            return
        super()._update_existing_reward_lines()

    def action_open_promotions_wizard(self):
        self.ensure_one()
        return {
            "name": _("Add a promotion"),
            "type": "ir.actions.act_window",
            "res_model": "coupon.selection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_order_id": self.id},
        }
