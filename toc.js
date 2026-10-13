/* On-this-page contents: highlights the section in view and pins a clicked item until the
   reader scrolls by hand. Expects a <nav class="toc"> whose links point at element ids. */
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var targets = links.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  var ticking = false;
  var pinned = -1;                       // set by a click, cleared when the reader scrolls by hand

  function mark(cur) {
    links.forEach(function (a, i) {
      a.classList.toggle('is-active', i === cur);
      if (i === cur) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
  }
  function update() {
    ticking = false;
    if (pinned >= 0) { mark(pinned); return; }
    var cur = 0;
    targets.forEach(function (t, i) {
      if (t && t.getBoundingClientRect().top <= 120) cur = i;
    });
    /* At the very bottom, the last section wins. */
    if (window.innerHeight + window.pageYOffset >= document.documentElement.scrollHeight - 4) cur = links.length - 1;
    mark(cur);
  }
  /* A short timer rather than requestAnimationFrame: rAF is paused while a page is hidden, and a
     lost callback would leave `ticking` true for good, so scrolling would stop updating the list. */
  function schedule() {
    if (!ticking) { ticking = true; setTimeout(update, 40); }
  }

  /* Service and Skills are short, so the page cannot always scroll far enough to put
     the clicked section at the top and the bottom rule would hand the highlight to the
     last item. Keep the clicked item lit until the reader scrolls on their own. */
  links.forEach(function (a, i) {
    a.addEventListener('click', function () { pinned = i; mark(i); });
  });
  ['wheel', 'touchmove'].forEach(function (ev) {
    window.addEventListener(ev, function () { pinned = -1; }, { passive: true });
  });
  window.addEventListener('keydown', function (e) {
    if (/^(ArrowUp|ArrowDown|PageUp|PageDown|Home|End| )$/.test(e.key)) pinned = -1;
  });

  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  update();
})();
