# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_model_renames = [
    ("sale.coupon.rule.salesmen.limit", "coupon.rule.salesmen.limit"),
]
_table_renames = [("sale_coupon_rule_salesmen_limit", "coupon_rule_salesmen_limit")]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
