(function () {
    var data = window.__ANTIGRAVITY_I18N_DATA__ || {};
    var EXACT = data.exact || {};
    var REVERSE_MAP = data.reverse_map || {};
    var REGEX_RULES = [];
    if (Array.isArray(data.regex_rules)) {
        for (var i = 0; i < data.regex_rules.length; i++) {
            try {
                REGEX_RULES.push({
                    re: new RegExp(data.regex_rules[i].pattern),
                    rep: data.regex_rules[i].replacement
                });
            } catch (e) {}
        }
    }
    var EXEMPTIONS = data.exemptions || [];

    // Always update global store on new data injection
    window.__ANTIGRAVITY_EXACT__ = Object.assign(window.__ANTIGRAVITY_EXACT__ || {}, EXACT);
    window.__ANTIGRAVITY_REVERSE_MAP__ = Object.assign(window.__ANTIGRAVITY_REVERSE_MAP__ || {}, REVERSE_MAP);
    window.__ANTIGRAVITY_REGEX_RULES__ = REGEX_RULES;
    window.__ANTIGRAVITY_EXEMPTIONS__ = EXEMPTIONS;

    // Build multi-candidate REVERSE_INDEX (zh -> [en1, en2, ...]) so controlled components
    // (Base UI / Radix Select & ToggleGroup) can test which English key exists in their specific Map instance
    var reverseIndex = {};
    var addReverseCandidate = function (zh, en) {
        if (!zh || !en || zh === en) return;
        if (!reverseIndex[zh]) {
            reverseIndex[zh] = [en];
        } else if (reverseIndex[zh].indexOf(en) === -1) {
            reverseIndex[zh].push(en);
        }
    };
    var mergedRev = window.__ANTIGRAVITY_REVERSE_MAP__;
    for (var zhKey in mergedRev) {
        if (Object.prototype.hasOwnProperty.call(mergedRev, zhKey)) {
            addReverseCandidate(zhKey, mergedRev[zhKey]);
        }
    }
    var mergedExact = window.__ANTIGRAVITY_EXACT__;
    for (var enKey in mergedExact) {
        if (Object.prototype.hasOwnProperty.call(mergedExact, enKey)) {
            addReverseCandidate(mergedExact[enKey], enKey);
        }
    }
    window.__ANTIGRAVITY_REVERSE_INDEX__ = reverseIndex;

    if (window.__antigravity_i18n_runner_v3_active) {
        if (typeof window.__antigravity_translateWholePage === "function") {
            window.__antigravity_translateWholePage();
        }
        return;
    }
    window.__antigravity_i18n_runner_active = true;
    window.__antigravity_i18n_runner_v3_active = true;

    // 1. Controlled Component Multi-Candidate Reverse Map Hook (Protects Base UI / Radix Select & ToggleGroup states)
    if (!window.__antigravity_map_v3_hooked) {
        window.__antigravity_map_hooked = true;
        window.__antigravity_map_v3_hooked = true;
        var origHas = Map.prototype.has;
        var origGet = Map.prototype.get;

        Map.prototype.has = function (key) {
            if (origHas.call(this, key)) return true;
            if (typeof key === "string") {
                var idx = window.__ANTIGRAVITY_REVERSE_INDEX__;
                var candidates = idx && idx[key];
                if (candidates) {
                    for (var i = 0; i < candidates.length; i++) {
                        if (origHas.call(this, candidates[i])) return true;
                    }
                }
                var rev = window.__ANTIGRAVITY_REVERSE_MAP__;
                if (rev && rev[key] && origHas.call(this, rev[key])) {
                    return true;
                }
            }
            return false;
        };

        Map.prototype.get = function (key) {
            var val = origGet.call(this, key);
            if (val !== undefined || origHas.call(this, key)) return val;
            if (typeof key === "string") {
                var idx = window.__ANTIGRAVITY_REVERSE_INDEX__;
                var candidates = idx && idx[key];
                if (candidates) {
                    for (var i = 0; i < candidates.length; i++) {
                        if (origHas.call(this, candidates[i])) {
                            return origGet.call(this, candidates[i]);
                        }
                    }
                }
                var rev = window.__ANTIGRAVITY_REVERSE_MAP__;
                if (rev && rev[key]) {
                    return origGet.call(this, rev[key]);
                }
            }
            return undefined;
        };
    }

    // 2. Isolation & Exemption Checks
    var EXCLUDED_TAGS = {
        "SCRIPT": true,
        "STYLE": true,
        "PRE": true,
        "CODE": true,
        "TEXTAREA": true
    };

    function isInsideExcluded(node) {
        var curr = node;
        while (curr && curr !== document.body && curr !== document.documentElement) {
            if (curr.nodeType === 1) {
                var tag = curr.tagName;
                if (EXCLUDED_TAGS[tag]) return true;
                if (curr.isContentEditable) return true;
                var cls = curr.className;
                if (typeof cls === "string" && (
                    cls.indexOf("monaco-editor") !== -1 ||
                    cls.indexOf("xterm") !== -1
                )) {
                    return true;
                }
            }
            curr = curr.parentNode;
        }
        return false;
    }

    function isExempt(text) {
        var exemptions = window.__ANTIGRAVITY_EXEMPTIONS__ || EXEMPTIONS;
        for (var i = 0; i < exemptions.length; i++) {
            if (text.indexOf(exemptions[i]) !== -1) {
                return true;
            }
        }
        return false;
    }

    function getTranslatedText(original) {
        if (typeof original !== "string") return null;
        var trimmed = original.trim();
        if (!trimmed) return null;
        if (isExempt(original)) return null;

        var exactMap = window.__ANTIGRAVITY_EXACT__ || EXACT;
        var regexList = window.__ANTIGRAVITY_REGEX_RULES__ || REGEX_RULES;

        // Exact match
        if (exactMap[trimmed]) {
            var target = exactMap[trimmed];
            var leading = original.match(/^\s*/)[0];
            var trailing = original.match(/\s*$/)[0];
            return leading + target + trailing;
        }

        // Regex dynamic rules
        for (var i = 0; i < regexList.length; i++) {
            if (regexList[i].re.test(trimmed)) {
                var replaced = trimmed.replace(regexList[i].re, regexList[i].rep);
                var lead = original.match(/^\s*/)[0];
                var trail = original.match(/\s*$/)[0];
                return lead + replaced + trail;
            }
        }

        return null;
    }
    window.__antigravity_getTranslatedText = getTranslatedText;

    // 3. Transient Native Context Menu Hook (translates preload.js showContextMenu items during 120ms click window)
    if (!window.__antigravity_menu_hooked) {
        window.__antigravity_menu_hooked = true;
        var origArrayMap = Array.prototype.map;
        var mapHookTimer = null;

        var translateMenuItemsRecursive = function (items) {
            if (!Array.isArray(items)) return;
            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                if (item && typeof item === "object") {
                    if (typeof item.label === "string" && item.label) {
                        var tLabel = getTranslatedText(item.label);
                        if (tLabel !== null) {
                            item.label = tLabel;
                        }
                    }
                    if (Array.isArray(item.submenu)) {
                        translateMenuItemsRecursive(item.submenu);
                    }
                }
            }
        };

        var patchedMenuMap = function (fn, thisArg) {
            var res = origArrayMap.call(this, fn, thisArg);
            if (this.length > 0 && res.length === this.length) {
                var first = res[0];
                if (first && typeof first === "object" && ("label" in first || first.type === "separator")) {
                    translateMenuItemsRecursive(res);
                }
            }
            return res;
        };

        var enableTempMenuMapHook = function () {
            Array.prototype.map = patchedMenuMap;
            if (mapHookTimer) clearTimeout(mapHookTimer);
            mapHookTimer = setTimeout(function () {
                Array.prototype.map = origArrayMap;
                mapHookTimer = null;
            }, 120);
        };

        window.addEventListener("contextmenu", enableTempMenuMapHook, true);
        window.addEventListener("pointerdown", enableTempMenuMapHook, true);
        window.addEventListener("mousedown", enableTempMenuMapHook, true);
    }

    // 4. Node Translation Engine (Pure value matching, no harmful WeakSet blocking)
    function translateTextNode(textNode) {
        if (!textNode || textNode.nodeType !== 3) return;
        var val = textNode.nodeValue;
        if (!val || !val.trim()) return;

        if (isInsideExcluded(textNode)) return;

        var translated = getTranslatedText(val);
        if (translated !== null && translated !== val) {
            textNode.nodeValue = translated;
        }
    }

    function translateElementAttributes(el) {
        if (!el || el.nodeType !== 1) return;
        if (EXCLUDED_TAGS[el.tagName]) return;

        var attrs = ["placeholder", "title", "aria-label", "alt"];
        for (var i = 0; i < attrs.length; i++) {
            var attr = attrs[i];
            if (el.hasAttribute(attr)) {
                var val = el.getAttribute(attr);
                var tVal = getTranslatedText(val);
                if (tVal !== null && tVal !== val) {
                    el.setAttribute(attr, tVal);
                }
            }
        }
    }

    function translateSubtree(root) {
        if (!root) return;
        if (root.nodeType === 3) {
            translateTextNode(root);
            return;
        }
        if (root.nodeType === 1) {
            if (isInsideExcluded(root)) return;
            translateElementAttributes(root);
            var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
            var node;
            while ((node = walker.nextNode())) {
                translateTextNode(node);
            }
            var elementsWithAttrs = root.querySelectorAll("[placeholder], [title], [aria-label], [alt]");
            for (var i = 0; i < elementsWithAttrs.length; i++) {
                translateElementAttributes(elementsWithAttrs[i]);
            }
        }
    }

    // 5. Initial Full Page Translation & Lifecycle Hooks
    function translateWholePage() {
        var target = document.body || document.documentElement;
        if (target) {
            translateSubtree(target);
        }
    }
    window.__antigravity_translateWholePage = translateWholePage;

    translateWholePage();

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", translateWholePage);
    }
    window.addEventListener("load", translateWholePage);

    // SPA client-side routing & interaction triggers
    window.addEventListener("popstate", function () { setTimeout(translateWholePage, 50); });
    window.addEventListener("hashchange", function () { setTimeout(translateWholePage, 50); });
    window.addEventListener("click", function () { setTimeout(translateWholePage, 60); }, true);

    // Multi-turn progressive scans for React initial async rendering
    var scanDelays = [100, 250, 500, 1000, 1800, 3000, 5000];
    for (var k = 0; k < scanDelays.length; k++) {
        setTimeout(translateWholePage, scanDelays[k]);
    }

    // 6. High-Performance MutationObserver (observes childList on documentElement)
    var isTranslating = false;
    var observer = new MutationObserver(function (mutations) {
        if (isTranslating) return;
        isTranslating = true;
        try {
            for (var i = 0; i < mutations.length; i++) {
                var m = mutations[i];
                if (m.type === "childList") {
                    for (var j = 0; j < m.addedNodes.length; j++) {
                        translateSubtree(m.addedNodes[j]);
                    }
                }
            }
        } finally {
            isTranslating = false;
        }
    });

    function startObserving() {
        var root = document.documentElement || document.body;
        if (root) {
            observer.observe(root, {
                childList: true,
                subtree: true
            });
        } else {
            setTimeout(startObserving, 30);
        }
    }
    startObserving();

    console.log("[Antigravity i18n] Localization runner v3.0 successfully initialized and active.");
})();
