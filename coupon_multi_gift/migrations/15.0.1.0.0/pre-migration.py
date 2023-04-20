# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def install_new_modules(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_module_module
        SET state='to install'
        WHERE name = 'sale_coupon_multi_gift' AND state='uninstalled'""",
    )


@openupgrade.migrate()
def migrate(env, version):
    install_new_modules(env)
