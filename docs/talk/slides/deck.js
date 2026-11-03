// Deck engine: step builds, cued video clips and keyboard control. No network, no dependencies.
//
// Keys: Right, Space, PageDown = next. Left, PageUp = back. Home, End. F = full screen.
// B = blank the screen. G = go to a slide number. P = show the slide number.
//
// data-step="n"          revealed at step n of its slide.
// data-clips="n:a:b;..." on a video: at step n, play from a to b seconds, then hold the frame.
// data-bar="w"           on .fillbar: grows to w px when its step is reached.
// data-h="h"             on a budget bar: grows to h px when its step is reached.
(function () {
  const stage = document.getElementById('stage');
  const slides = [...document.querySelectorAll('.slide')];
  let index = 0;
  let step = 0;

  const stepsOf = (s) => Math.max(0, ...[...s.querySelectorAll('[data-step]')].map((e) => +e.dataset.step),
    ...[...s.querySelectorAll('[data-clips]')].flatMap((v) => parseClips(v).map((c) => c.step)));

  function parseClips(v) {
    return (v.dataset.clips || '').split(';').filter(Boolean).map((c) => {
      const [step, from, to] = c.split(':').map(Number);
      return { step, from, to };
    });
  }

  function brandAll() {
    slides.forEach((s) => {
      const kind = s.dataset.brand;
      if (kind === 'none') return;
      const light = kind === 'light';
      const b = document.createElement('div');
      b.className = 'brand';
      b.style.color = light ? '#FFFFFF' : '#0B1220';
      b.innerHTML = `<img src="local/shipht-${light ? 'light' : 'dark'}.png" alt=""><span>Shipht</span>`;
      (s.querySelector('.block') || s).appendChild(b);
    });
  }

  function fit() {
    const k = Math.min(innerWidth / 1280, innerHeight / 720);
    stage.style.transform = `translate(-50%, -50%) scale(${k})`;
  }

  function pauseAll() {
    document.querySelectorAll('video').forEach((v) => { v.pause(); v._stop = null; });
  }

  function cue(s) {
    s.querySelectorAll('video[data-clips]').forEach((v) => {
      const clips = parseClips(v);
      const clip = clips.find((c) => c.step === step);
      if (clip) {
        // Seeking in the long recording can stall, so a clip that continues from where the
        // video already is just keeps playing.
        if (Math.abs(v.currentTime - clip.from) > 0.5) v.currentTime = clip.from;
        v._stop = clip.to;
        v.play().catch(() => {});
      } else if (step === 0 && clips.length) {
        v._stop = null;
        v.currentTime = clips[0].from;
      }
    });
  }

  function apply(s) {
    s.querySelectorAll('[data-step]').forEach((e) => e.classList.toggle('on', +e.dataset.step <= step));
    s.querySelectorAll('[data-h]').forEach((e) => {
      const at = +(e.dataset.at || 0);
      e.style.height = step >= at ? `${e.dataset.h}px` : '0';
    });
    s.querySelectorAll('[data-bar]').forEach((e) => {
      const at = +(e.dataset.at || 0);
      e.style.width = step >= at ? `${e.dataset.bar}px` : '0';
    });
    s.querySelectorAll('[data-merge]').forEach((e) => e.classList.toggle('merged', step >= +e.dataset.merge));
    // Scoreboard values: data-from before step data-at, data-to from then on.
    s.querySelectorAll('[data-to]').forEach((e) => {
      const value = step >= +e.dataset.at ? e.dataset.to : e.dataset.from;
      e.textContent = value;
      if (e.parentElement.classList.contains('ms')) {
        e.parentElement.classList.toggle('over', parseFloat(value) > 8.33);
        e.parentElement.classList.toggle('ok', parseFloat(value) <= 8.33);
      }
    });
  }

  function show(i, st) {
    const changed = i !== index || !slides[i].classList.contains('active');
    if (changed) {
      pauseAll();
      slides.forEach((s) => s.classList.remove('active'));
      slides[i].classList.add('active');
    }
    index = i;
    if (changed) {
      // Start hidden so entrance transitions run each time the slide opens.
      step = -1;
      apply(slides[index]);
      void slides[index].offsetWidth;
    }
    step = st;
    apply(slides[index]);
    cue(slides[index]);
    document.getElementById('pos').textContent = `${index + 1}/${slides.length}`;
    history.replaceState(null, '', `#${index + 1}.${step}`);
  }

  function next() {
    if (step < stepsOf(slides[index])) show(index, step + 1);
    else if (index < slides.length - 1) show(index + 1, 0);
  }
  function back() {
    if (step > 0) show(index, step - 1);
    else if (index > 0) show(index - 1, stepsOf(slides[index - 1]));
  }

  document.addEventListener('keydown', (e) => {
    const k = e.key;
    if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); back(); }
    else if (k === 'Home') show(0, 0);
    else if (k === 'End') show(slides.length - 1, 0);
    else if (k === 'f' || k === 'F') {
      if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen();
    } else if (k === 'b' || k === 'B') {
      const b = document.getElementById('black');
      b.style.display = b.style.display === 'block' ? 'none' : 'block';
    } else if (k === 'p' || k === 'P') {
      const n = document.getElementById('pos');
      n.style.display = n.style.display === 'block' ? 'none' : 'block';
    } else if (k === 'g' || k === 'G') {
      const n = parseInt(prompt('Go to slide'), 10);
      if (n >= 1 && n <= slides.length) show(n - 1, 0);
    }
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('a')) next(); });

  document.querySelectorAll('video').forEach((v) => {
    v.muted = true;
    v.addEventListener('timeupdate', () => {
      if (v._stop != null && v.currentTime >= v._stop) { v.pause(); v._stop = null; }
    });
  });

  // Charts built from data
  document.querySelectorAll('.squares[data-count]').forEach((box) => {
    const n = +box.dataset.count;
    box.innerHTML = '<i></i>'.repeat(n);
    [...box.children].forEach((c, i) => { c.style.transitionDelay = `${i * 8}ms`; });
  });
  document.querySelectorAll('[data-segs]').forEach((box) => { box.innerHTML = '<i style="height:100%"></i>'.repeat(+box.dataset.segs); });
  const HEIGHTS = [52, 70, 96, 78, 110, 134, 118, 160, 186, 214, 246, 268, 292, 278, 300];
  document.querySelectorAll('.budget[data-bars]').forEach((box) => {
    const limit = 118;
    const html = HEIGHTS.map((h, i) => `<i class="${h > limit ? 'late' : ''}" data-h="${h}" data-at="1" style="transition-delay:${i * 45}ms"></i>`).join('');
    box.insertAdjacentHTML('afterbegin', html);
  });
  document.querySelectorAll('.trace .bar[data-trace]').forEach((bar) => {
    const [key, part] = bar.dataset.trace.split('.');
    const scale = 100 / +(bar.dataset.window || 100);
    let html = '';
    for (let t = 0; t < 100; t += 8.33) html += `<u style="left:${t * scale}%"></u>`;
    (window.TRACE[key][part] || []).forEach(([start, ms]) => {
      if (start < 0 || start > 100) return;
      html += `<i style="left:${start * scale}%;width:${Math.max(ms * scale, 0.4)}%"></i>`;
    });
    bar.innerHTML = html;
  });

  brandAll();
  addEventListener('resize', fit);
  fit();
  const m = location.hash.match(/#(\d+)(?:\.(\d+))?/);
  const start = m ? Math.min(+m[1] - 1, slides.length - 1) : 0;
  slides[start].classList.add('active');
  index = start;
  show(start, m && m[2] ? +m[2] : 0);

  // PDF backup: show every step, every bar.
  addEventListener('beforeprint', () => {
    document.querySelectorAll('[data-h]').forEach((e) => { e.style.height = `${e.dataset.h}px`; e.style.transition = 'none'; });
    document.querySelectorAll('[data-bar]').forEach((e) => { e.style.width = `${e.dataset.bar}px`; e.style.transition = 'none'; });
    document.querySelectorAll('[data-step]').forEach((e) => e.classList.add('on'));
  });
})();
