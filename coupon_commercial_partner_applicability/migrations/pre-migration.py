from openupgradelib import openupgrade

namespec = [
    ("coupon_commercial_partner_applicability", "sale_loyalty_partner_applicability")
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.update_module_names(env.cr, namespec, merge_modules=True)
