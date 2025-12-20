// ui/mario/js/mario_events.js
window.TONOSAMA = window.TONOSAMA || {};
const S = TONOSAMA.state;

TONOSAMA.events = {
    bind() {
        // modal
        document.getElementById("btnCloseModal").addEventListener("click", (e) => {
            e.stopPropagation();
            TONOSAMA.render.closeModal();
        });
        document.getElementById("imageModal").addEventListener("click", () => TONOSAMA.render.closeModal());

        // capture buttons
        document.getElementById("btnCaptureCamera").addEventListener("click", () => document.getElementById("cameraInput").click());
        document.getElementById("btnCapturePhoto").addEventListener("click", () => document.getElementById("photoInput").click());

        document.getElementById("cameraInput").addEventListener("change", (e) => this.handleCaptureUpload(e));
        document.getElementById("photoInput").addEventListener("change", (e) => this.handleCaptureUpload(e));

        // select
        document.getElementById("selectList").addEventListener("change", (e) => {
            const t = e.target;
            if (t && t.matches("input[type=checkbox][data-id]")) {
                const id = t.getAttribute("data-id");
                this.toggleSelect(id, !!t.checked);
            }
        });

        document.getElementById("btnSelectConfirm").addEventListener("click", async () => {
            if (S.selectedIds.length !== 3) return;
            await this.confirmSelect();
        });

        // plan/lang
        document.getElementById("planToggle").addEventListener("input", async (e) => {
            const v = Number(e.target.value);
            S.plan = v;
            TONOSAMA.render.showToast(v === 69 ? "✨ 69コース：生成します" : "🧪 39コース：空欄でOK");
            if (v === 69) await this.ensureGenerated();
            TONOSAMA.render.renderCard();
        });

        document.getElementById("langSelect").addEventListener("change", (e) => {
            S.activeLang = e.target.value;
            TONOSAMA.render.renderCard();
        });

        // buttons
        document.getElementById("btnBack").addEventListener("click", () => this.goBack());
        document.getElementById("btnReject").addEventListener("click", () => this.reject());
        document.getElementById("btnApprove").addEventListener("click", () => this.approve());
        document.getElementById("btnSubmit").addEventListener("click", async () => this.submit());
    },

    toggleSelect(id, checked) {
        const set = new Set(S.selectedIds);
        if (checked) set.add(id); else set.delete(id);

        // enforce exactly 3 (hard guard)
        if (set.size > 3) {
            TONOSAMA.render.showToast("❌ 3つまでです");
            // revert UI checkbox
            const cb = document.querySelector(`input[type=checkbox][data-id="${id}"]`);
            if (cb) cb.checked = false;
            return;
        }

        S.selectedIds = Array.from(set);
        TONOSAMA.render.updateSelectCount();
    },

    async handleCaptureUpload(e) {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;
        if (S.isProcessing) return;

        S.isProcessing = true;
        TONOSAMA.render.showLoading(true);

        const base64 = await this.fileToBase64(file);
        try {
            const res = await TONOSAMA.api.extractItems({ base64, mimeType: file.type || "image/jpeg" });
            S.extractedItems = (res.items || []).slice(0, 10);

            if (S.extractedItems.length < 3) {
                TONOSAMA.render.showToast("❌ 品目が足りません。撮り直してください");
                TONOSAMA.render.setStep(0);
            } else {
                S.selectedIds = [];
                TONOSAMA.render.setStep(1);
                TONOSAMA.render.renderSelectList();
                TONOSAMA.render.showToast("✅ 10品を抽出しました");
            }
        } catch (err) {
            console.error(err);
            TONOSAMA.render.showToast("❌ 読み取りに失敗しました");
            TONOSAMA.render.setStep(0);
        } finally {
            TONOSAMA.render.showLoading(false);
            S.isProcessing = false;
        }
    },

    async confirmSelect() {
        TONOSAMA.render.showLoading(true);
        try {
            await TONOSAMA.api.selectItems(S.selectedIds);
            S.selectedItems = S.extractedItems.filter(x => S.selectedIds.includes(x.tmp_item_id));
            S.currentIndex = 0;
            S.plan = Number(document.getElementById("planToggle").value) || 39;
            TONOSAMA.render.setStep(2);
            TONOSAMA.render.renderLangOptions();
            if (S.plan === 69) await this.ensureGenerated();
            TONOSAMA.render.renderCard();
            TONOSAMA.render.showToast("🚀 3品でデモ開始");
        } finally {
            TONOSAMA.render.showLoading(false);
        }
    },

    async ensureGenerated() {
        if (S.plan !== 69) return;
        TONOSAMA.render.showLoading(true);
        try {
            const langs = S.langs || [];
            const res = await TONOSAMA.api.generatePreview({ planCode: 69, langs, toneStyle: "standard" });
            S.generated = res;
            TONOSAMA.render.showToast(res.cache?.hit ? "🧠 キャッシュ表示" : "✨ 生成完了");
        } catch (e) {
            console.error(e);
            TONOSAMA.render.showToast("❌ 生成に失敗しました");
        } finally {
            TONOSAMA.render.showLoading(false);
        }
    },

    // card navigation
    goBack() {
        if (S.currentIndex <= 0) return;
        if (S.isEditing) {
            if (!confirm("編集中の内容は破棄されます。よろしいですか？")) return;
            this.cancelEdit();
        }
        S.currentIndex--;
        TONOSAMA.render.renderCard();
        TONOSAMA.render.showToast("⏪ 前の品目に戻りました");
    },

    reject() {
        this.enableEdit();
    },

    approve() {
        if (S.isEditing) { alert("編集を保存してからOKを押してください"); return; }
        TONOSAMA.render.showToast("✅ ありがとうございます！");
        S.currentIndex++;

        const card = document.querySelector(".card");
        if (card) {
            card.style.transform = "translateX(150%) rotate(20deg)";
            card.style.opacity = "0";
        }
        setTimeout(() => TONOSAMA.render.renderCard(), 250);
    },

    // edit
    enableEdit() {
        const view = document.getElementById("descView");
        const hint = document.getElementById("editHint");
        const area = document.getElementById("editArea");
        const ta = document.getElementById("editText");
        if (!view || !area || !ta) return;

        // 39コースは編集不要
        if (S.plan === 39) return;

        S.isEditing = true;
        view.style.display = "none";
        if (hint) hint.style.display = "none";
        area.classList.add("active");

        const it = S.selectedItems[S.currentIndex];
        const text = TONOSAMA.render.getActiveText(it.tmp_item_id).body;
        ta.value = text;
        setTimeout(() => ta.focus(), 50);

        TONOSAMA.render.showToast("✏️ お気軽に修正してください");
        this.bindEditButtons();
    },

    bindEditButtons() {
        const cancel = document.getElementById("btnEditCancel");
        const save = document.getElementById("btnEditSave");
        if (cancel) cancel.onclick = () => this.cancelEdit();
        if (save) save.onclick = () => this.saveEdit();
    },

    cancelEdit() {
        S.isEditing = false;
        const view = document.getElementById("descView");
        const hint = document.getElementById("editHint");
        const area = document.getElementById("editArea");
        if (view) view.style.display = "block";
        if (hint) hint.style.display = "block";
        if (area) area.classList.remove("active");
    },

    saveEdit() {
        const ta = document.getElementById("editText");
        if (!ta) return;
        const text = ta.value.trim();
        if (!text) { alert("説明文を入力してください"); return; }

        // local override
        const it = S.selectedItems[S.currentIndex];
        // overwrite generated object locally
        if (S.generated && S.generated.items) {
            const item = S.generated.items.find(x => x.tmp_item_id === it.tmp_item_id);
            const lang = S.activeLang || "ja";
            if (item && item[lang]) item[lang].review_18s = text;
        }

        this.cancelEdit();
        TONOSAMA.render.renderCard();
        TONOSAMA.render.showToast("💾 保存しました！");
    },

    // item image
    async triggerItemImage() {
        document.getElementById("itemImageInput").click();
    },

    async handleItemImageUpload(e) {
        const file = e.target.files && e.target.files[0];
        e.target.value = "";
        if (!file) return;

        const it = S.selectedItems[S.currentIndex];
        const base64 = await this.fileToBase64(file);
        S.itemImages[it.tmp_item_id] = `data:${file.type || "image/jpeg"};base64,${base64}`;

        TONOSAMA.render.renderCard();
        TONOSAMA.render.showToast("📷 写真を選択しました");

        // upload
        try {
            await TONOSAMA.api.uploadItemImage(it.tmp_item_id, { base64, mimeType: file.type || "image/jpeg" });
        } catch (err) {
            console.error(err);
            TONOSAMA.render.showToast("⚠️ 写真保存に失敗（デモは継続）");
        }
    },

    bindCardImageEvents() {
        const btnPhoto = document.getElementById("btnItemPhoto");
        const btnChange = document.getElementById("btnItemChange");
        const btnRemove = document.getElementById("btnItemRemove2");
        const img = document.getElementById("imgPreview");

        const input = document.getElementById("itemImageInput");
        if (input && !input.__bound) {
            input.addEventListener("change", (e) => this.handleItemImageUpload(e));
            input.__bound = true;
        }

        const openPicker = () => this.triggerItemImage();
        if (btnPhoto) btnPhoto.onclick = openPicker;
        if (btnChange) btnChange.onclick = (ev) => { ev.stopPropagation(); openPicker(); };
        if (btnRemove) btnRemove.onclick = (ev) => {
            ev.stopPropagation();
            const it = S.selectedItems[S.currentIndex];
            delete S.itemImages[it.tmp_item_id];
            TONOSAMA.render.showToast("🗑️ 写真を削除しました");
            TONOSAMA.render.renderCard();
            this.afterCardRender();
        };
        if (img) img.onclick = () => TONOSAMA.render.openModal(img.getAttribute("src"));
    },

    afterCardRender() {
        this.bindCardImageEvents();
        const view = document.getElementById("descView");
        if (view) view.onclick = () => this.enableEdit();
    },

    async submit() {
        TONOSAMA.render.showLoading(true);
        try {
            await TONOSAMA.api.completeDemo({
                plan: S.plan,
                selected_tmp_item_ids: S.selectedIds,
                item_images_count: Object.keys(S.itemImages || {}).length
            });
            alert("確定しました。本登録URLを送付します（実装後）");
        } catch (e) {
            console.error(e);
            alert("送信に失敗しました（デモは保存されている想定）");
        } finally {
            TONOSAMA.render.showLoading(false);
        }
    },

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const r = new FileReader();
            r.onload = () => {
                const dataUrl = String(r.result || "");
                const b64 = dataUrl.split(",")[1] || "";
                resolve(b64);
            };
            r.onerror = reject;
            r.readAsDataURL(file);
        });
    }
};
