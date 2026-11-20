'use strict';
/* Connect Four agents in JavaScript: ports of the Python agents.
   Board: Int8Array(42), row-major, row 0 = top. Players: +1 (Yellow, first) and -1 (Red). */
const ROWS = 6, COLS = 7;
const DIRS = [[0, 1], [1, 0], [1, 1], [1, -1]];

function validMoves(b) { const m = []; for (let c = 0; c < COLS; c++) if (b[c] === 0) m.push(c); return m; }
function dropRow(b, c) { for (let r = ROWS - 1; r >= 0; r--) if (b[r * COLS + c] === 0) return r; return -1; }
function play(b, c, p) { const r = dropRow(b, c); b[r * COLS + c] = p; return r; }

/* cells of a winning four through (r,c), or null */
function winCells(b, r, c, p) {
  for (const [dr, dc] of DIRS) {
    const cells = [[r, c]];
    for (const s of [1, -1]) {
      let rr = r + dr * s, cc = c + dc * s;
      while (rr >= 0 && rr < ROWS && cc >= 0 && cc < COLS && b[rr * COLS + cc] === p) {
        cells.push([rr, cc]); rr += dr * s; cc += dc * s;
      }
    }
    if (cells.length >= 4) return cells;
  }
  return null;
}
function hasWin(b, p) {
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    if (b[r * COLS + c] !== p) continue;
    for (const [dr, dc] of DIRS) {
      let n = 0;
      for (let i = 0; i < 4; i++) {
        const rr = r + dr * i, cc = c + dc * i;
        if (rr >= 0 && rr < ROWS && cc >= 0 && cc < COLS && b[rr * COLS + cc] === p) n++;
      }
      if (n === 4) return true;
    }
  }
  return false;
}

/* ---------- Minimax / Alpha-Beta (same heuristic as the Python code) ---------- */
const WSCORE = [0, 1, 10, 50, 100];
function evaluate(b, p) {
  let s = 0;
  for (let r = 0; r < ROWS; r++) if (b[r * COLS + 3] === p) s += 3;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) for (const [dr, dc] of DIRS) {
    let own = 0, opp = 0, n = 0;
    for (let i = 0; i < 4; i++) {
      const rr = r + dr * i, cc = c + dc * i;
      if (rr >= 0 && rr < ROWS && cc >= 0 && cc < COLS) { n++; const v = b[rr * COLS + cc]; if (v === p) own++; else if (v === -p) opp++; }
    }
    if (n === 4) { if (opp === 0) s += WSCORE[own]; if (own === 0) s -= WSCORE[opp]; }
  }
  return s;
}
function search(b, depth, maximizing, p, alpha, beta, prune) {
  const mv = validMoves(b);
  if (hasWin(b, p)) return 100000 + depth;
  if (hasWin(b, -p)) return -100000 - depth;
  if (depth === 0 || mv.length === 0) return evaluate(b, p);
  let v = maximizing ? -Infinity : Infinity;
  for (const c of mv) {
    const nb = b.slice(); play(nb, c, maximizing ? p : -p);
    const s = search(nb, depth - 1, !maximizing, p, alpha, beta, prune);
    if (maximizing) { v = Math.max(v, s); alpha = Math.max(alpha, v); } else { v = Math.min(v, s); beta = Math.min(beta, v); }
    if (prune && alpha >= beta) break;
  }
  return v;
}
function minimaxMove(b, p, depth, prune) {
  const mv = validMoves(b); if (!mv.length) return null;
  let best = -Infinity, bm = mv[0], alpha = -Infinity;
  for (const c of mv) {
    const nb = b.slice(); play(nb, c, p);
    const s = search(nb, depth - 1, false, p, alpha, Infinity, prune);
    if (s > best) { best = s; bm = c; }
    if (prune) alpha = Math.max(alpha, best);
  }
  return bm;
}

/* ---------- Random ---------- */
function randomMove(b) { const m = validMoves(b); return m.length ? m[Math.floor(Math.random() * m.length)] : null; }

