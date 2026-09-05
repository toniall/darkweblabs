// Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
/*
 * darkweb-clipboard — automatic clipboard sync for the lab desktop.
 *
 * noVNC ships a clipboard *panel*: an explicit box you paste into and copy out
 * of. That is a browser security boundary, not a noVNC shortcoming — a page
 * cannot silently read your system clipboard, because a page that could would
 * be able to steal whatever you last copied.
 *
 * This restores automatic sync where the browser permits it, and falls back
 * cleanly where it does not.
 *
 * Three paths, in decreasing order of seamlessness:
 *
 *   1. Automatic read on focus. Needs the `clipboard-read` permission, which
 *      Chrome grants after a single prompt. Firefox has no such permission and
 *      never will — a deliberate decision by Mozilla, not an omission.
 *
 *   2. Ctrl+Shift+V. A real paste gesture hands the clipboard over with no
 *      permission at all, in every browser — but only if the gesture has
 *      somewhere to land. A <canvas> is not editable, so Firefox fires no
 *      paste event on it. We keep an invisible textarea and hand it focus for
 *      one tick so the event has a target. Ctrl+V is left alone: noVNC
 *      forwards it to the remote session, which is where it belongs.
 *
 *   3. Automatic write on remote copy. navigator.clipboard.writeText() needs
 *      only a secure context, which https://127.0.0.1 satisfies.
 *
 * Requires window.UI. noVNC's app/ui.js is an ES module that exports the UI
 * singleton without ever attaching it to window, so the image appends
 * `window.UI = UI;` to that file at build time. Without it every path here is
 * dead code that fails silently.
 *
 * Set window.DARKWEB_CLIPBOARD_AUTO = false before this loads to keep the
 * explicit panel behaviour.
 */
