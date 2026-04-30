from odoo import api, models
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("reward_origin_generated_line_ids", "reward_id")
    def _compute_margin(self):
        res = super()._compute_margin()
        for line in self.filtered(lambda x: x.reward_origin_generated_line_ids):
            if not line.reward_id.sale_margin_formula:
                continue
            origin_lines = line.reward_origin_generated_line_ids
            eval_context = line._get_reward_eval_context()
            safe_eval(
                str(line.reward_id.sale_margin_formula).strip(),
                eval_context,
                mode="exec",
                nocopy=True,
            )
            origin_lines[0].margin = eval_context.get("result", 0)
            origin_lines[0].margin_percent = (
                origin_lines[0].margin / origin_lines[0].price_subtotal
            )
            break
        return res

    def _get_reward_eval_context(self):
        return {
            "env": self.env,
            "context": self.env.context,
            "user": self.env.user,
            "origin_lines": self.reward_origin_generated_line_ids,
            "reward": self.reward_id,
            "reward_line": self,
            "float_compare": float_compare,
        }
