// ui/mario/js/mario_state.js
window.TONOSAMA = window.TONOSAMA || {};

TONOSAMA.state = {
    config: null,

    // step0
    sourceAssetId: null,
    extractedItems: [], // up to 10: {tmp_item_id,name_ja,price,category_ja,...}
    // step1
    selectedIds: [],
    selectedItems: [],

    // step2
    currentIndex: 0,
    plan: 39, // 39 or 69
    langs: [], // from preset
    activeLang: "ja",

    // per item image
    itemImages: {}, // tmp_item_id -> dataURL
    // generation cache (token saver)
    previewCache: {}, // key -> response
    // generated preview payload for active plan/lang
    generated: null, // last generate response

    isEditing: false,
    isProcessing: false,

    // Phase 3 (Hearing)
    currentItem: null, // P3: Active HearingItem
    completed: false // P3: All items confirmed
};

TONOSAMA.util = {
    nowIso: () => new Date().toISOString()
};
