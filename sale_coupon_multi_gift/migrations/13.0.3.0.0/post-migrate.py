# Copyright 2022 Tecnativa - David Vidal
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Link lines and reward lines"""
    multi_gift_programs = env["sale.coupon.program"].search(
        [("reward_type", "=", "multi_gift")]
    )
    for program in multi_gift_programs:
        order_lines = env["sale.order.line"].search(
            [("is_reward_line", "=", "True"), ("coupon_program_id", "=", program.id)]
        )
        for reward_line in program.coupon_multi_gift_ids:
            reward_lines = order_lines.filtered(
                lambda x: x.product_id in reward_line.reward_product_ids
            )
            # Remember the choice
            for product in reward_lines.product_id:
                reward_lines.write(
                    {
                        "multi_gift_reward_line_id": reward_line.id,
                        "multi_gift_reward_line_id_option_product_id": product.id,
                    }
                )
            order_lines -= reward_lines
