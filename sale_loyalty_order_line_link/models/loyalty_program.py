from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    related_so_count = fields.Integer(compute="_compute_related_so_count")

    def _compute_related_so_count(self):
        line_data = self.env["sale.order.line"]._read_group(
            [("loyalty_program_id", "in", self.ids)],
            groupby=["loyalty_program_id"],
            aggregates=["order_id:count_distinct"],
        )
        counts = {program.id: count for program, count in line_data}
        for program in self:
            program.related_so_count = counts.get(program.id, 0)

    def action_open_related_sale_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action["domain"] = [("order_line.loyalty_program_id", "in", self.ids)]
        return action
