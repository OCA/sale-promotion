# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_model_renames = [
    ("sale.coupon.criteria", "coupon.criteria"),
]
_table_renames = [("sale_coupon_criteria", "coupon_criteria")]


def install_new_modules(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module
        SET state='to install'
        WHERE name = 'sale_coupon_criteria_multi_product' AND state='uninstalled'""",
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    install_new_modules(env)
