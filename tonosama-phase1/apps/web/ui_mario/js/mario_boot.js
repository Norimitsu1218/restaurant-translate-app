// ui/mario/js/mario_boot.js
window.TONOSAMA = window.TONOSAMA || {};
const S = TONOSAMA.state;

(function boot() {
    const cfg = window.__TONOSAMA__;
    if (!cfg || !cfg.apiBase || !cfg.demoSessionId) {
        alert("設定が不足しています（apiBase / demoSessionId）");
        return;
    }
    S.config = cfg;

    // preview preset -> langs
    // friendly_nations = en + zh-Hant + de（親日寄せ）
    const preset = cfg.previewPreset || "friendly_nations";
    if (preset === "friendly_nations") S.langs = ["en", "zh-Hant", "de"];
    else if (preset === "eu_focus") S.langs = ["en", "de", "fr"];
    else if (preset === "asia_mix") S.langs = ["en", "ko", "zh-Hant"];
    else S.langs = ["en", "zh-Hant", "de"];

    S.activeLang = "ja";
    S.plan = cfg.defaultPlan || 39;

    // initial step
    TONOSAMA.render.setStep(0);

    // Phase 3 Override
    if (cfg.mode === "hearing") {
        TONOSAMA.render.setStep(2); // Jump to Review

        // Hide Back Button initially? Or always?
        // P3 Back logic is complicated (Server side cursor). 
        // For now, let's just fetch the first item.
        setTimeout(async () => {
            TONOSAMA.render.showLoading(true);
            try {
                await TONOSAMA.events.loadNextHearingItem();
                TONOSAMA.render.showToast("🚀 確認スタート");
            } catch (e) {
                console.error(e);
                alert("起動に失敗しました (Network Error?)");
            } finally {
                TONOSAMA.render.showLoading(false);
            }
        }, 500);
    }

    // bind global events
    TONOSAMA.events.bind();

    // render initial options
    document.getElementById("planToggle").value = String(S.plan);
    TONOSAMA.render.renderLangOptions();

    // whenever card renders, bind per-card handlers
    const origRender = TONOSAMA.render.renderCard.bind(TONOSAMA.render);
    TONOSAMA.render.renderCard = function () {
        origRender();
        TONOSAMA.events.afterCardRender();
    };

    TONOSAMA.render.showToast("🏁 デモ開始");
})();
