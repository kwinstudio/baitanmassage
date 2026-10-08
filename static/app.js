/* Baitan Thai Massage — kleine, afhankelijkheidsvrije interacties */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const mqDesktop = window.matchMedia('(min-width: 1081px)');

  /* Header-rand bij scrollen + mobiele contactbalk */
  const header = $('[data-header]');
  const bar = $('[data-mobile-bar]');
  const footerEl = $('.site-footer');
  let footerVisible = false;
  if (footerEl && 'IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => { footerVisible = e.isIntersecting; onScroll(); }).observe(footerEl);
  }
  function onScroll() {
    const y = window.scrollY;
    header?.classList.toggle('is-scrolled', y > 8);
    bar?.classList.toggle('is-visible', y > 480 && !footerVisible);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobiel menu */
  const toggle = $('[data-menu-toggle]');
  const list = $('#nav-list');
  if (toggle && list) {
    const setOpen = (open) => {
      list.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.querySelector('.sr-only').textContent = open ? 'Menu sluiten' : 'Menu';
    };
    toggle.addEventListener('click', () => setOpen(!list.classList.contains('is-open')));
    list.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && list.classList.contains('is-open')) { setOpen(false); toggle.focus(); }
    });
    document.addEventListener('click', (e) => {
      if (list.classList.contains('is-open') && !list.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
    });
    mqDesktop.addEventListener?.('change', (e) => { if (e.matches) setOpen(false); });
  }

  /* Google Maps pas laden na toestemming */
  $$('[data-load-map]').forEach((btn) => btn.addEventListener('click', () => {
    const shell = btn.closest('[data-map]');
    if (!shell) return;
    const iframe = document.createElement('iframe');
    iframe.className = 'map-frame';
    iframe.title = 'Kaart: Baitan Thai Massage, Hollandsch Diep 71–73, Capelle aan den IJssel';
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'no-referrer-when-downgrade';
    iframe.src = shell.dataset.map;
    shell.replaceWith(iframe);
  }));

  /* Massagekeuze: vijf vragen, één advies */
  const quiz = $('[data-quiz]');
  if (quiz) {
    const data = JSON.parse(quiz.dataset.quiz);
    const steps = $$('.quiz-step', quiz);
    const label = $('[data-quiz-label]', quiz);
    const barEl = $('[data-quiz-bar]', quiz);
    const result = $('[data-quiz-result]', quiz);
    const progress = $('.quiz-progress', quiz);
    const ids = ['thai', 'aroma', 'sport', 'hotstone', 'duo'];
    let scores;

    const show = (i) => {
      steps.forEach((s, n) => { s.hidden = n !== i; });
      label.textContent = `Vraag ${i + 1} van ${steps.length}`;
      barEl.style.transform = `scaleX(${(i + 1) / steps.length})`;
    };
    const reset = () => {
      scores = Object.fromEntries(ids.map((id) => [id, 0]));
      result.hidden = true;
      progress.hidden = false;
      show(0);
    };
    const finish = () => {
      steps.forEach((s) => { s.hidden = true; });
      progress.hidden = true;
      // Bij gelijke stand wint de eerste in de lijst (Thaise massage)
      const best = ids.reduce((a, b) => (scores[b] > scores[a] ? b : a), ids[0]);
      const t = data[best];
      $('[data-quiz-title]', quiz).textContent = t.name;
      $('[data-quiz-text]', quiz).textContent = t.text;
      $('[data-quiz-link]', quiz).href = t.url;
      result.hidden = false;
      result.focus({ preventScroll: true });
      if (!mqDesktop.matches) result.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    steps.forEach((step, i) => {
      $$('.quiz-option', step).forEach((btn) => btn.addEventListener('click', () => {
        const s = btn.dataset.score;
        if (s === 'neutral') ids.forEach((id) => { scores[id] += 0.25; });
        else if (s in scores) scores[s] += 2;
        if (i === steps.length - 1) finish();
        else { show(i + 1); $('.quiz-option', steps[i + 1])?.focus({ preventScroll: true }); }
      }));
    });
    $('[data-quiz-restart]', quiz)?.addEventListener('click', () => {
      reset();
      $('.quiz-option', steps[0])?.focus({ preventScroll: true });
    });
    reset();
  }
})();
