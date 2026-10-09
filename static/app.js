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

  /* Live openingsstatus (tijd in Nederland) */
  const statusEls = $$('[data-open-status]');
  if (statusEls.length) {
    const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Amsterdam', weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
    const get = (t) => parts.find((p) => p.type === t)?.value;
    const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(get('weekday'));
    const now = Number(get('hour')) * 60 + Number(get('minute'));
    const mins = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
    const nice = (t) => t.endsWith(':00') ? String(Number(t.split(':')[0])) : t.replace(/^0/, '');
    const names = ['zondag', 'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag'];
    statusEls.forEach((el) => {
      let week;
      try { week = JSON.parse(el.dataset.week); } catch { return; }
      if (day < 0 || !week) return;
      const today = week[day];
      let open = false, text;
      if (today && now >= mins(today[0]) && now < mins(today[1])) {
        open = true;
        text = `<strong>Nu open</strong> · tot ${nice(today[1])} uur`;
      } else if (today && now < mins(today[0])) {
        text = `<strong>Gesloten</strong> · vandaag open vanaf ${nice(today[0])} uur`;
      } else {
        let i = 1;
        while (i < 7 && !week[(day + i) % 7]) i++;
        const nxt = week[(day + i) % 7];
        if (!nxt) return;
        text = `<strong>Gesloten</strong> · ${i === 1 ? 'morgen' : names[(day + i) % 7]} open vanaf ${nice(nxt[0])} uur`;
      }
      if ('short' in el.dataset) el.textContent = text.replace(/<[^>]+>/g, '');
      else el.innerHTML = text;
      el.classList.toggle('is-closed', !open);
      el.hidden = false;
    });
  }

  /* Footer: linkgroepen op mobiel standaard dicht */
  if (window.matchMedia('(max-width: 759px)').matches) {
    $$('.footer-group[open]').forEach((d) => { d.open = false; });
  }

  /* Massagekeuze: vijf vragen (voor wie, doel, druk, extra, duur) -> advies met uitleg */
  const quiz = $('[data-quiz]');
  /* Massagekeuze op mobiel: pas tonen na 'Start' */
  const quizOpen = $('[data-quiz-open]');
  if (quiz && quizOpen && window.matchMedia('(max-width: 699px)').matches) {
    const grid = quiz.closest('.quiz-grid');
    quiz.hidden = true;
    quizOpen.hidden = false;
    grid?.classList.add('is-collapsed');
    quizOpen.addEventListener('click', () => {
      quiz.hidden = false;
      quizOpen.hidden = true;
      quizOpen.setAttribute('aria-expanded', 'true');
      grid?.classList.remove('is-collapsed');
      $('.quiz-option', quiz)?.focus({ preventScroll: true });
      quiz.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    });
  }
  if (quiz) {
    const cfg = JSON.parse(quiz.dataset.quiz);
    const steps = $$('.quiz-step', quiz);
    const label = $('[data-quiz-label]', quiz);
    const barEl = $('[data-quiz-bar]', quiz);
    const back = $('[data-quiz-back]', quiz);
    const result = $('[data-quiz-result]', quiz);
    const progress = $('.quiz-progress', quiz);
    const q = (sel) => $(sel, quiz);
    const euro = (n) => `€${n}`;
    let answers = [];
    let current = 0;

    const mode = () => (answers[0] != null ? cfg.steps[0].options[answers[0]].mode : 'self');

    const show = (i, focus) => {
      current = i;
      const m = mode();
      steps.forEach((s, n) => {
        s.hidden = n !== i;
        const legend = $('legend', s);
        const texts = cfg.steps[n].q;
        legend.textContent = texts[m] || texts.self;
        $$('.quiz-option', s).forEach((b) => b.setAttribute('aria-pressed', String(answers[n] === +b.dataset.o)));
      });
      label.textContent = `Vraag ${i + 1} van ${steps.length}`;
      barEl.style.transform = `scaleX(${(i + 1) / steps.length})`;
      back.hidden = i === 0;
      if (focus) $('.quiz-option', steps[i])?.focus({ preventScroll: true });
    };

    const score = () => {
      const pts = Object.fromEntries(cfg.order.map((id) => [id, 0]));
      const goal = cfg.steps[1].options[answers[1]]?.w || {};
      answers.forEach((o, i) => {
        const w = cfg.steps[i].options[o]?.w || {};
        Object.entries(w).forEach(([id, v]) => { if (id in pts) pts[id] += v; });
      });
      // Gelijke stand: eerst het doel (vraag 2), dan de vaste volgorde
      const ranked = [...cfg.order].sort((a, b) =>
        (pts[b] - pts[a]) || ((goal[b] || 0) - (goal[a] || 0)) || (cfg.order.indexOf(a) - cfg.order.indexOf(b)));
      return { pts, ranked };
    };

    const finish = () => {
      const m = mode();
      const { pts, ranked } = score();
      const best = ranked[0];
      const alt = ranked.find((id) => id !== best && pts[id] > 0);
      const t = cfg.t[best];
      const dur = cfg.steps[4].options[answers[4]]?.dur;
      const prices = (m === 'duo' ? t.duo : t.solo) || [];
      const di = cfg.durations.indexOf(dur);

      q('[data-quiz-kicker]').textContent = m === 'duo' ? 'Jullie beste match' : m === 'gift' ? 'Mooi cadeau-idee' : 'Jouw beste match';
      q('[data-quiz-title]').textContent = m === 'duo' ? `${t.name}, samen als duo` : m === 'gift' ? `Cadeaubon voor een ${t.lname}` : t.name;

      let meta;
      if (di > -1 && prices[di]) meta = `${dur} minuten · ${euro(prices[di])}${m === 'duo' ? ' voor twee personen' : ''}`;
      else meta = `${cfg.durations.join(', ').replace(/, (\d+)$/, ' of $1')} minuten · vanaf ${euro(Math.min(...prices.filter(Boolean)))}${m === 'duo' ? ' voor twee' : ''}`;
      q('[data-quiz-meta]').textContent = meta;
      q('[data-quiz-text]').textContent = t.text;

      // Redenen: alleen antwoorden die echt punten gaven aan deze behandeling
      const why = [];
      answers.forEach((o, i) => {
        const opt = cfg.steps[i].options[o];
        if (opt?.why && (opt.w?.[best] || 0) > 0) why.push(opt.why);
      });
      if (m === 'duo') why.push('Jullie worden tegelijk behandeld');
      if (m === 'gift') why.push('Een cadeaubon regel je in de salon of via WhatsApp');
      if (!why.length) why.push('Een veelzijdige keuze als je nog geen duidelijke voorkeur hebt');
      const list = q('[data-quiz-why]');
      list.replaceChildren(...why.map((w) => Object.assign(document.createElement('li'), { textContent: w })));

      q('[data-quiz-book]').hidden = m === 'gift';
      q('[data-quiz-gift]').hidden = m !== 'gift';
      const link = q('[data-quiz-link]');
      link.href = m === 'duo' ? cfg.duoUrl : t.url;
      link.textContent = m === 'duo' ? 'Meer over duo-massage' : `Meer over ${t.lname}`;

      const altBox = q('[data-quiz-alt]');
      altBox.hidden = !alt;
      if (alt) {
        const a = q('[data-quiz-alt-link]');
        a.href = cfg.t[alt].url;
        a.textContent = cfg.t[alt].name;
      }

      steps.forEach((s) => { s.hidden = true; });
      progress.hidden = true;
      result.hidden = false;
      result.focus({ preventScroll: true });
      if (!mqDesktop.matches) result.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const reset = () => {
      answers = [];
      result.hidden = true;
      progress.hidden = false;
      show(0);
    };

    steps.forEach((step, i) => {
      $$('.quiz-option', step).forEach((btn) => btn.addEventListener('click', () => {
        answers[i] = +btn.dataset.o;
        answers.length = i + 1;
        if (i === steps.length - 1) finish();
        else show(i + 1, true);
      }));
    });
    back.addEventListener('click', () => { if (current > 0) show(current - 1, true); });
    q('[data-quiz-restart]')?.addEventListener('click', () => { reset(); $('.quiz-option', steps[0])?.focus({ preventScroll: true }); });
    reset();
  }
})();
