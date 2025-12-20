// ui/mario/js/mario_render.js
window.TONOSAMA = window.TONOSAMA || {};
const S = TONOSAMA.state;

TONOSAMA.render = {
    showToast(msg) {
        const toast = document.getElementById("toast");
        toast.textContent = msg;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 1800);
    },

    showLoading(on) {
        document.getElementById("loadingSpinner").classList.toggle("active", !!on);
    },

    openModal(src) {
        if (!src) return;
        const modal = document.getElementById("imageModal");
        document.getElementById("modalImage").src = src;
        modal.style.display = "flex";
    },

    closeModal() {
        document.getElementById("imageModal").style.display = "none";
    },

    setStep(step) {
        const cap = document.getElementById("captureSection");
        const sel = document.getElementById("selectSection");
        const main = document.getElementById("mainSection");
        cap.style.display = step === 0 ? "block" : "none";
        sel.style.display = step === 1 ? "block" : "none";
        main.style.display = step === 2 ? "block" : "none";
    },

    renderSelectList() {
        const list = document.getElementById("selectList");
        list.innerHTML = "";

        for (const it of S.extractedItems) {
            const checked = S.selectedIds.includes(it.tmp_item_id) ? "checked" : "";
            const price = (it.price && it.price.raw) ? it.price.raw : "";
            const cat = it.category_ja || "";

            const row = document.createElement("div");
            row.className = "select-row";
            row.innerHTML = `
        <div class="select-row-left">
          <div class="select-name">${this.esc(it.name_ja || "")}</div>
          <div class="select-sub">${this.esc(cat)} ${this.esc(price)}</div>
        </div>
        <input type="checkbox" data-id="${it.tmp_item_id}" ${checked} />
      `;
            list.appendChild(row);
        }

        this.updateSelectCount();
    },

    updateSelectCount() {
        const el = document.getElementById("selectCount");
        el.textContent = `${S.selectedIds.length} / 3`;
        document.getElementById("btnSelectConfirm").disabled = (S.selectedIds.length !== 3);
    },

    updateProgress() {
        document.getElementById("progress").textContent = `${S.currentIndex + 1} / ${S.selectedItems.length} 品目`;
    },

    updateEncouragement() {
        const i = S.currentIndex + 1;
        const n = S.selectedItems.length || 3;
        const p = i / n;
        let msg = "それでは1品目から始めましょう！";
        if (p >= 0.9) msg = "あと1品です！頑張りましょう 🏁";
        else if (p >= 0.75) msg = "もうすぐ終わります！あと少し 🚀";
        else if (p >= 0.5) msg = "ちょうど半分まできました！⭐";
        else if (p >= 0.25) msg = "いい調子です！あと少しです 💪";
        document.getElementById("encouragement").textContent = msg;
    },

    renderLangOptions() {
        const sel = document.getElementById("langSelect");
        sel.innerHTML = "";
        const langs = ["ja", ...S.langs]; // jaは固定表示
        for (const l of langs) {
            const opt = document.createElement("option");
            opt.value = l;
            opt.textContent = l === "ja" ? "日本語" :
                l === "en" ? "English" :
                    l === "de" ? "Deutsch" :
                        l === "zh-Hant" ? "繁體中文" : l;
            sel.appendChild(opt);
        }
        sel.value = S.activeLang;
    },

    fingerprintItems(items) {
        return (items || [])
            .map(it => `${it.name_ja || ""}|${(it.price && it.price.raw) || ""}|${it.category_ja || ""}`)
            .join("||");
    },

    getActiveText(tmpItemId) {
        if (S.plan === 39) {
            return { title: "", body: "（39コースでは食レポは空欄のままでOKです）", editable: false };
        }
        const g = S.generated;
        if (!g || !g.items) return { title: "", body: "（生成待ち）", editable: false };

        const item = g.items.find(x => x.tmp_item_id === tmpItemId);
        if (!item) return { title: "", body: "（生成対象外）", editable: false };

        const lang = S.activeLang || "ja";
        const t = item[lang] || item["ja"];
        const review = t?.review_18s || "";
        const how = t?.how_to_eat || "";
        const pair = t?.pairing || "";
        const body = [
            review,
            how ? `食べ方：${how}` : "",
            pair ? `ペアリング：${pair}` : ""
        ].filter(Boolean).join("\n\n");

        return { title: "", body: body || "（生成なし）", editable: true };
    },

    renderCard() {
        if (S.currentIndex >= S.selectedItems.length) {
            this.showComplete();
            return;
        }
        const it = S.selectedItems[S.currentIndex];
        const hasImage = !!S.itemImages[it.tmp_item_id];
        const img = S.itemImages[it.tmp_item_id] || "";

        const metaPrice = (it.price && it.price.raw) ? it.price.raw : "";
        const metaCat = it.category_ja || "";

        const text = this.getActiveText(it.tmp_item_id);

        document.getElementById("cardContainer").innerHTML = `
      <div class="card">
        <div class="dish-name">${this.esc(it.name_ja || "")}</div>
        <div class="dish-meta">
          <div class="dish-price">${this.esc(metaPrice)}</div>
          <div class="dish-cat">${this.esc(metaCat)}</div>
        </div>

        <div class="image-upload-section">
          <div class="image-upload-label">料理の写真</div>

          <div class="image-upload-buttons ${hasImage ? "hidden" : ""}">
            <div class="upload-button" id="btnItemPhoto">
              <span class="icon">📷</span>
              <span class="label">写真を選択</span>
            </div>
            <div class="upload-button" id="btnItemRemove" style="opacity:.5;pointer-events:none;">
              <span class="icon">🗑️</span>
              <span class="label">削除</span>
            </div>
          </div>

          <div class="image-preview-container ${hasImage ? "has-image" : ""}">
            <img src="${img}" class="image-preview" id="imgPreview" alt="${this.esc(it.name_ja || "")}">
            <div class="image-actions">
              <button class="image-action-btn" id="btnItemChange">📷 変更</button>
              <button class="image-action-btn" id="btnItemRemove2">🗑️ 削除</button>
            </div>
          </div>
        </div>

        <div class="dish-description" id="descView">${this.escMultiline(text.body)}</div>
        <div class="edit-hint" id="editHint">${text.editable ? "タップして編集" : ""}</div>

        <div class="edit-area" id="editArea">
          <textarea id="editText"></textarea>
          <div class="edit-buttons">
            <button class="edit-button cancel-button" id="btnEditCancel">キャンセル</button>
            <button class="edit-button save-button" id="btnEditSave">保存</button>
          </div>
        </div>
      </div>
    `;

        S.isEditing = false;
        this.updateProgress();
        this.updateEncouragement();

        document.getElementById("btnBack").style.display = S.currentIndex === 0 ? "none" : "flex";
    },

    showComplete() {
        document.getElementById("cardContainer").style.display = "none";
        document.getElementById("actionButtons").style.display = "none";
        document.getElementById("progress").style.display = "none";
        document.getElementById("encouragement").style.display = "none";
        document.getElementById("completeScreen").style.display = "block";
        this.showToast("🎉 お疲れさまでした！");
    },

    esc(s) {
        return String(s).replace(/[&<>"']/g, c => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        }[c]));
    },

    escMultiline(s) {
        return this.esc(s).replace(/\n/g, "<br>");
    }
};
