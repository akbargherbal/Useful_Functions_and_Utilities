(function () {
  const SCOPE = "colab-composer";

  const shadowCSS = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* 1. Global Panel Background (Deep Obsidian Black) */
    :host, 
    .conversation-container, 
    .main-container, 
    .composer-container, 
    colab-composer-conversation, 
    .chat-area, 
    .scrollable {
      background-color: #08090a !important;
    }

    /* Override host background for dropdowns, menus, and popovers */
    :host(colab-composer-autocomplete),
    :host(colab-composer-input-tune-menu),
    :host(colab-composer-model-selector) {
      background-color: #121316 !important;
      border: 1px solid #202226 !important;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
    }

    /* Ensure text inside all dropdowns, menus, and options is bright and readable */
    colab-composer-autocomplete *:not(button):not(a),
    colab-composer-input-tune-menu *:not(button):not(a),
    colab-composer-model-selector *:not(button):not(a) {
      color: #e4e6eb !important;
    }

    /* Hover and selection highlights inside menus */
    [role="menuitem"]:hover,
    [role="option"]:hover,
    .menu-item:hover,
    .option:hover,
    mwc-list-item:hover {
      background-color: rgba(86, 242, 195, 0.1) !important;
      color: #56f2c3 !important;
    }

    /* Hide ONLY the disclaimer legal notice */
    .legal-notice,
    div.legal-notice {
      display: none !important;
    }

    /* 2. Scaled Cyberpunk Scrollbars (6px for 27" screens) */
    .scrollable::-webkit-scrollbar,
    ::-webkit-scrollbar { 
      width: 6px !important; 
      height: 6px !important; 
    }
    .scrollable::-webkit-scrollbar-track,
    ::-webkit-scrollbar-track { 
      background: transparent !important; 
    }
    .scrollable::-webkit-scrollbar-thumb,
    ::-webkit-scrollbar-thumb { 
      background-color: rgba(86, 242, 195, 0.15) !important;
      border-radius: 0px !important; 
    }
    .scrollable::-webkit-scrollbar-thumb:hover,
    ::-webkit-scrollbar-thumb:hover { 
      background-color: #56f2c3 !important; 
    }
    * { 
      scrollbar-width: thin !important;
      scrollbar-color: rgba(86, 242, 195, 0.15) transparent !important; 
    }

    /* 3. Global Selection Color */
    ::selection {
      background-color: rgba(86, 242, 195, 0.2) !important;
      color: #ffffff !important;
    }

    /* 4. Desktop-Scaled Typography (Excludes UI Vectors/Icons) */
    p, li, .message-content, .text-content {
      font-family: "Space Grotesk", "Inter", system-ui, -apple-system, sans-serif !important;
    }
    div:not([class*="icon"]):not([class*="material"]):not([class*="sym"]):not([style*="icon"]),
    span:not([class*="icon"]):not([class*="material"]):not([class*="sym"]):not([style*="icon"]) {
      font-family: "Space Grotesk", "Inter", system-ui, -apple-system, sans-serif !important;
    }

    /* Scaled Paragraph & List Treatment */
    p { 
      font-size: 17px !important; 
      line-height: 1.85 !important;
      letter-spacing: 0.1px !important; 
      color: #e4e6eb !important;
      margin-top: 10px !important; 
      margin-bottom: 20px !important; 
    }
    ul, ol { 
      padding-left: 24px !important; 
      margin-bottom: 20px !important; 
    }
    li { 
      font-size: 17px !important; 
      line-height: 1.85 !important;
      color: #e4e6eb !important; 
      margin-bottom: 10px !important; 
    }

    /* User Message Styling (Sleek Console Style) */
    colab-composer-message[user] p,
    colab-composer-message[user] span,
    .user-message p,
    .user-message span {
      font-family: "JetBrains Mono", monospace !important;
      font-size: 17px !important;
      color: #56f2c3 !important;
    }

    /* Clean Dividers Between Messages */
    colab-composer-message {
      border-bottom: 1px solid #1a1c1e !important;
      padding: 20px 0 !important;
    }

    /* 5. Highly Legible Code Display */
    code { 
      font-family: "JetBrains Mono", "Fira Code", monospace !important;
      font-size: 15px !important; 
      font-weight: 600 !important;
      background-color: rgba(86, 242, 195, 0.07) !important;
      border: 1px solid rgba(86, 242, 195, 0.25) !important;
      border-radius: 4px !important; 
      padding: 2px 6px !important;
      color: #7bfce0 !important; 
      word-break: break-word !important;
    }

    pre { 
      font-family: "JetBrains Mono", "Fira Code", monospace !important;
      font-size: 15px !important; 
      line-height: 1.65 !important;
      background-color: #030304 !important;
      border: 1px solid rgba(255, 255, 255, 0.03) !important;
      border-left: 3px solid #56f2c3 !important;
      border-radius: 4px !important; 
      padding: 18px !important;
      margin: 22px 0 !important; 
      overflow-x: auto !important;
      box-shadow: 0 0 20px rgba(86, 242, 195, 0.04) !important;
    }

    /* 6. Easily-Clickable Suggestion Chips */
    colab-composer-suggestion-chips button,
    colab-composer-suggestion-chips [role="button"],
    .suggestion-chip {
      background-color: rgba(86, 242, 195, 0.02) !important;
      border: 1px solid rgba(86, 242, 195, 0.2) !important;
      color: #7bfce0 !important;
      border-radius: 4px !important;
      padding: 8px 16px !important; 
      font-family: "Space Grotesk", "JetBrains Mono", monospace !important;
      font-size: 14px !important;
      font-weight: 500 !important;
      transition: all 0.2s ease-in-out !important;
      cursor: pointer !important;
      box-shadow: none !important;
      margin: 6px !important;
      text-align: left !important;
      line-height: 1.4 !important;
    }
    colab-composer-suggestion-chips button:hover,
    colab-composer-suggestion-chips [role="button"]:hover,
    .suggestion-chip:hover {
      background-color: rgba(86, 242, 195, 0.08) !important;
      border-color: #56f2c3 !important;
      color: #ffffff !important;
      transform: translateX(2px) !important;
    }

    /* 7. Input Terminal Area */
    colab-composer-input {
      background-color: #0b0c0e !important;
      border-top: 1px solid #1a1c1e !important;
    }
    colab-composer-rich-text-field {
      font-family: "JetBrains Mono", monospace !important;
      font-size: 16px !important;
      color: #e4e6eb !important;
    }
  `;

  const S = SCOPE;
  const lightCSS = `
    ${S} {
      background-color: #08090a !important;
    }
  `;

  // ── Toggle state ──────────────────────────────────────────────────────────
  let themeEnabled = true;
  let trackedHeaders = new Set();

  // Search up the DOM / Shadow DOM paths from the element to find the parent tab-pane-header
  function findAndHideParentHeader(composer) {
    let current = composer;
    while (current) {
      if (current.querySelector) {
        const header = current.querySelector(".tab-pane-header");
        if (header && header.textContent.includes("Gemini")) {
          header.style.setProperty("display", "none", "important");
          trackedHeaders.add(header);
          return;
        }
      }
      // Climes up parent elements or escapes shadow host barriers
      current = current.parentNode || current.host;
    }
  }

  function injectStylesDeep(node) {
    if (!node) return;

    if (node.shadowRoot) {
      let style = node.shadowRoot.getElementById("colab-gemini-shadow-theme");
      if (!style) {
        style = document.createElement("style");
        style.id = "colab-gemini-shadow-theme";
        node.shadowRoot.appendChild(style);
      }
      if (style.textContent !== shadowCSS) {
        style.textContent = shadowCSS;
      }
      injectStylesDeep(node.shadowRoot);
    }

    // Surgical inline overrides
    if (node.nodeType === Node.ELEMENT_NODE) {
      const tagName = node.tagName.toLowerCase();

      if (tagName === "div" && node.classList.contains("scrollable")) {
        node.style.setProperty("padding-top", "4px", "important");
        node.style.setProperty("padding-bottom", "4px", "important");
      }
      if (tagName === "h2" && node.classList.contains("greeting")) {
        node.style.setProperty("margin-top", "4px", "important");
        node.style.setProperty("margin-bottom", "6px", "important");
      }
      if (tagName === "span" && node.classList.contains("sub-greeting")) {
        node.style.setProperty("margin-bottom", "12px", "important");
      }
      if (tagName === "div" && node.classList.contains("footer")) {
        node.style.setProperty("margin-bottom", "0px", "important");
      }
      if (tagName === "colab-composer-input") {
        node.style.setProperty("padding", "6px 14px", "important");
      }
      if (
        tagName === "div" &&
        node.classList.contains("colab-monaco-wrapper")
      ) {
        node.style.setProperty("padding", "4px 8px", "important");
      }
    }

    if (node.children) {
      for (const child of node.children) {
        injectStylesDeep(child);
      }
    }
  }

  function removeStylesDeep(node) {
    if (!node) return;

    if (node.shadowRoot) {
      const style = node.shadowRoot.getElementById("colab-gemini-shadow-theme");
      if (style) style.textContent = "";
      removeStylesDeep(node.shadowRoot);
    }

    if (node.children) {
      for (const child of node.children) {
        removeStylesDeep(child);
      }
    }
  }

  function removeInlineStylesDeep(node) {
    if (!node) return;

    if (node.shadowRoot) {
      removeInlineStylesDeep(node.shadowRoot);
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
      const tagName = node.tagName.toLowerCase();

      if (tagName === "div" && node.classList.contains("scrollable")) {
        node.style.removeProperty("padding-top");
        node.style.removeProperty("padding-bottom");
      }
      if (tagName === "h2" && node.classList.contains("greeting")) {
        node.style.removeProperty("margin-top");
        node.style.removeProperty("margin-bottom");
      }
      if (tagName === "span" && node.classList.contains("sub-greeting")) {
        node.style.removeProperty("margin-bottom");
      }
      if (tagName === "div" && node.classList.contains("footer")) {
        node.style.removeProperty("margin-bottom");
      }
      if (tagName === "colab-composer-input") {
        node.style.removeProperty("padding");
      }
      if (
        tagName === "div" &&
        node.classList.contains("colab-monaco-wrapper")
      ) {
        node.style.removeProperty("padding");
      }
    }

    if (node.children) {
      for (const child of node.children) {
        removeInlineStylesDeep(child);
      }
    }
  }

  let mainStyle = document.getElementById("colab-gemini-main-theme");
  if (!mainStyle) {
    mainStyle = document.createElement("style");
    mainStyle.id = "colab-gemini-main-theme";
    document.head.appendChild(mainStyle);
  }
  mainStyle.textContent = lightCSS;

  function applyToScope() {
    const composers = document.querySelectorAll(SCOPE);
    composers.forEach(injectStylesDeep);
    composers.forEach(findAndHideParentHeader);
  }

  function removeFromScope() {
    document.querySelectorAll(SCOPE).forEach(removeStylesDeep);
    document.querySelectorAll(SCOPE).forEach(removeInlineStylesDeep);

    // Restore parent headers
    trackedHeaders.forEach((header) => {
      header.style.removeProperty("display");
    });
    trackedHeaders.clear();

    mainStyle.textContent = "";
  }

  applyToScope();

  if (window.geminiStyleTimer) clearInterval(window.geminiStyleTimer);
  window.geminiStyleTimer = setInterval(() => {
    if (themeEnabled) applyToScope();
  }, 800);

  // ── ALT+T keyboard toggle ─────────────────────────────────────────────────
  if (window.geminiStyleToggleListener) {
    document.removeEventListener("keydown", window.geminiStyleToggleListener);
  }

  window.geminiStyleToggleListener = function (e) {
    if (e.altKey && e.key === "t") {
      themeEnabled = !themeEnabled;
      if (themeEnabled) {
        mainStyle.textContent = lightCSS;
        applyToScope();
        console.log("🎨 [Alt+T] Cyberpunk theme → ON");
      } else {
        removeFromScope();
        console.log("🌑 [Alt+T] Cyberpunk theme → OFF");
      }
    }
  };

  document.addEventListener("keydown", window.geminiStyleToggleListener);

  console.log(
    "🎨 High-Resolution Cyberpunk Gemini theme applied to <" + SCOPE + ">.",
  );
  console.log("⌨️  Press Alt+T to toggle the theme on/off.");
})();