/* ---------- Standard MCTS (UCB1 + random rollouts) ---------- */
function mctsMove(b0, p0, sims) {
  const mv0 = validMoves(b0); if (!mv0.length) return null;
  const mk = (board, player, parent, move) => ({ board, player, parent, move, pjm: parent ? -player : null, children: [], visits: 0, wins: 0, untried: validMoves(board) });
  const root = mk(b0.slice(), p0, null, null);
  for (let i = 0; i < sims; i++) {
    let node = root;
    while (node.untried.length === 0 && node.children.length) {
      let best = null, bs = -Infinity;
      for (const ch of node.children) {
        const s = ch.wins / ch.visits + Math.sqrt(2 * Math.log(node.visits) / ch.visits);
        if (s > bs) { bs = s; best = ch; }
      }
      node = best;
    }
    if (node.untried.length) {
      const k = Math.floor(Math.random() * node.untried.length);
      const move = node.untried.splice(k, 1)[0];
      const nb = node.board.slice(); play(nb, move, node.player);
      const ch = mk(nb, -node.player, node, move);
      node.children.push(ch); node = ch;
    }
    const prev = -node.player;
    let winner;
    if (hasWin(node.board, prev)) winner = prev;
    else if (node.untried.length === 0) winner = 0;
    else {
      const rb = node.board.slice(); let pl = node.player; winner = 0;
      for (;;) {
        const m = validMoves(rb); if (!m.length) { winner = 0; break; }
        const c = m[Math.floor(Math.random() * m.length)];
        const r = play(rb, c, pl);
        if (winCells(rb, r, c, pl)) { winner = pl; break; }
        pl = -pl;
      }
    }
    for (let n = node; n; n = n.parent) {
      n.visits++;
      if (n.pjm !== null) { if (winner === n.pjm) n.wins += 1; else if (winner === 0) n.wins += 0.5; }
    }
  }
  if (!root.children.length) return null;
  let bc = root.children[0];
  for (const ch of root.children) if (ch.visits > bc.visits) bc = ch;
  return bc.move;
}

/* ---------- CNN forward pass (same architecture as AlphaZeroCNN) ---------- */
const HW = 42;
class Net {
  constructor(w) {
    this.w = {};
    for (const k in w) this.w[k] = Float32Array.from(w[k]);
  }
  conv3(inp, cin, wk, bk, cout) {
    const W = this.w[wk], B = this.w[bk], out = new Float32Array(cout * HW);
    for (let co = 0; co < cout; co++) {
      const o = co * HW; out.fill(B[co], o, o + HW);
      for (let ci = 0; ci < cin; ci++) {
        const ib = ci * HW, wb = (co * cin + ci) * 9;
        for (let kh = 0; kh < 3; kh++) {
          const h0 = Math.max(0, 1 - kh), h1 = Math.min(5, 6 - kh);
          for (let kw = 0; kw < 3; kw++) {
            const wv = W[wb + kh * 3 + kw]; if (wv === 0) continue;
            const x0 = Math.max(0, 1 - kw), x1 = Math.min(6, 7 - kw);
            for (let h = h0; h <= h1; h++) {
              const orow = o + h * 7, irow = ib + (h + kh - 1) * 7 + kw - 1;
              for (let x = x0; x <= x1; x++) out[orow + x] += wv * inp[irow + x];
            }
          }
        }
      }
      for (let i = o; i < o + HW; i++) if (out[i] < 0) out[i] = 0;
    }
    return out;
  }
  conv1(inp, cin, wk, bk, cout) {
    const W = this.w[wk], B = this.w[bk], out = new Float32Array(cout * HW);
    for (let co = 0; co < cout; co++) {
      const o = co * HW; out.fill(B[co], o, o + HW);
      for (let ci = 0; ci < cin; ci++) {
        const wv = W[co * cin + ci], ib = ci * HW;
        for (let i = 0; i < HW; i++) out[o + i] += wv * inp[ib + i];
      }
      for (let i = o; i < o + HW; i++) if (out[i] < 0) out[i] = 0;
    }
    return out;
  }
  fc(inp, wk, bk, nout, relu) {
    const W = this.w[wk], B = this.w[bk], nin = inp.length, out = new Float32Array(nout);
    for (let j = 0; j < nout; j++) {
      let s = B[j]; const wb = j * nin;
      for (let i = 0; i < nin; i++) s += W[wb + i] * inp[i];
      out[j] = relu && s < 0 ? 0 : s;
    }
    return out;
  }
  /* state: Float32Array(42) = board * player. returns {logits[7], value} */
  forward(state) {
    let x = this.conv3(state, 1, 'conv1.weight', 'conv1.bias', 64);
    x = this.conv3(x, 64, 'conv2.weight', 'conv2.bias', 128);
    x = this.conv3(x, 128, 'conv3.weight', 'conv3.bias', 128);
    const p = this.conv1(x, 128, 'policy_conv.weight', 'policy_conv.bias', 32);
    const logits = this.fc(p, 'policy_fc.weight', 'policy_fc.bias', 7, false);
    const v = this.conv1(x, 128, 'value_conv.weight', 'value_conv.bias', 32);
    const h = this.fc(v, 'value_fc1.weight', 'value_fc1.bias', 128, true);
    const o = this.fc(h, 'value_fc2.weight', 'value_fc2.bias', 1, false);
    return { logits, value: Math.tanh(o[0]) };
  }
}

