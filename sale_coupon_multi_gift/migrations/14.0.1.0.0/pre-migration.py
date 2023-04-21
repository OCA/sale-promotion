# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_model_renames = [
    ("sale.coupon.reward.product_line", "coupon.reward.product_line"),
]

_table_renames = [
    ("sale_coupon_reward_product_line", "coupon_reward_product_line"),
]

_xmlid_renames = [
    (
        "sale_coupon_multi_gift.sale_coupon_program_view_form_common",
        "sale_coupon_multi_gift.coupon_program_view_form_common",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    openupgrade.rename_xmlids(env.cr, _xmlid_renames)
