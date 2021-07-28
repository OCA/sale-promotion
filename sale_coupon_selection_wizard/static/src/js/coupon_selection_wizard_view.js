odoo.define("sale_coupon_selection_wizard.coupon_selection_wizard_form", function(
    require
) {
    "use strict";

    var FormController = require("web.FormController");
    var FormView = require("web.FormView");
    var FormRenderer = require("web.FormRenderer");
    var viewRegistry = require("web.view_registry");
    var CouponSelectionMixin = require("sale_coupon_selection_wizard.CouponSelectionMixin");

    var CouponSelectionWizardFormRenderer = FormRenderer.extend({
        /**
         * @override
         */
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                self.$el.append($("<div>", {class: "promotion_container"}));
                self.renderPromotion(self.promotionHtml);
            });
        },

        /**
         * Renders the promotion wizard within the form
         *
         * @param {String} promotionHtml the evaluated template of
         *   the product configurator
         */
        renderPromotion: function(promotionHtml) {
            var $promotionContainer = this.$(".promotion_container");
            $promotionContainer.empty();
            var $promotionHtml = $(promotionHtml);
            $promotionHtml.appendTo($promotionContainer);
        },
    });

    var CouponSelectionWizardFormController = FormController.extend(
        CouponSelectionMixin,
        {
            start: function() {
                var self = this;
                return this._super.apply(this, arguments).then(function() {
                    self.$el.addClass("o_coupon_wizard");
                });
            },
        }
    );

    var CouponSelectionWizardFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: CouponSelectionWizardFormController,
            Renderer: CouponSelectionWizardFormRenderer,
        }),
    });

    viewRegistry.add("coupon_selection_wizard_form", CouponSelectionWizardFormView);
    return CouponSelectionWizardFormView;
});