(function () {
  'use strict';

  var AUTO = window.DARKWEB_CLIPBOARD_AUTO !== false;
  var lastSent = null;
  var lastRecv = null;

  var XK_Control_L = 0xffe3;
  var XK_v = 0x76;

  // How long to wait after setting the remote clipboard before replaying the
  // keystroke. vncconfig has to claim ownership of the CLIPBOARD selection
  // before the guest application asks who owns it. Raise this if pastes land
  // empty or stale on a slow link.
  var PASTE_DELAY_MS = 80;

  function log(msg) {
    if (window.console) console.log('[darkweb-clipboard] ' + msg);
  }

  function rfb() {
    return (window.UI && window.UI.rfb) || window.rfb || null;
  }

  function sendToRemote(text) {
    var c = rfb();
    if (!c || typeof text !== 'string' || text === lastSent) return false;
    lastSent = text;
    try {
      c.clipboardPasteFrom(text);
      return true;
    } catch (e) {
      log('could not send to remote: ' + e);
      return false;
    }
  }

  // Replay a plain Ctrl+V into the session so the focused application actually
  // pastes. GUI applications — Tor Browser, Firefox, the text editor — all take
  // Ctrl+V. A terminal does not; there, middle-click uses PRIMARY, which
  // autocutsel keeps in step with CLIPBOARD.
  function replayPaste() {
    var c = rfb();
    if (!c) return;
    setTimeout(function () {
      try {
        c.focus();
        c.sendKey(XK_Control_L, 'ControlLeft', true);
        c.sendKey(XK_v, 'KeyV', true);
        c.sendKey(XK_v, 'KeyV', false);
        c.sendKey(XK_Control_L, 'ControlLeft', false);
      } catch (e) {
        log('could not replay paste: ' + e);
      }
    }, PASTE_DELAY_MS);
  }

  /* ---- the paste target -------------------------------------------------- */
  // A canvas cannot receive a paste event. This can. It holds focus for one
  // tick, catches the event, and hands focus straight back.

  var sink = document.createElement('textarea');
  sink.setAttribute('aria-hidden', 'true');
  sink.setAttribute('tabindex', '-1');
  sink.style.cssText =
    'position:fixed;top:0;left:0;width:1px;height:1px;' +
    'opacity:0;border:0;padding:0;margin:0;z-index:-1;';

  function attachSink() {
    if (document.body && !sink.parentNode) document.body.appendChild(sink);
  }
  if (document.body) attachSink();
  else document.addEventListener('DOMContentLoaded', attachSink);

  var returnFocusTo = null;

  function isEditable(el) {
    return !!(el && el.closest &&
              el.closest('input, textarea, [contenteditable]'));
  }

  /* ---- 2. Ctrl+Shift+V: works everywhere, needs no permission ------------ */

  document.addEventListener('keydown', function (e) {
    if (!e.ctrlKey || !e.shiftKey) return;
    if (String(e.key).toLowerCase() !== 'v') return;
    if (e.target === sink || isEditable(e.target)) return;

    // Do NOT preventDefault here — that would suppress the very paste event
    // we are trying to provoke. Stopping propagation is enough to keep noVNC
    // from forwarding the combination to the remote session.
    e.stopPropagation();

    attachSink();
    returnFocusTo = document.activeElement;
    sink.value = '';
    sink.focus();
  }, true);

  document.addEventListener('keyup', function (e) {
    if (e.target === sink) e.stopPropagation();
  }, true);

  sink.addEventListener('paste', function (e) {
    var text = e.clipboardData && e.clipboardData.getData('text');
    e.preventDefault();
    if (text && sendToRemote(text)) {
      log('sent ' + text.length + ' chars via paste gesture');
      replayPaste();
    }
    if (returnFocusTo && returnFocusTo.focus) returnFocusTo.focus();
    returnFocusTo = null;
  });

  // Chrome delivers paste to the document even with no editable focus. Harmless
  // to keep as a second route; the dedupe on lastSent stops a double send.
  document.addEventListener('paste', function (e) {
    if (e.target === sink) return;
    var text = e.clipboardData && e.clipboardData.getData('text');
    if (text && sendToRemote(text)) {
      log('sent ' + text.length + ' chars via document paste');
    }
  });

  /* ---- 3. remote copy -> host clipboard ---------------------------------- */
  // writeText() needs transient user activation in Firefox. The Ctrl+C or the
  // mouse selection that caused the copy grants roughly five seconds, and
  // ServerCutText normally lands well inside that window.

  function hookOutbound() {
    var c = rfb();
    if (!c || c._darkwebHooked) return;
    c._darkwebHooked = true;

    c.addEventListener('clipboard', function (ev) {
      var text = ev.detail && ev.detail.text;
      if (!text || text === lastRecv) return;
      lastRecv = text;

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(function (err) {
          log('writeText refused (' + err + ') — falling back');
          legacyCopy(text);
        });
      } else {
        legacyCopy(text);
      }
    });
    log('outbound hook attached');
  }

  function legacyCopy(text) {
    attachSink();
    var prev = document.activeElement;
    sink.value = text;
    sink.focus();
    sink.select();
    try {
      document.execCommand('copy');
    } catch (err) {
      log('host copy blocked — use the panel');
    }
    if (prev && prev.focus) prev.focus();
  }

  /* ---- 1. automatic inbound sync, where the browser allows it ------------ */

  function pollHostClipboard() {
    if (!AUTO) return;
    if (!navigator.clipboard || !navigator.clipboard.readText) return;
    if (!document.hasFocus()) return;

    navigator.clipboard.readText()
      .then(sendToRemote)
      .catch(function () {
        /* Firefox lands here every time: no clipboard-read permission exists.
           Silent by design — Ctrl+Shift+V and the panel both still work. */
      });
  }

  function start() {
    hookOutbound();
    if (AUTO && navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: 'clipboard-read' })
        .then(function (status) {
          log('clipboard-read permission: ' + status.state);
          if (status.state !== 'denied') {
            window.addEventListener('focus', pollHostClipboard);
            setInterval(pollHostClipboard, 1000);
          }
        })
        .catch(function () {
          log('clipboard-read unavailable — Ctrl+Shift+V still works');
        });
    }
  }

  // The RFB object appears only once a session is connected.
  var tries = 0;
  var wait = setInterval(function () {
    if (rfb()) {
      clearInterval(wait);
      start();
    } else if (++tries > 120) {
      clearInterval(wait);
      log('gave up waiting for UI.rfb — is window.UI exposed in app/ui.js?');
    }
  }, 500);
})();
