from odoo import fields

from . import controllers
from . import models
from . import wizard


def _post_init_seed(env):
    """Seed the referral settings and the program's reward. The reward's
    discount product is created here rather than in data so it can adapt to
    optional product fields (e.g. website_sale's required publish_date)."""
    program = env.ref(
        "sale_loyalty_referral.referral_program", raise_if_not_found=False
    )
    if not program:
        return
    params = env["ir.config_parameter"].sudo()
    stored = int(params.get_param("sale_loyalty_referral.referral_program_id") or 0)
    if stored != program.id and not env["loyalty.program"].browse(
        stored
    ).exists().filtered("active"):
        # Point to the seed when unset or when the stored program is gone
        # (e.g. deleted manually or by a module uninstall).
        params.set_param("sale_loyalty_referral.referral_program_id", program.id)
    if not params.get_param("sale_loyalty_referral.referral_base_url"):
        params.set_param("sale_loyalty_referral.referral_base_url", "/")
    if "customer_order_condition" in program._fields and (
        not program.customer_order_condition
    ):
        program.customer_order_condition = "first_ever"
    if program.reward_ids:
        return
    product_vals = {
        "name": "Referral Discount",
        "type": "service",
        "sale_ok": False,
        "purchase_ok": False,
        "list_price": 0,
        "invoice_policy": "order",
    }
    if "publish_date" in env["product.template"]._fields:
        product_vals["publish_date"] = fields.Datetime.now()
    product = env["product.template"].sudo().create(product_vals)
    program.reward_ids = [
        (
            0,
            0,
            {
                "reward_type": "discount",
                "discount": 10,
                "discount_mode": "per_order",
                "discount_applicability": "order",
                "discount_line_product_id": product.product_variant_id.id,
            },
        )
    ]