/* ---------- Neural MCTS (PUCT) ---------- */
function neuralMove(net, b0, p0, sims, cpuct = 1.5) {
  const mv0 = validMoves(b0); if (!mv0.length) return null;
  const toState = (b, p) => { const s = new Float32Array(HW); for (let i = 0; i < HW; i++) s[i] = b[i] * p; return s; };
  const mk = (board, player, prior, parent, move) => ({ board, player, prior, parent, move, children: [], visits: 0, vsum: 0 });
  function expand(node, out) {
    const mv = validMoves(node.board); if (!mv.length) return;
    const lg = out.logits; let mx = -Infinity;
    for (let i = 0; i < 7; i++) if (lg[i] > mx) mx = lg[i];
    const e = Array.from(lg, v => Math.exp(v - mx)); const tot = e.reduce((a, c) => a + c, 0);
    let ps = mv.map(m => e[m] / tot); const s = ps.reduce((a, c) => a + c, 0);
    ps = s <= 0 ? mv.map(() => 1 / mv.length) : ps.map(v => v / s);
    mv.forEach((m, i) => { const nb = node.board.slice(); play(nb, m, node.player); node.children.push(mk(nb, -node.player, ps[i], node, m)); });
  }
  const root = mk(b0.slice(), p0, 1, null, null);
  expand(root, net.forward(toState(root.board, root.player)));
  for (let i = 0; i < sims; i++) {
    let node = root;
    while (node.children.length) {
      let best = null, bs = -Infinity;
      for (const ch of node.children) {
        const q = ch.visits === 0 ? 0 : -(ch.vsum / ch.visits);
        const s = q + cpuct * ch.prior * Math.sqrt(node.visits + 1) / (1 + ch.visits);
        if (s > bs) { bs = s; best = ch; }
      }
      node = best;
    }
    let value;
    if (hasWin(node.board, -node.player)) value = -1;
    else if (validMoves(node.board).length === 0) value = 0;
    else { const out = net.forward(toState(node.board, node.player)); value = out.value; expand(node, out); }
    for (let n = node; n; n = n.parent) { n.visits++; n.vsum += value; value = -value; }
  }
  if (!root.children.length) return null;
  let bc = root.children[0];
  for (const ch of root.children) if (ch.visits > bc.visits) bc = ch;
  return bc.move;
}

/* ---------- Web Worker entry ---------- */
const LEVELS = { Easy: [2, 50], Medium: [3, 100], Hard: [4, 200] };
let NET = null;
function chooseMove(agent, level, board, player) {
  const [depth, sims] = LEVELS[level] || LEVELS.Medium;
  const b = Int8Array.from(board);
  switch (agent) {
    case 'random': return randomMove(b);
    case 'minimax': return minimaxMove(b, player, depth, false);
    case 'alphabeta': return minimaxMove(b, player, depth + 1, true);
    case 'mcts': return mctsMove(b, player, sims);
    case 'neural': return neuralMove(NET, b, player, sims);
  }
  return randomMove(b);
}
if (typeof WorkerGlobalScope !== 'undefined' && typeof self !== 'undefined' && self instanceof WorkerGlobalScope) {
  self.onmessage = async (e) => {
    const m = e.data;
    if (m.type === 'init') {
      try { const r = await fetch(m.url); if (!r.ok) throw new Error('no model'); NET = new Net(await r.json()); self.postMessage({ type: 'ready', ok: true }); }
      catch (err) { self.postMessage({ type: 'ready', ok: false }); }
    } else if (m.type === 'move') {
      const t0 = performance.now();
      const move = chooseMove(m.agent, m.level, m.board, m.player);
      self.postMessage({ type: 'move', move, token: m.token, ms: Math.round(performance.now() - t0) });
    }
  };
}
if (typeof module !== 'undefined') module.exports = { Net, validMoves, play, hasWin, winCells, minimaxMove, mctsMove, neuralMove, randomMove, chooseMove, setNet: n => { NET = n; } };
