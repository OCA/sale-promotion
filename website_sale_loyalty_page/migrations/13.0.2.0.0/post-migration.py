# Copyright 2021 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.convert_field_to_html(
        env.cr,
        "sale_coupon_program",
        openupgrade.get_legacy_name("public_name"),
        "public_name",
    )
