// Start-up: runs last, once every other script has defined its parts.

applyMode(true);
measureHeader();
// the initially selected buttons start fully painted (measured once the counts are filled in)
[...segButtons, ...chips].forEach(b => setFillOrigin(b, null));
idle(prepareSpark, { timeout: 1500 });
save();
route();
// keep downloaded artwork on this device (sw.js); service workers only run on websites, not file:// copies
if ("serviceWorker" in navigator && window.isSecureContext && location.protocol !== "file:")
  navigator.serviceWorker.register("sw.js").catch(() => {});
