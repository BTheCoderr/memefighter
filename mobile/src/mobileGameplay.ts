/**
 * Minimal native WebView presentation layer around the single source of truth:
 * root index.html. No gameplay, ratings, online protocol, or fighter rules are
 * reimplemented in the shell.
 */
export const MOBILE_GAME_CSS = `
  :root { color-scheme:dark; }
  html,body { overscroll-behavior:none; }
  .shell { max-width:none!important; }
  /* Landscape matches have limited vertical space on modern iPhones. */
  @media (orientation:landscape) {
    html,body { height:100%; overflow:hidden!important; }
    .shell { padding:3px 5px!important; margin:0!important; }
    .topbar, .foot { display:none!important; }
    .arena-wrap {
      height:calc(100dvh - 74px)!important;
      min-height:0!important;
      overflow:hidden!important;
      border-radius:11px!important;
    }
    .arena-clip { height:100%!important; }
    .arena {
      width:100%!important;
      height:100%!important;
      aspect-ratio:auto!important;
      object-fit:fill!important;
    }
    .screen {
      height:100%!important;
      overflow-y:auto!important;
      -webkit-overflow-scrolling:touch;
      padding:6px 10px!important;
      align-items:flex-start!important;
    }
    .panel { max-width:980px!important; margin:auto!important; }
    .panel h1 { font-size:clamp(22px,4vw,36px)!important; }
    .panel p { margin:4px auto 5px!important; font-size:11px!important; }
    .selector { grid-template-columns:1fr 1fr!important; margin:6px 0!important; }
    .settings { margin:6px 0!important; }
    .controls { margin:3px 0 0!important; gap:0!important; }
    .controls .tip, .controls .keys { display:none!important; }
    .mobile {
      display:grid!important;
      grid-template-columns:1.15fr 1.65fr!important;
      gap:7px!important;
      margin:4px 0 0!important;
      align-items:center!important;
    }
    .pad,.moves { display:flex!important; flex-wrap:nowrap!important; gap:6px!important; }
    .touch-btn { min-height:53px!important; padding:4px!important; font-size:12px!important; touch-action:none; }
    .screen:has(#start) { padding-bottom:5px!important; }
  }
`;

export function makeArcadeHtml(source: string, offline: boolean): string {
  if (!source.includes("</head>") || !source.includes('id="game"')) {
    throw new Error("The arcade HTML is missing its head or game canvas");
  }
  const offlineRule = offline ? ".online-box{display:none!important}" : "";
  return source.replace("</head>", "<style>" + MOBILE_GAME_CSS + offlineRule + "</style></head>");
}

/** Executed only after a game document loads, not as an arbitrary injected website script. */
export function makeBridgeScript(createOnlineRoom: boolean): string {
  return [
    "(function(){",
    "if(window.__memeFighterNativeBridge)return;",
    "window.__memeFighterNativeBridge=true;",
    "var st=document.createElement('style');",
    "st.textContent=" + JSON.stringify(MOBILE_GAME_CSS) + ";document.head.appendChild(st);",
    "function post(type,code){try{window.ReactNativeWebView.postMessage(JSON.stringify({type:type,code:code}));}catch(e){}}",
    "document.addEventListener('pointerdown',function(e){if(e.target.closest('.touch-btn'))post('touch');},{passive:true});",
    "var local=document.getElementById('mode');",
    "if(local&&location.protocol!=='https:'){var opt=local.querySelector('option[value=local]');if(opt)opt.remove();}",
    "var codeEl=document.getElementById('room-code');",
    "if(codeEl){var notify=function(){var c=codeEl.textContent.trim().toUpperCase();if(/^[A-HJ-NP-Z2-9]{6}$/.test(c))post('room',c);};",
    "new MutationObserver(notify).observe(codeEl,{childList:true,characterData:true,subtree:true});notify();}",
    "var copy=document.getElementById('copy-room');",
    "if(copy)copy.addEventListener('click',function(e){",
    "var c=codeEl&&codeEl.textContent.trim().toUpperCase();",
    "if(/^[A-HJ-NP-Z2-9]{6}$/.test(c)){e.preventDefault();e.stopImmediatePropagation();post('invite',c);}",
    "},true);",
    "var result=document.getElementById('result');",
    "if(result)new MutationObserver(function(){if(!result.hidden)post('finished');}).observe(result,{attributes:true,attributeFilter:['hidden']});",
    createOnlineRoom
      ? "var create=document.getElementById('create-room');if(create)create.click();"
      : "",
    "})();true;"
  ].join("");
}
