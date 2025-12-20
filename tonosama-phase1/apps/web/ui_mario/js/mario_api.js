// ui/mario/js/mario_api.js
window.TONOSAMA = window.TONOSAMA || {};
const S = TONOSAMA.state;

TONOSAMA.api = {
    async post(path, body) {
        const url = `${S.config.apiBase}${path}`;
        const resp = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        if (!resp.ok) {
            const text = await resp.text().catch(() => "");
            throw new Error(`API ${path} failed: ${resp.status} ${text}`);
        }
        return await resp.json();
    },

    async extractItems({ base64, mimeType }) {
        return await this.post("/api/demo/extract_items", {
            demo_session_id: S.config.demoSessionId,
            image: { mime_type: mimeType, base64 }
        });
    },

    async selectItems(selectedTmpItemIds) {
        return await this.post("/api/demo/select_items", {
            demo_session_id: S.config.demoSessionId,
            selected_tmp_item_ids: selectedTmpItemIds
        });
    },

    async uploadItemImage(tmpItemId, { base64, mimeType }) {
        return await this.post("/api/demo/upload_item_image", {
            demo_session_id: S.config.demoSessionId,
            tmp_item_id: tmpItemId,
            image: { mime_type: mimeType, base64 }
        });
    },

    async generatePreview({ planCode, langs, toneStyle }) {
        const key = `${S.config.demoSessionId}:${planCode}:${toneStyle}:${langs.join(",")}:${TONOSAMA.render.fingerprintItems(S.selectedItems)}`;
        if (S.previewCache[key]) return { ...S.previewCache[key], cache: { hit: true, cache_key: key } };

        const res = await this.post("/api/demo/generate_preview", {
            demo_session_id: S.config.demoSessionId,
            plan_code: planCode,
            preview_langs: langs,
            tone_style: toneStyle || "standard"
        });

        S.previewCache[key] = { ...res, cache: { hit: false, cache_key: key } };
        return S.previewCache[key];
    },

    async completeDemo(payload) {
        // 申込へ繋ぐ場合に使う（任意）
        return await this.post("/api/demo/complete", {
            demo_session_id: S.config.demoSessionId,
            ...payload
        });
    }
};
