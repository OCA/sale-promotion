from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    related_so_count = fields.Integer(compute="_compute_related_so_count")

    def _compute_related_so_count(self):
        for program in self:
            program.related_so_count = self.env["sale.order"].search_count(
                [("order_line.loyalty_program_id", "=", program.id)]
            )

    def action_open_related_sale_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action["domain"] = [("order_line.loyalty_program_id", "=", self.id)]
        return action
