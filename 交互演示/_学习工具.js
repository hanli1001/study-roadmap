/* ══════════════════════════════════════════════════════════════════
   交互演示 · 学习工具箱  Lab v1  2026-09-23
   用法：<link rel="stylesheet" href="_主题.css">
        <script src="_学习工具.js" defer></script>
        <script src="_全局进度.js" defer></script>

   四件东西：
     Lab.mindmap(el, 节点)   思维导图（自动排版，墨线生长）
     Lab.rail(el, 数据)      进度轨道 + 停止旗（"你停在哪"）
     Lab.player(el, 步骤)    单步播放器（看得见的过程）
     Lab.wire(el, A, B)      配对流动：一个值沿手绘连线从 A 走到 B ← 招牌动效
   外加：Lab.ink / Lab.drawIn / Lab.store / Lab.initAll（自动接管 data-* 声明）
   ══════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var REDUCED = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── 小工具 ─────────────────────────────────────────────── */
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }
  function svg(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    return n;
  }
  var store = {
    get: function (k, dflt) {
      try { var v = localStorage.getItem(k); return v == null ? dflt : JSON.parse(v); }
      catch (e) { return dflt; }
    },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  /* 中英混排的宽度估算：中日韩字符按 1 个字宽，其余按 0.56 —— 够准且确定 */
  var CJK = /[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]/;
  function textW(s, size) {
    s = String(s == null ? '' : s); var w = 0;
    for (var i = 0; i < s.length; i++) w += CJK.test(s.charAt(i)) ? size : size * 0.56;
    return w;
  }

  /* ══ 思维导图 ═══════════════════════════════════════════════
     节点：{ label, note?, state?, children?[] }
     state: root | done | doing | current | todo   （颜色不是主角，笔触才是） */
  var PADX = 11, PADY = 7;
  function measure(n, d, acc) {
    n._d = d;
    n._h = n.note ? 44 : 31;
    n._w = Math.max(54,
      textW(n.label, 12.5) + PADX * 2,
      n.note ? textW(n.note, 10.5) + PADX * 2 : 0);
    acc.w[d] = Math.max(acc.w[d] || 0, n._w);
    var kids = n.children || [];
    if (!kids.length) { n._row = acc.rows++; }
    else kids.forEach(function (c) { measure(c, d + 1, acc); });
    return acc;
  }
  function placeH(n, colX) {
    n._x = colX[n._d];
    var kids = n.children || [];
    if (kids.length) {
      kids.forEach(function (c) { placeH(c, colX); });
      n._y = (kids[0]._y + kids[kids.length - 1]._y) / 2;
    } else { n._y = n._row * acc.rowH; }
  }
  var acc = null; /* 排版中途的累加器（单线程，渲染时不重入） */

  function mindmap(host, spec, opts) {
    if (typeof host === 'string') host = $(host);
    if (!host) return;
    opts = opts || {};
    var roots = Array.isArray(spec) ? spec : [spec];
    var box = host.getBoundingClientRect();
    var vertical = opts.vertical === true ||
      (opts.vertical !== false && box.width > 0 && box.width < 620);

    acc = { w: {}, rows: 0, rowH: 56 };
    roots.forEach(function (r) { measure(r, 0, acc); });
    if (!roots.length) return;

    var GAPX = 40, GAPY = 13, IND = 22;
    var colX = [], x = 0;
    if (!vertical) {
      var maxD = Math.max.apply(null, Object.keys(acc.w).map(Number));
      for (var d = 0; d <= maxD; d++) { colX[d] = x; x += (acc.w[d] || 0) + GAPX; }
    }

    /* 纵向：缩进式列表（手机上只有这个读得下去） */
    var cur = 0;
    function placeV(n) {
      n._x = n._d * IND;
      n._y = cur;
      cur += n._h + GAPY;
      (n.children || []).forEach(placeV);
    }

    if (vertical) roots.forEach(placeV);
    else roots.forEach(function (r) { placeH(r, colX); });

    /* 画布尺寸 = 所有节点包围盒 */
    var W = 0, H = 0;
    roots.forEach(function walk(r) {
      W = Math.max(W, r._x + r._w);
      H = Math.max(H, r._y + r._h);
      (r.children || []).forEach(walk);
    });
    W += 12; H += 12;   /* 留出边距：节点贴着容器边缘会像被裁掉 */

    host.textContent = '';
    var s = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H,
                         role: 'img', 'aria-label': opts.label || '思维导图' });
    var gLink = svg('g'), gNode = svg('g');
    s.appendChild(gLink); s.appendChild(gNode);

    var paths = [];
    function drawLinks(n) {
      var kids = n.children || [];
      var x1 = vertical ? n._x + 11 : n._x + n._w;
      var y1 = vertical ? n._y + n._h : n._y + n._h / 2;
      kids.forEach(function (c) {
        var d;
        if (vertical) {                       /* 肘形折线，像目录的层级线 */
          var xm = c._x - 9, ym = c._y + c._h / 2;
          d = 'M' + x1 + ' ' + y1 + ' L' + x1 + ' ' + ym + ' L' + xm + ' ' + ym +
              ' L' + c._x + ' ' + ym;
        } else {                              /* 手绘感的贝塞尔连线 */
          var x2 = c._x, y2 = c._y + c._h / 2, dx = (x2 - x1) * 0.46;
          d = 'M' + x1 + ' ' + y1 + ' C' + (x1 + dx) + ' ' + y1 + ',' +
              (x2 - dx) + ' ' + y2 + ',' + x2 + ' ' + y2;
        }
        var p = svg('path', { d: d, class: 'mm-link' });
        gLink.appendChild(p); paths.push(p);
        drawLinks(c);
      });
    }
    roots.forEach(drawLinks);

    function drawNode(n) {
      var g = svg('g', { class: 'mm-node ' + (n.state || 'todo') });
      g.appendChild(svg('rect', { x: n._x, y: n._y, width: n._w, height: n._h, rx: 4 }));
      var t = svg('text', { x: n._x + PADX, y: n._y + (n.note ? PADY + 9 : n._h / 2 + 1) });
      t.textContent = n.label; g.appendChild(t);
      if (n.note) {
        var t2 = svg('text', { x: n._x + PADX, y: n._y + PADY + 26, class: 'nt' });
        t2.textContent = n.note; g.appendChild(t2);
      }
      gNode.appendChild(g);
      (n.children || []).forEach(drawNode);
    }
    roots.forEach(drawNode);

    host.appendChild(s);
    if (opts.animate !== false) drawIn(paths);
    return s;
  }

  /* 墨线生长：路径按长度自己画出来 */
  function drawIn(paths, opts) {
    if (!paths || !paths.length) return;
    paths = Array.prototype.slice.call(paths);
    if (REDUCED) return;
    var run = function () {
      paths.forEach(function (p, i) {
        var len = 0; try { len = p.getTotalLength(); } catch (e) {}
        if (!len) return;
        p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
        p.style.transition = 'stroke-dashoffset 620ms cubic-bezier(.16,1,.3,1) ' + (i * 45) + 'ms';
        requestAnimationFrame(function () { p.style.strokeDashoffset = 0; });
      });
    };
    onceVisible(paths[0], run);
  }

  function onceVisible(node, fn) {
    if (!node || !global.IntersectionObserver) { fn(); return; }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { io.disconnect(); fn(); } });
    }, { threshold: 0.15 });
    io.observe(node);
  }

  /* ══ 进度轨道 + 停止旗 ═══════════════════════════════════ */
  function rail(host, data) {
    if (typeof host === 'string') host = $(host);
    if (!host) return;
    /* ⚠️ 这一行不能少：.rail 的定位 / 上边距 / 窄屏横滑全靠它。
       漏掉的后果是旗子标签压住上方正文，且手机上整页横向溢出（都实测过）。 */
    host.classList.add('rail');
    host.textContent = '';
    var line = el('div', 'rail-line');
    line.appendChild(el('div', 'rail-done'));
    var stops = el('div', 'rail-stops');
    var n = data.stops.length, nowIdx = -1;
    data.stops.forEach(function (st, i) {
      var d = el('div', 'stop ' + (st.state || ''));
      d.appendChild(document.createTextNode(st.label));
      if (st.date) { var sm = el('small', null, st.date); d.appendChild(sm); }
      if (st.state === 'now') nowIdx = i;
      stops.appendChild(d);
    });
    host.appendChild(line); host.appendChild(stops);

    var pct = nowIdx < 0 ? 0 : ((nowIdx + 0.5) / n) * 100;
    var flag = el('div', 'flag');
    flag.setAttribute('data-l', data.flagLabel || '你在这里');
    flag.style.left = pct + '%';
    line.appendChild(flag);
    if (!REDUCED) {
      onceVisible(host, function () {
        line.querySelector('.rail-done').style.transform = 'scaleX(' + (pct / 100) + ')';
        flag.style.transition = 'left 760ms cubic-bezier(.16,1,.3,1)';
      });
    } else { line.querySelector('.rail-done').style.transform = 'scaleX(' + (pct / 100) + ')'; }
    return host;
  }

  /* ══ 单步播放器 ═════════════════════════════════════════
     Lab.player(host, { steps:[{cap, on:'.sel, .sel2', do:fn}] }) */
  function player(host, cfg) {
    if (typeof host === 'string') host = $(host);
    if (!host) return;
    var steps = cfg.steps || [], i = -1, timer = null;
    host.classList.add('player');
    host.textContent = '';

    var bar = el('div', 'player-bar');
    var bPrev = el('button', null, '上一步'), bNext = el('button', 'primary', '下一步'),
        bPlay = el('button', null, '自动播放'), bReset = el('button', 'ghost', '重置'),
        cnt = el('span', 'count', '0 / ' + steps.length);
    [bPrev, bNext, bPlay, bReset].forEach(function (b) { bar.appendChild(b); });
    bar.appendChild(cnt);
    var body = el('div', 'player-body'), cap = el('div', 'player-cap');
    host.appendChild(bar); host.appendChild(body); host.appendChild(cap);
    if (cfg.render) cfg.render(body, host);

    var root = cfg.root ? $(cfg.root) : document;
    function clear() {
      $$('.step-on', root).forEach(function (n) { n.classList.remove('step-on'); });
      $$('tr.hit,tr.src', root).forEach(function (n) { n.classList.remove('hit', 'src'); });
    }
    function show(k) {
      clear();
      i = k;
      if (k < 0) { cap.textContent = cfg.hint || '按「下一步」开始 —— 一步一步看它到底做了什么。'; }
      else {
        var st = steps[k];
        (st.on ? $$(st.on, root) : []).forEach(function (n) { n.classList.add('step-on'); });
        if (st.do) st.do(root);
        cap.textContent = st.cap || '';
      }
      cnt.textContent = (i + 1 > steps.length ? steps.length : (i < 0 ? 0 : i + 1)) + ' / ' + steps.length;
      bPrev.disabled = i < 0; bNext.disabled = i >= steps.length - 1;
    }
    bNext.onclick = function () { stop(); show(Math.min(i + 1, steps.length - 1)); };
    bPrev.onclick = function () { stop(); show(Math.max(i - 1, -1)); };
    bReset.onclick = function () { stop(); show(-1); };
    function stop() { if (timer) { clearInterval(timer); timer = null; bPlay.textContent = '自动播放'; } }
    bPlay.onclick = function () {
      if (timer) { stop(); return; }
      bPlay.textContent = '暂停';
      if (i >= steps.length - 1) show(-1);
      timer = setInterval(function () {
        if (i >= steps.length - 1) { stop(); return; }
        show(i + 1);
      }, cfg.interval || 1500);
    };
    show(-1);
    return { show: show, stop: stop };
  }

  /* ══ 配对流动（招牌动效）═════════════════════════════════
     一个值沿手绘连线从 A 走到 B。JOIN 的机制本身就是这个动作。
     Lab.wire(container, fromEl, toEl, {text:'7', onArrive:fn}) → Promise */
  function wire(container, from, to, opts) {
    if (typeof container === 'string') container = $(container);
    from = typeof from === 'string' ? $(from) : from;
    to = typeof to === 'string' ? $(to) : to;
    opts = opts || {};
    return new Promise(function (resolve) {
      if (!container || !from || !to) { resolve(); return; }
      var c = container.getBoundingClientRect();
      var a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
      var x1 = a.right - c.left, y1 = a.top - c.top + a.height / 2;
      var x2 = b.left - c.left, y2 = b.top - c.top + b.height / 2;

      var s = $('svg.wire', container);
      if (!s) { s = svg('svg', { class: 'wire' }); container.appendChild(s); }
      /* 同一行内配对时让连线**拱过**中间那些格子 ——
         直线会从数据上碾过去，令牌也跟着压在数字上（实测过，很难看）。 */
      var flat = Math.abs(y2 - y1) < 10;
      var bow = flat ? (opts.bow == null ? 44 : opts.bow) : 0;
      var dx = (x2 - x1) * 0.5;
      var p = svg('path', { d: 'M' + x1 + ' ' + y1 + ' C' + (x1 + dx) + ' ' + (y1 - bow) + ',' +
                                (x2 - dx) + ' ' + (y2 - bow) + ',' + x2 + ' ' + y2 });
      s.appendChild(p);

      /* 令牌自己的中心钉在路径点上：先 left/top 定位到起点，再用 transform 走 */
      var tok = el('div', 'token', opts.text == null ? '' : opts.text);
      container.appendChild(tok);
      tok.style.left = x1 + 'px'; tok.style.top = y1 + 'px';
      function put(px, py) {
        tok.style.transform = 'translate(' + (px - x1) + 'px,' + (py - y1) + 'px) translate(-50%,-50%)';
      }
      put(x1, y1);

      from.classList.add('src');
      var len = 0; try { len = p.getTotalLength(); } catch (e) { len = 0; }
      var dur = opts.dur || 620, t0 = null;
      function arrive() {
        to.classList.add('hit');
        if (opts.onArrive) opts.onArrive();
      }
      if (REDUCED || !len) {
        put(x2, y2); arrive();
        setTimeout(function () { resolve(); }, 60); return;
      }
      p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
      p.style.transition = 'stroke-dashoffset ' + dur + 'ms cubic-bezier(.16,1,.3,1)';
      requestAnimationFrame(function () { p.style.strokeDashoffset = 0; });

      function frame(ts) {
        if (t0 == null) t0 = ts;
        var k = Math.min(1, (ts - t0) / dur);
        var e = 1 - Math.pow(1 - k, 3);          /* 与 CSS 同族的减速 */
        var pt = p.getPointAtLength(len * e);
        put(pt.x, pt.y);
        if (k < 1) requestAnimationFrame(frame);
        else {
          arrive();
          if (opts.keep === true) {
            /* 停在连线最高点，而不是压在目标格子的数字上 */
            var mid = p.getPointAtLength(len * 0.5);
            tok.style.transition = 'transform 320ms cubic-bezier(.16,1,.3,1)';
            put(mid.x, mid.y);
          } else {
            tok.style.transition = 'opacity 260ms linear';
            tok.style.opacity = '0';
          }
          resolve();
        }
      }
      requestAnimationFrame(frame);
    });
  }

  function ink(node) {
    node = typeof node === 'string' ? $(node) : node;
    if (!node || REDUCED) return;
    node.classList.remove('ink-in'); void node.offsetWidth; node.classList.add('ink-in');
  }

  /* ══ 自动接管：不用写一行 JS 的声明式用法 ═══════════════
     <div data-mm="mmA"></div>          ← 找 window.MM_DATA.mmA 渲染
     <div data-rail="railA"></div>      ← 找 window.MM_DATA.railA
     <div data-mindmap-global></div>    ← 渲染全局总图（来自 _全局进度.js） */
  function initAll(scope) {
    scope = scope || document;
    var D = global.MM_DATA || {};
    $$('[data-mm]', scope).forEach(function (n) {
      var spec = D[n.getAttribute('data-mm')];
      if (spec) mindmap(n, spec, { vertical: n.hasAttribute('data-vertical') ? true : 'auto',
                                   label: n.getAttribute('aria-label') || '思维导图' });
    });
    $$('[data-rail]', scope).forEach(function (n) {
      var spec = D[n.getAttribute('data-rail')];
      if (spec) rail(n, spec);
    });
    $$('[data-global-map]', scope).forEach(function (n) {
      if (global.LabProgress) mindmap(n, global.LabProgress.tree(), { vertical: 'auto' });
    });
    $$('[data-global-rail]', scope).forEach(function (n) {
      if (global.LabProgress) rail(n, global.LabProgress.railSpec());
    });
  }
  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }
  ready(function () { initAll(); });

  /* 窄屏切横向/纵向：只在跨过断点时重排，不抖动 */
  var lastV = null;
  global.addEventListener('resize', debounce(function () {
    var narrow = document.documentElement.clientWidth < 620;
    if (lastV === narrow) return; lastV = narrow;
    initAll();
  }, 220));
  function debounce(fn, ms) {
    var t; return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  global.Lab = { mindmap: mindmap, rail: rail, player: player, wire: wire,
                 ink: ink, drawIn: drawIn, store: store, initAll: initAll,
                 textW: textW, $: $, $$: $$, el: el, svg: svg, reduced: REDUCED };
})(window);
