/* Kron Word · 传送带消消乐 demo engine
 * Shared by juicy.html (果冻糖果版) and sticker.html (黑金贴纸版).
 * Data comes from data.js (window.KRON_DATA), built by scripts/build_demo_data.py.
 */
(function () {
  'use strict';
  const DATA = window.KRON_DATA;
  const TRAY_SIZE = 7;          // 3 colours × 2 + 1: the tray can never deadlock
  const MATCH = 3;              // same colour × 3 → 撞掉
  const COLORS = ['c1', 'c2', 'c3'];
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const store = {
    get(k, d) { try { const v = localStorage.getItem('kronword:' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('kronword:' + k, JSON.stringify(v)); } catch (e) { } }
  };

  /* ---------------- sound ---------------- */
  const sfx = {
    ctx: null,
    ac() { if (!this.ctx) { try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { } } return this.ctx; },
    tone(f, d = 0.09, type = 'sine', vol = 0.18, delay = 0) {
      const c = this.ac(); if (!c) return;
      const t = c.currentTime + delay, o = c.createOscillator(), g = c.createGain();
      o.type = type; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 1.5, t + d);
      g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + d + 0.08);
      o.connect(g).connect(c.destination); o.start(t); o.stop(t + d + 0.1);
    },
    pop(n = 0) { this.tone(520 + n * 60, 0.06, 'triangle', 0.16); },
    back() { this.tone(300, 0.05, 'triangle', 0.12); },
    wrong() { this.tone(180, 0.18, 'sawtooth', 0.08); },
    right() { [0, 4, 7, 12].forEach((s, i) => this.tone(523 * Math.pow(2, s / 12), 0.12, 'triangle', 0.15, i * 0.07)); },
    smash(combo) { [0, 7, 12, 16, 19].forEach((s, i) => this.tone(392 * Math.pow(2, (s + combo * 2) / 12), 0.1, 'square', 0.07, i * 0.05)); }
  };
  const buzz = ms => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { } };

  /* Phonics-ish TTS: consonant-only chunks get a sound-alike so the voice says the sound, not the letter names. */
  const PHONICS = { b: 'buh', c: 'kuh', d: 'duh', f: 'fff', g: 'guh', h: 'huh', j: 'juh', k: 'kuh', l: 'lll', m: 'mmm', n: 'nnn', p: 'puh', q: 'kwuh', r: 'rrr', s: 'sss', t: 'tuh', v: 'vvv', w: 'wuh', x: 'ks', z: 'zzz', sh: 'shh', ch: 'chuh', th: 'thuh', ph: 'fff', wh: 'wuh', wr: 'ruh', kn: 'nuh', ck: 'kuh', ng: 'ng', gg: 'guh', ll: 'lll', ss: 'sss', cks: 'ks' };
  let voice = null;
  function pickVoice() {
    try {
      const vs = speechSynthesis.getVoices().filter(v => /^en(-|_)/i.test(v.lang));
      voice = vs.find(v => /Samantha|Google US|Aria|Jenny/i.test(v.name)) || vs.find(v => /en-US/i.test(v.lang)) || vs[0] || null;
    } catch (e) { }
  }
  try { pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; } catch (e) { }
  function speak(text, rate = 0.9) {
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US'; u.rate = rate; if (voice) u.voice = voice;
      speechSynthesis.speak(u);
    } catch (e) { }
  }
  function speakChunk(chunk) {
    const c = chunk.toLowerCase();
    if (!/[aeiouy]/.test(c)) return speak(PHONICS[c] || c.split('').map(x => PHONICS[x] || x).join(' '), 0.8);
    speak(c, 0.75);
  }

  /* ---------------- Kron mascot ---------------- */
  function kronSVG(mood = 'happy', size = 56) {
    const mouth = mood === 'wow' ? '<ellipse cx="50" cy="70" rx="7" ry="8" fill="#7a2b1d"/>'
      : mood === 'oops' ? '<path d="M40 72 q10 -7 20 0" stroke="#7a2b1d" stroke-width="4" fill="none" stroke-linecap="round"/>'
        : '<path d="M37 66 q13 14 26 0" stroke="#7a2b1d" stroke-width="4" fill="#fff" stroke-linecap="round"/>';
    return `<svg class="kron" width="${size}" height="${size}" viewBox="0 0 100 100" aria-label="Kron">
      <circle cx="50" cy="54" r="38" fill="#FFD9B8"/>
      <path d="M14 46 q4 -34 36 -34 q34 0 38 32 q-10 -12 -22 -14 q4 8 -2 12 q-6 -12 -20 -12 q-12 0 -18 10 q-2 -6 2 -12 q-10 6 -14 18z" fill="#2b2320"/>
      <circle cx="12" cy="56" r="7" fill="#FFC8A0"/><circle cx="88" cy="56" r="7" fill="#FFC8A0"/>
      <g fill="none" stroke="#2b2320" stroke-width="4"><rect x="24" y="44" width="21" height="17" rx="7" fill="#fff" fill-opacity=".55"/><rect x="55" y="44" width="21" height="17" rx="7" fill="#fff" fill-opacity=".55"/><path d="M45 51 h10"/></g>
      <circle cx="35" cy="53" r="3.6" fill="#2b2320"/><circle cx="65" cy="53" r="3.6" fill="#2b2320"/>
      <circle cx="26" cy="66" r="5" fill="#FF9A8A" opacity=".55"/><circle cx="74" cy="66" r="5" fill="#FF9A8A" opacity=".55"/>
      ${mouth}</svg>`;
  }

  /* ---------------- word helpers ---------------- */
  // 'pl|ay an in|stru|ment' → [{type:'b',text:'pl',i:0}, ..., {type:'gap'}, ...]
  function parseBlocks(enc) {
    const parts = []; let i = 0, n = 0;
    enc.split(/([A-Za-z|]+)/).forEach(run => {
      if (!run) return;
      if (/^[A-Za-z|]+$/.test(run)) run.split('|').filter(Boolean).forEach(t => parts.push({ type: 'b', text: t, i: n++ }));
      else if (/^\s+$/.test(run)) parts.push({ type: 'gap' });
      else parts.push({ type: 'glyph', text: run.trim() });
    });
    return parts;
  }
  const plain = w => w.b.replace(/\|/g, '');
  // hide the answer inside Kron's tip: the word itself, its parts and its blocks
  function maskTip(tip, w) {
    const word = plain(w).toLowerCase();
    const bits = new Set(word.split(/[^a-z]+/).filter(t => t.length >= 2));
    parseBlocks(w.b).forEach(p => p.type === 'b' && p.text.length >= 2 && bits.add(p.text.toLowerCase()));
    return esc(tip).replace(/[A-Za-z]+/g, t => {
      const l = t.toLowerCase();
      return bits.has(l) || (l.length >= 3 && word.includes(l)) || l.includes(word) ? '<span class="mask">？？</span>' : t;
    });
  }
  function highlight(sentence, chunks) {
    const low = sentence.toLowerCase(), mark = new Array(sentence.length).fill(false);
    chunks.filter(c => c.length >= 2).forEach(c => {
      c = c.toLowerCase(); let k = low.indexOf(c);
      while (k >= 0) { for (let j = k; j < k + c.length; j++) mark[j] = true; k = low.indexOf(c, k + 1); }
    });
    let html = '', on = false;
    for (let i = 0; i < sentence.length; i++) {
      if (mark[i] !== on) { html += mark[i] ? '<mark>' : '</mark>'; on = mark[i]; }
      html += esc(sentence[i]);
    }
    return html + (on ? '</mark>' : '');
  }
  const shortCn = s => String(s || '').replace(/\s*[（(].*?[）)]\s*/g, '').split(/[\/／;；,，]/)[0].trim().slice(0, 8);

  /* ---------------- state ---------------- */
  const S = {
    bookId: store.get('book', 'pu0'), unit: store.get('unit', 3), count: store.get('count', 9),
    cards: [], belt: [], tray: [], active: null, cleared: 0, score: 0, combo: 0, best: 0, firstTry: 0, mistakes: 0, raf: 0
  };
  const book = () => DATA.books.find(b => b.id === S.bookId) || DATA.books[0];

  /* ---------------- setup screen ---------------- */
  function renderSetup() {
    const b = book();
    if (S.unit >= b.units.length) S.unit = 0;
    const isFeat = (bid, ui) => DATA.featured.some(f => f.book === bid && f.unit === ui);
    $('#setup').innerHTML = `
      <div class="setup-inner">
        <div class="brand">${kronSVG('happy', 64)}<div><h1>Kron Word</h1><p>${esc(document.body.dataset.tagline || '')}</p></div></div>
        <div class="howto">
          <div><b>1</b>传送带上挑一张卡片</div>
          <div><b>2</b>点音节积木，听拼读、拼单词</div>
          <div><b>3</b>拼完收进卡槽，同色 ${MATCH} 张撞掉！</div>
        </div>
        <h2>选词书</h2>
        <div class="books">${DATA.books.map(x => `<button class="book ${x.id === b.id ? 'on' : ''}" data-book="${x.id}" style="--bk:${x.color}"><small>${esc(x.series)}</small><span>${esc(x.level)}</span></button>`).join('')}</div>
        <h2>选单元</h2>
        <div class="units">${b.units.map((u, i) => `<button class="unit ${i === S.unit ? 'on' : ''}" data-unit="${i}">
          <span class="un">${esc(u.n)}</span><span class="ut">${esc(u.t.replace(/^.*?·\s*/, ''))}</span><span class="uc">${u.w.length} 词${isFeat(b.id, i) ? ' · <em>绕口令</em>' : ''}</span></button>`).join('')}</div>
        <h2>这一轮背几个</h2>
        <div class="counts">${[6, 9, 12, 15].map(n => `<button class="count ${n === S.count ? 'on' : ''}" data-count="${n}">${n}</button>`).join('')}</div>
        <button class="go big-btn" id="go">开始传送！</button>
        <p class="foot">演示版 · 数据来自仓库里的 ${DATA.books.length} 本词书 · 绕口令和 Kron 插画目前只有 Power Up Start Smart 的 Unit 3、Unit 6</p>
      </div>`;
    $('#setup').onclick = e => {
      const t = e.target.closest('button'); if (!t) return;
      sfx.pop();
      if (t.dataset.book) { S.bookId = t.dataset.book; S.unit = 0; renderSetup(); }
      else if (t.dataset.unit) { S.unit = +t.dataset.unit; renderSetup(); }
      else if (t.dataset.count) { S.count = +t.dataset.count; renderSetup(); }
      else if (t.id === 'go') start();
    };
    const on = $('#setup .unit.on'); if (on) on.scrollIntoView({ block: 'nearest' });
  }

  /* ---------------- game ---------------- */
  function pickWords() {
    const b = book(), first = shuffle(b.units[S.unit].w);
    const rest = shuffle(b.units.filter((_, i) => i !== S.unit).flatMap(u => u.w));
    const seen = new Set(), out = [];
    for (const w of first.concat(rest)) { const k = w.t.toLowerCase(); if (!seen.has(k)) { seen.add(k); out.push(w); } if (out.length >= S.count) break; }
    return out;
  }
  function start() {
    store.set('book', S.bookId); store.set('unit', S.unit); store.set('count', S.count);
    const words = pickWords();
    const n = words.length - words.length % MATCH;
    // colour by groups of 3 so every colour count is a multiple of MATCH and the round always clears
    const colors = shuffle(Array.from({ length: n }, (_, i) => COLORS[Math.floor(i / MATCH) % COLORS.length]));
    S.cards = words.slice(0, n).map((w, i) => ({ id: i, w, color: colors[i], done: false }));
    S.belt = []; S.tray = []; S.active = null; S.cleared = 0; S.score = 0; S.combo = 0; S.best = 0; S.firstTry = 0; S.mistakes = 0;
    document.body.classList.remove('show-setup', 'show-end');
    $('#tray').innerHTML = Array.from({ length: TRAY_SIZE }, () => '<div class="tslot"></div>').join('');
    buildBelt(); renderStageIdle(); renderHud();
    sfx.right();
  }

  /* conveyor belt: cards drift right→left and loop, like the PvZ seed conveyor */
  function buildBelt() {
    const belt = $('#belt-cards'); belt.innerHTML = '';
    const W = belt.clientWidth || 360, cw = 86, gap = 14;
    S.loop = Math.max(W + cw + gap, S.cards.length * (cw + gap));
    S.cards.forEach((c, i) => {
      const el = document.createElement('button');
      el.className = `card ${c.color}`;
      el.innerHTML = `<i class="dot"></i><span class="em">${c.w.em || ''}</span><span class="cn">${esc(shortCn(c.w.m))}</span><span class="len">${parseBlocks(c.w.b).filter(p => p.type === 'b').length} 块</span>`;
      el.onclick = () => takeCard(c, el);
      belt.appendChild(el);
      c.el = el; c.x = 16 + i * (cw + gap);
      S.belt.push(c);
    });
    cancelAnimationFrame(S.raf);
    let last = performance.now();
    const tick = now => {
      const dt = Math.min(0.05, (now - last) / 1000); last = now;
      const speed = S.active ? 22 : 46;
      S.belt.forEach(c => {
        c.x -= speed * dt;
        if (c.x < -cw - gap) c.x += S.loop;
        c.el.style.transform = `translateX(${c.x}px)`;
      });
      S.raf = requestAnimationFrame(tick);
    };
    S.raf = requestAnimationFrame(tick);
  }

  function fly(fromEl, toRect, cls, html, ms = 420) {
    const r = fromEl.getBoundingClientRect(), f = document.createElement('div');
    f.className = 'flyer ' + cls; f.innerHTML = html;
    Object.assign(f.style, { left: r.left + 'px', top: r.top + 'px', width: r.width + 'px', height: r.height + 'px' });
    document.body.appendChild(f);
    const dx = toRect.left + toRect.width / 2 - (r.left + r.width / 2), dy = toRect.top + toRect.height / 2 - (r.top + r.height / 2);
    const s = Math.min(toRect.width / r.width, toRect.height / r.height);
    const a = f.animate([
      { transform: 'translate(0,0) scale(1) rotate(0)' },
      { transform: `translate(${dx * 0.5}px,${dy * 0.5 - 40}px) scale(${(1 + s) / 2 * 1.1}) rotate(-6deg)`, offset: 0.55 },
      { transform: `translate(${dx}px,${dy}px) scale(${s}) rotate(0)` }
    ], { duration: ms, easing: 'cubic-bezier(.5,0,.3,1)' });
    return a.finished.then(() => f.remove());
  }

  function takeCard(c, el) {
    if (S.active) { el.animate([{ transform: el.style.transform + ' rotate(0)' }, { transform: el.style.transform + ' rotate(-8deg)' }, { transform: el.style.transform + ' rotate(8deg)' }, { transform: el.style.transform }], { duration: 300 }); sfx.back(); toast('先把手上这张拼完～'); return; }
    S.active = { card: c, mistakes: 0 };
    S.belt = S.belt.filter(x => x !== c);
    sfx.pop(3); buzz(8);
    const target = $('#stage').getBoundingClientRect();
    fly(el, { left: target.left + target.width / 2 - 60, top: target.top + 10, width: 120, height: 60 }, `card ${c.color}`, el.innerHTML, 380);
    el.remove();
    renderStudy();
  }

  function renderStageIdle() {
    const left = S.cards.filter(c => !c.done && !S.tray.includes(c)).length;
    $('#stage').innerHTML = `<div class="idle">${kronSVG('happy', 88)}
      <div class="bubble big">${left ? `从上面的传送带挑一张卡片吧！<br><small>卡槽里同色 ${MATCH} 张会撞掉，挑颜色也是策略哦</small>` : '卡片都拼完啦，看看卡槽！'}</div></div>`;
  }

  function renderStudy() {
    const { card } = S.active, w = card.w, parts = parseBlocks(w.b);
    const blocks = parts.filter(p => p.type === 'b');
    let order = shuffle(blocks);
    for (let k = 0; k < 4 && blocks.length > 1 && order.every((b, i) => b.text === blocks[i].text); k++) order = shuffle(blocks);
    S.active.parts = parts; S.active.blocks = blocks; S.active.slots = blocks.map(() => null);
    $('#stage').innerHTML = `
      <div class="study ${card.color}">
        <div class="tip">${kronSVG('happy', 46)}<div class="bubble"><b>Kron 的脑洞</b>${maskTip(w.k, w) || '这个词我也有话说……先拼出来看看！'}</div></div>
        <div class="meaning"><span class="cn">${esc(w.m)}</span><button class="ear" id="ear" title="听整个单词">🔊</button></div>
        <div class="slots" id="slots">${parts.map(p => p.type === 'b' ? `<div class="slot" data-i="${p.i}"></div>` : p.type === 'gap' ? '<div class="sgap"></div>' : `<div class="glyph">${esc(p.text)}</div>`).join('')}</div>
        <div class="tiles" id="tiles">${order.map(b => `<button class="tile" data-k="${b.i}">${esc(b.text)}</button>`).join('')}</div>
        <p class="hint">点积木听拼读 · 按顺序拼出单词 · 点已放好的积木可以拿回来</p>
      </div>`;
    $('#ear').onclick = () => speak(plain(w), 0.8);
    $('#tiles').onclick = e => { const t = e.target.closest('.tile'); if (t && !t.classList.contains('used')) placeTile(t); };
    $('#slots').onclick = e => { const s = e.target.closest('.slot.filled'); if (s) returnTile(s); };
  }

  function placeTile(t) {
    const A = S.active, k = +t.dataset.k, b = A.blocks.find(x => x.i === k);
    const si = A.slots.indexOf(null); if (si < 0) return;
    A.slots[si] = k;
    speakChunk(b.text); sfx.pop(si); buzz(6);
    t.classList.add('used');
    const slot = $(`#slots .slot[data-i="${A.blocks[si].i}"]`);
    slot.classList.add('filled', 'incoming'); slot.dataset.k = k; slot.textContent = b.text;
    fly(t, slot.getBoundingClientRect(), 'tile', esc(b.text), 260).then(() => {
      slot.classList.remove('incoming'); slot.classList.add('land');
      setTimeout(() => slot.classList.remove('land'), 300);
      if (!A.slots.includes(null)) check();
    });
  }
  function returnTile(slot) {
    const A = S.active; if (A.locked) return;
    const k = +slot.dataset.k, si = A.slots.indexOf(k);
    if (si < 0) return;
    A.slots[si] = null; sfx.back();
    slot.classList.remove('filled', 'bad'); slot.textContent = ''; delete slot.dataset.k;
    const t = $(`#tiles .tile[data-k="${k}"]`); t.classList.remove('used'); t.classList.add('land'); setTimeout(() => t.classList.remove('land'), 300);
  }

  function check() {
    const A = S.active;
    const ok = A.slots.every((k, i) => A.blocks.find(b => b.i === k).text.toLowerCase() === A.blocks[i].text.toLowerCase());
    const slots = [...document.querySelectorAll('#slots .slot')];
    if (!ok) {
      A.mistakes++; S.mistakes++; S.combo = 0; renderHud();
      sfx.wrong(); buzz([20, 40, 20]);
      A.locked = true;
      slots.forEach((s, i) => { const k = A.slots[i]; if (A.blocks.find(b => b.i === k).text.toLowerCase() !== A.blocks[i].text.toLowerCase()) s.classList.add('bad'); });
      $('#slots').classList.add('shake');
      setTimeout(() => {
        $('#slots').classList.remove('shake'); A.locked = false;
        slots.filter(s => s.classList.contains('bad')).forEach(returnTile);
      }, 650);
      return;
    }
    A.locked = true;
    if (!A.mistakes) { S.firstTry++; S.combo++; S.best = Math.max(S.best, S.combo); }
    S.score += A.mistakes ? 10 : 20 + S.combo * 5; renderHud();
    sfx.right(); buzz(15);
    slots.forEach((s, i) => setTimeout(() => s.classList.add('good'), i * 70));
    $('#slots').classList.add('merge');
    setTimeout(() => { speak(plain(A.card.w), 0.85); confetti($('#slots')); }, slots.length * 70 + 120);
    setTimeout(renderReveal, slots.length * 70 + 650);
  }

  function renderReveal() {
    const { card } = S.active, w = card.w, chunks = S.active.blocks.map(b => b.text);
    let sent = '';
    if (w.tw) sent = `<div class="sent"><div class="lbl">Kron 绕口令 <span>同音积木已高亮</span></div><p class="en">${highlight(w.tw, chunks)}</p><p class="zh">${esc(w.twc)}</p><button class="ear" data-say="tw">🔊 读一遍</button></div>`;
    else if (w.e) sent = `<div class="sent"><div class="lbl">例句 <span>绕口令待同步</span></div><p class="en">${highlight(w.e, chunks)}</p>${w.ec ? `<p class="zh">${esc(w.ec)}</p>` : ''}<button class="ear" data-say="e">🔊 读一遍</button></div>`;
    const xs = (w.x || []).map(([wd, hl, cn]) => `<span class="xf">${highlight(wd, [hl])}<small>${esc(cn)}</small></span>`).join('');
    const pic = w.em
      ? `<div class="pic"><div class="scene"><span class="bigem">${w.em}</span><span class="kpeek">${kronSVG('wow', 70)}</span></div><p>🎨 ${esc(w.sc)}</p></div>`
      : `<div class="pic"><div class="scene plain"><span class="kpeek center">${kronSVG('happy', 84)}</span><span class="sign">${esc(plain(w))}</span></div><p>🎨 Kron 插画位（同步本地插画后显示）</p></div>`;
    $('#stage').innerHTML = `
      <div class="reveal ${card.color}">
        <div class="word"><h2>${esc(w.t)}</h2><button class="ear" data-say="w">🔊</button></div>
        <div class="ipa">${esc(w.i)} · ${esc(w.m)}</div>
        <div class="chips">${chunks.map(c => `<button class="chip" data-chunk="${esc(c)}">${esc(c)}</button>`).join('<i>+</i>')}</div>
        <div class="tip small">${kronSVG('wow', 34)}<div class="bubble">${esc(w.k)}</div></div>
        ${pic}${sent}
        ${xs ? `<div class="xfs"><div class="lbl">举一反三</div>${xs}</div>` : ''}
        <button class="big-btn" id="keep">收进卡槽 →</button>
      </div>`;
    $('#stage').scrollTop = 0;
    $('#stage').onclick = e => {
      const t = e.target.closest('[data-say],[data-chunk]'); if (!t) return;
      if (t.dataset.chunk) return speakChunk(t.dataset.chunk);
      speak(t.dataset.say === 'tw' ? w.tw : t.dataset.say === 'e' ? w.e : plain(w), t.dataset.say === 'w' ? 0.8 : 0.85);
    };
    $('#keep').onclick = () => { $('#stage').onclick = null; keepCard(); };
  }

  /* ---------------- tray & match-3 ---------------- */
  function keepCard() {
    const c = S.active.card; c.done = true; S.active = null; renderHud();
    // insert next to cards of the same colour so matches line up
    let at = S.tray.length; for (let i = S.tray.length - 1; i >= 0; i--) if (S.tray[i].color === c.color) { at = i + 1; break; }
    S.tray.splice(at, 0, c);
    renderTray(c);
    const slot = $('#tray').children[at];
    fly($('#keep'), slot.getBoundingClientRect(), `mini ${c.color}`, `<span>${esc(plain(c.w))}</span>`, 420).then(() => {
      slot.classList.add('land'); sfx.pop(5);
      setTimeout(() => resolveMatches(), 200);
    });
    renderStageIdle();
  }
  function renderTray(hidden) {
    const slots = $('#tray').children;
    for (let i = 0; i < TRAY_SIZE; i++) {
      const c = S.tray[i], s = slots[i];
      s.className = 'tslot' + (c ? ` full ${c.color}` : '') + (c && c === hidden ? ' pending' : '');
      s.innerHTML = c ? `<i class="dot"></i><span>${esc(plain(c.w))}</span>` : '';
    }
  }
  function resolveMatches() {
    renderTray();
    const by = {}; S.tray.forEach(c => (by[c.color] = by[c.color] || []).push(c));
    const hit = Object.values(by).find(a => a.length >= MATCH);
    if (!hit) { if (S.tray.length >= TRAY_SIZE) toast('卡槽满啦，先拼同色的卡！'); maybeEnd(); return; }
    const group = hit.slice(0, MATCH), idx = group.map(c => S.tray.indexOf(c)), slots = $('#tray').children;
    const mid = slots[idx[1]].getBoundingClientRect();
    idx.forEach(i => {
      const r = slots[i].getBoundingClientRect();
      slots[i].animate([{ transform: 'translate(0,0) scale(1)' }, { transform: `translate(${(mid.left - r.left) * 0.9}px,-18px) scale(1.15)`, offset: 0.6 }, { transform: `translate(${mid.left - r.left}px,-10px) scale(0.2)`, opacity: 0 }], { duration: 520, easing: 'cubic-bezier(.6,-0.3,.7,1)', fill: 'forwards' });
    });
    S.smash = (S.smash || 0) + 1;
    setTimeout(() => {
      sfx.smash(Math.min(S.smash, 5)); buzz([10, 30, 30]);
      burst(mid, group[0].color);
      S.score += 60; S.cleared += MATCH; renderHud();
      toast(['撞掉！', '漂亮！', '三连消！', 'Kron 为你鼓掌 👏'][Math.random() * 4 | 0], 'good');
      S.tray = S.tray.filter(c => !group.includes(c));
      [...slots].forEach(s => s.getAnimations().forEach(a => a.cancel()));
      renderTray();
      setTimeout(resolveMatches, 150);
    }, 520);
  }
  function maybeEnd() {
    if (S.cleared < S.cards.length) return;
    setTimeout(() => {
      cancelAnimationFrame(S.raf);
      document.body.classList.add('show-end');
      const acc = Math.round(S.firstTry / S.cards.length * 100);
      $('#end').innerHTML = `<div class="end-inner">${kronSVG('wow', 110)}
        <h2>全部撞掉！</h2>
        <div class="stats"><div><b>${S.score}</b><span>得分</span></div><div><b>${acc}%</b><span>一次拼对</span></div><div><b>${S.best}</b><span>最高连击</span></div></div>
        <div class="learned">${S.cards.map(c => `<button class="mini ${c.color}" data-w="${esc(plain(c.w))}"><i class="dot"></i>${esc(plain(c.w))}<small>${esc(shortCn(c.w.m))}</small></button>`).join('')}</div>
        <button class="big-btn" id="again">再来一轮</button><button class="ghost-btn" id="menu">换词书</button></div>`;
      confetti($('#end .kron'), 80);
      $('#end').onclick = e => { const t = e.target.closest('button'); if (!t) return; if (t.dataset.w) speak(t.dataset.w); else if (t.id === 'again') start(); else if (t.id === 'menu') openSetup(); };
    }, 400);
  }

  /* ---------------- hud / fx ---------------- */
  function renderHud() {
    const total = S.cards.length || 1;
    $('#hud').innerHTML = `<button class="x" id="quit" aria-label="返回">✕</button>
      <div class="bar"><i style="width:${S.cards.filter(c => c.done).length / total * 100}%"></i></div>
      <span class="pill">⚡ ${S.score}</span>${S.combo > 1 ? `<span class="pill fire">🔥 ${S.combo}</span>` : ''}`;
    $('#quit').onclick = openSetup;
  }
  function openSetup() { cancelAnimationFrame(S.raf); document.body.classList.remove('show-end'); document.body.classList.add('show-setup'); renderSetup(); }
  let toastT;
  function toast(msg, kind = '') {
    const t = $('#toast'); t.textContent = msg; t.className = 'show ' + kind;
    clearTimeout(toastT); toastT = setTimeout(() => t.className = '', 1300);
  }
  function confetti(el, n = 36) {
    if (!el) return;
    const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const cols = getComputedStyle(document.body).getPropertyValue('--confetti').split(',').map(s => s.trim()).filter(Boolean);
    for (let i = 0; i < n; i++) {
      const p = document.createElement('i'); p.className = 'confetti';
      p.style.background = cols[i % cols.length]; p.style.left = cx + 'px'; p.style.top = cy + 'px';
      document.body.appendChild(p);
      const a = Math.random() * Math.PI * 2, v = 80 + Math.random() * 160;
      p.animate([{ transform: 'translate(0,0) rotate(0)', opacity: 1 }, { transform: `translate(${Math.cos(a) * v}px,${Math.sin(a) * v - 60}px) rotate(${Math.random() * 720}deg)`, opacity: 1, offset: 0.6 }, { transform: `translate(${Math.cos(a) * v * 1.2}px,${Math.sin(a) * v + 120}px) rotate(${Math.random() * 900}deg)`, opacity: 0 }], { duration: 900 + Math.random() * 500, easing: 'cubic-bezier(.2,.8,.4,1)' }).finished.then(() => p.remove());
    }
  }
  function burst(r, color) {
    const ring = document.createElement('i'); ring.className = `ring ${color}`;
    ring.style.left = r.left + r.width / 2 + 'px'; ring.style.top = r.top + r.height / 2 + 'px';
    document.body.appendChild(ring);
    ring.animate([{ transform: 'translate(-50%,-50%) scale(.2)', opacity: 1 }, { transform: 'translate(-50%,-50%) scale(3.2)', opacity: 0 }], { duration: 600, easing: 'ease-out' }).finished.then(() => ring.remove());
    confetti({ getBoundingClientRect: () => r }, 28);
  }

  window.addEventListener('resize', () => { if (S.cards.length && !document.body.classList.contains('show-setup')) { const W = $('#belt-cards').clientWidth; S.loop = Math.max(W + 100, S.belt.length * 100); } });
  document.addEventListener('DOMContentLoaded', () => { document.body.classList.add('show-setup'); renderSetup(); });
})();
