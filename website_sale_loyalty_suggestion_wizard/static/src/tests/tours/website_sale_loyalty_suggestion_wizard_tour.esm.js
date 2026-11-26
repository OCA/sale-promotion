import {registry} from "@web/core/registry";
import tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add("website_sale_loyalty_suggestion_wizard_tour", {
    url: "/shop",
    steps: () => [
        // 1. Add product to cart
        ...tourUtils.addToCart({productName: "Product A"}),
        // 2. Go to promotions
        {
            content: "go to promotions",
            trigger: "a[href='/promotions']",
        },
        // 3. Click Apply on the promotion
        {
            content: "click apply promotion",
            trigger:
                ".card:has(.card-body:has(.card-text:contains('Test Loyalty Order Suggestion'))) a.btn-primary:contains('Apply')",
        },
        // 4. Wait for modal and confirm
        {
            content: "wait for wizard modal and confirm",
            trigger: ".modal-dialog footer button.btn-primary",
        },
        // 5. Verify redirect to cart
        {
            content: "check we are in cart and promotion applied",
            trigger: "body:has(#cart_products)",
            isCheck: true,
        },
    ],
});
