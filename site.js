/* MrGreenlee — shared page behavior. No dependencies. */
(function () {
  'use strict';

  // Header lifts a shadow once the page scrolls.
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('scrolled', window.scrollY > 8);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Unit-chart medallion tooltips (cast-iron nameplate). Value (the No.) leads.
  var meds = document.querySelectorAll('.med[data-name]');
  if (meds.length) {
    var tip = document.createElement('div');
    tip.className = 'viz-tip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    var vtNo = document.createElement('span'); vtNo.className = 'vt-no';
    var vtMeta = document.createElement('span'); vtMeta.className = 'vt-meta';
    var vtStatus = document.createElement('span'); vtStatus.className = 'vt-status';
    tip.appendChild(vtNo); tip.appendChild(vtMeta); tip.appendChild(vtStatus);
    document.body.appendChild(tip);

    var showTip = function (el) {
      // textContent only — never innerHTML — labels are treated as untrusted.
      vtNo.textContent = el.getAttribute('data-no');
      vtMeta.textContent = el.getAttribute('data-name') + ' · ' +
        el.getAttribute('data-year') + ' · ' + el.getAttribute('data-series');
      vtStatus.textContent = el.getAttribute('data-status');
      tip.hidden = false;
      var r = el.getBoundingClientRect();
      var t = tip.getBoundingClientRect();
      var vw = document.documentElement.clientWidth;
      var left = r.left + r.width / 2 - t.width / 2 + window.scrollX;
      left = Math.max(window.scrollX + 8, Math.min(left, window.scrollX + vw - t.width - 8));
      var top = r.top + window.scrollY - t.height - 10;
      if (r.top - t.height - 10 < 0) { top = r.bottom + window.scrollY + 10; }
      tip.style.left = left + 'px';
      tip.style.top = top + 'px';
    };
    var hideTip = function () { tip.hidden = true; };

    meds.forEach(function (el) {
      el.addEventListener('pointerenter', function () { showTip(el); });
      el.addEventListener('pointerleave', hideTip);
      el.addEventListener('focus', function () { showTip(el); });
      el.addEventListener('blur', hideTip);
    });
    window.addEventListener('scroll', hideTip, { passive: true });
  }

  // Fade-up reveals; skipped entirely for reduced-motion users.
  var reveals = document.querySelectorAll('.reveal');
  if (!reveals.length) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('in'); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        io.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

  reveals.forEach(function (el) { io.observe(el); });
})();
