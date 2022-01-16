# Copyright 2021 Tecnativa - David Vidal
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """We're depending now on `sale_coupon_order_line_link` which eases the matching
    of the promoted lines. We want to link the existing promoted lines.
    """
    programs = (
        env["sale.coupon.program"]
        .with_context(active_test=False)
        .search([("reward_type", "=", "multiple_of")])
    )
    for program in programs:
        # TODO: Take into account program dates
        lines = env["sale.order.line"].search(
            [
                ("product_id", "=", program.reward_product_id.id),
                ("is_reward_line", "=", True),
            ],
        )
        openupgrade.logged_query(
            env.cr,
            "UPDATE sale_order_line SET coupon_program_id = %s WHERE id in %s",
            (program.id, tuple(lines.ids)),
        )
