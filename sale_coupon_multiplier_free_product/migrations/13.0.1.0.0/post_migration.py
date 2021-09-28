# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """We're depending now on `sale_coupon_order_line_link` which eases the matching
    of the promoted lines. We want to link the existing promoted lines"""
    programs = (
        env["sale.coupon.program"]
        .with_context(active_test=False)
        .search([("reward_type", "=", "multiple_of")])
    )
    for program in programs:
        sales = env["sale.order"].search(
            [
                "|",
                ("applied_coupon_ids", "in", program.ids),
                ("code_promo_program_id", "=", program.id),
            ]
        )
        lines = sales.filtered(
            lambda x: x.is_reward_line and x.product_id == program.reward_product_id
        )
        lines.write({"coupon_program_id": program.id})
