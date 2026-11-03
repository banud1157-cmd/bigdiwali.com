document.addEventListener("DOMContentLoaded", () => {
  const timer = document.getElementById("timer");
  if (!timer) return;
  let remaining = Number(timer.dataset.seconds || 300);
  const label = document.getElementById("timer-status");
  const tick = () => {
    const m = String(Math.floor(remaining / 60)).padStart(2, "0");
    const s = String(remaining % 60).padStart(2, "0");
    timer.textContent = `${m}:${s}`;
    if (remaining <= 0) {
      label.textContent = "Demo timer ended. You can still test the simulation controls.";
      timer.classList.add("expired");
      return;
    }
    remaining -= 1;
    setTimeout(tick, 1000);
  };
  tick();
});
function copyReferral() {
  const code = document.getElementById("refcode").textContent.trim();
  if (navigator.clipboard) {
    navigator.clipboard.writeText(code).then(() => alert("Demo referral code copied!"));
  } else {
    alert("Your  referral code: " + code);
  }
}
