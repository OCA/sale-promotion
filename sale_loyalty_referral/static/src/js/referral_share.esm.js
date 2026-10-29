const copy = async (btn, text) => {
    await navigator.clipboard.writeText(text);
    const span = btn.querySelector("span") || btn;
    const original = span.textContent;
    span.textContent = "Copied!";
    setTimeout(() => (span.textContent = original), 2000);
};

document.addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".s_referral_share");
    if (!btn) {
        return;
    }
    const url = btn.dataset.url;
    if (navigator.share) {
        try {
            await navigator.share({url, text: btn.dataset.text || url});
        } catch (e) {
            if (e.name !== "AbortError") {
                await copy(btn, url);
            }
        }
    } else {
        await copy(btn, url);
    }
});
