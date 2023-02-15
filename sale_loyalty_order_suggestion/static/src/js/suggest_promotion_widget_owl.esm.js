/** @odoo-module **/
import Registry from "web.widgetRegistry";
import {useService} from "@web/core/utils/hooks";
const {Component} = owl;

class SuggestPromotionWidget extends Component {
    setup() {
        this.data = this.props.record.data;
        this.action = useService("action");
    }
    _onClickButton() {
        // When it's a new line, we can't rely on a line id for the wizard, but
        // we can provide the proper element to find the and restrict the proper
        // rewards.
        // this.$el.find(".fa-gift").prop("special_click", true);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Add a promotion",
            res_model: "coupon.selection.wizard",
            context: {
                active_id: this.data.order_id.res_id,
                default_order_id: this.data.order_id.res_id,
                product_id: this.data.product_id.res_id,
            },
        });
    }
}

SuggestPromotionWidget.template = "sale_coupon_order_suggestion.suggestPromotion";

Registry.add("suggest_promotion_widget", SuggestPromotionWidget);
