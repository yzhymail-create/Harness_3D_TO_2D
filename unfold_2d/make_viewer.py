#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成仪表线束 2D 展开网页查看器（单文件 HTML，内嵌 layout.json，SVG 渲染，无 CDN）。
用法：python3 make_viewer.py <layout.json> <out.html>
2026-11-17 手机端修复：初始适配按可见视口铺满（100dvh + 底部导航预留 64px，
viewBox 边距约 8%）、窄屏图例改顶部可折叠（默认收起）、标签加白晕 + 放大时变大。
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unfold_2d_v3 import (seg_proper_intersect, seg_collinear_overlap,
                          seg_seg_dist, pt_eq)

TYPE_CN = {'connector': '连接器', 'clamp': '卡扣', 'fork': '分支点', 'joint': '接头'}
TYPE_COL = {'connector': '#e03131', 'clamp': '#2f9e44', 'fork': '#f08c00', 'joint': '#868e96'}

def main():
    lj_path, out_path = sys.argv[1], sys.argv[2]
    d = json.load(open(lj_path, encoding='utf-8'))
    stats = d['stats']
    branches, nodes = d['branches'], d['nodes']
    bends, warnings = d['bends'], d['warnings']
    xmin, ymin, xmax, ymax = stats['bbox']
    # 边距：约 8%（各边取总尺寸的 4%），初始适配时图占满视口约 92%
    M = round(0.04 * max(xmax - xmin, ymax - ymin), 1)
    # SVG 坐标：X = x，Y = -y（y 轴翻转）
    vb_x, vb_y = xmin - M, -ymax - M
    vb_w, vb_h = (xmax - xmin) + 2*M, (ymax - ymin) + 2*M

    def Y(y):
        return -y

    # ---- 静态 SVG 内容（Python 生成，便于离线核对元素数） ----
    parts = []
    # 管子折线
    for b in branches:
        pts = ' '.join(f"{x:.2f},{Y(y):.2f}" for x, y in b['points'])
        parts.append(
            f'<polyline class="tube" data-key="{b["key"]}" points="{pts}" '
            f'fill="none" stroke="#2c5f8a" stroke-width="1.6" stroke-linejoin="round" '
            f'stroke-linecap="round"><title>{b["key"]} Φ{b["dia"]} L={b["len_3d"]}</title></polyline>')
    # 节点圆 + 编号
    for n in nodes:
        c = TYPE_COL.get(n['type'], '#000')
        parts.append(
            f'<g class="node" data-code="{n["code"]}">'
            f'<circle class="ndot" cx="{n["x"]:.2f}" cy="{Y(n["y"]):.2f}" r="4.2" fill="{c}" '
            f'stroke="#fff" stroke-width="1.2"/>'
            f'<circle class="nhit" cx="{n["x"]:.2f}" cy="{Y(n["y"]):.2f}" r="12" fill="transparent"/>'
            f'<text class="lbl" x="{n["x"] + 6:.2f}" y="{Y(n["y"]) + 3:.2f}" fill="{c}">{n["code"]}</text>'
            f'</g>')
    # X 交叉点标记（v4 新增：红色 ✕，臂长 ±5mm；title 显示相交的两根分支）
    for x in d.get('crossings', []):
        cx, cy = x['x'], Y(x['y'])
        pair = ' × '.join(x.get('branches', []))
        parts.append(
            f'<g class="xmark"><title>X 交叉：{pair}</title>'
            f'<line class="xline" x1="{cx - 5:.2f}" y1="{cy - 5:.2f}" '
            f'x2="{cx + 5:.2f}" y2="{cy + 5:.2f}" stroke="#e03131" stroke-width="2.0" '
            f'stroke-linecap="round"/>'
            f'<line class="xline" x1="{cx - 5:.2f}" y1="{cy + 5:.2f}" '
            f'x2="{cx + 5:.2f}" y2="{cy - 5:.2f}" stroke="#e03131" stroke-width="2.0" '
            f'stroke-linecap="round"/></g>')
    svg_inner = '\n'.join(parts)

    # 节点连接关系（供弹窗用）
    node_branches = {}
    for b in branches:
        for code in (b['node0'], b['node1']):
            node_branches.setdefault(code, []).append(b['key'])

    data_json = json.dumps({
        'stats': stats, 'branches': branches, 'nodes': nodes,
        'bends': bends, 'warnings': warnings,
        'node_branches': node_branches,
        'checklist': d.get('checklist'),
        'crossings': d.get('crossings', []),
        'trunk': d.get('meta', {}).get('trunk'),
        'tilt_deg': d.get('meta', {}).get('tilt_deg'),
        'version': d.get('meta', {}).get('version', 'v3'),
    }, ensure_ascii=False).replace('<', '\\u003c')

    n_seg = sum(len(b['pieces']) for b in branches)
    total_len = stats['total_len_3d']
    w_mm = round(xmax - xmin, 1)
    h_mm = round(ymax - ymin, 1)
    # 干涉分类（从 layout.json 几何重算，不硬编码）
    subs = []  # (p1, p2, branch, seg, skip_dist)
    for b in branches:
        for pc in b['pieces']:
            pts = pc['pts']
            sd = (pc['na'] == pc['nb'])  # 自环三角不计间距
            for a, c in zip(pts, pts[1:]):
                subs.append((tuple(a), tuple(c), b['key'], pc['seg'], sd))
    n_x = n_near = n_ov = 0
    for i in range(len(subs)):
        for j in range(i + 1, len(subs)):
            if subs[i][2] == subs[j][2] and subs[i][3] == subs[j][3]:
                continue
            a1, a2, b1, b2 = subs[i][0], subs[i][1], subs[j][0], subs[j][1]
            shared = (pt_eq(a1, b1) or pt_eq(a1, b2)
                      or pt_eq(a2, b1) or pt_eq(a2, b2))
            if seg_proper_intersect(a1, a2, b1, b2):
                n_x += 1
            elif seg_collinear_overlap(a1, a2, b1, b2):
                n_ov += 1
            elif (not shared and not (subs[i][4] or subs[j][4])
                    and seg_seg_dist(a1, a2, b1, b2) < 5.0):
                n_near += 1

    # ---- 检查清单（v3 修正版 layout.json 才有；旧版 layout.json 无则不显示） ----
    ck = d.get('checklist')
    ck_header = ''   # 顶部统计区第二行（手机也可见）
    ck_verify = ''   # 右下验证信息区一行
    if ck:
        hard = ck.get('hard', [])
        n_pass = sum(1 for c in hard if c.get('pass'))
        tc = stats.get('trunk_center', {})
        h1 = next((c for c in hard if c.get('id') == 'H1'), None)
        h1_mark = '✓' if (h1 and h1.get('pass')) else '✗'
        all_mark = '✓' if ck.get('all_hard_pass') else '✗'
        # v4：主干居中横竖两方向分别显示；v3 旧版只有单值，兼容回退
        if tc.get('dev_x_pct') is not None:
            dev_txt = (f"横 {tc['dev_x_mm']} mm（{tc['dev_x_pct']}%）/ "
                       f"竖 {tc['dev_y_mm']} mm（{tc['dev_y_pct']}%）")
        else:
            dev_txt = f"{tc.get('dev_mm')} mm（{tc.get('dev_pct')}%）"
        ck_header = (f'<div class="stats">主干居中偏差 <b>{dev_txt}</b> {h1_mark} '
                     f'· 硬规则 <b>{n_pass}/{len(hard)} 通过</b> {all_mark} '
                     f'· 压着画 <b>{n_ov} 对</b> · X 交叉 <b>{n_x} 对</b>（红 ✕ 标记）</div>')
        # v4 第三行：正交符合率 + 翻转统计（v3 layout.json 无此字段则不显示）
        if stats.get('ortho_rate_pct') is not None:
            ck_header += (
                f'<div class="stats">正交符合率 <b>{stats["ortho_rate_pct"]}%</b> '
                f'（{stats["ortho_passed"]}/{stats["ortho_checked"]} 根） '
                f'· 翻转 放置 {stats.get("flips_placement", 0)} / '
                f'居中 {stats.get("flips_center", 0)} / '
                f'消交叉 {stats.get("flips_untangle", 0)} '
                f'· 投影侧符合 {stats.get("side_match", 0)}/{stats.get("side_total", 0)}</div>')
        ck_verify = (f'<br>主干居中偏差 {dev_txt}{h1_mark} · '
                     f'硬规则 {n_pass}/{len(hard)} 通过 {all_mark}')

    html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>仪表线束 2D展开图 v4（2026-11-17）</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f1f3f5; color: #212529; height: 100vh; height: -webkit-fill-available; height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }}
header {{ background: #1c3d5a; color: #fff; padding: 8px 12px; flex: none; }}
header h1 {{ font-size: 16px; font-weight: 600; }}
.stats {{ font-size: 12px; color: #ced4da; margin-top: 2px; line-height: 1.5; }}
.stats b {{ color: #fff; }}
.bar {{ display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }}
.bar input {{ flex: 1 1 140px; padding: 6px 8px; font-size: 14px; border: none; border-radius: 4px; }}
.bar button {{ padding: 6px 10px; font-size: 13px; border: none; border-radius: 4px; background: #2c5f8a; color: #fff; cursor: pointer; }}
.bar button:active {{ background: #1f4566; }}
#wrap {{ flex: 1; position: relative; overflow: hidden; background: #fff; }}
#svg {{ width: 100%; height: 100%; display: block; touch-action: none; cursor: grab; }}
#svg.dragging {{ cursor: grabbing; }}
.tube {{ cursor: pointer; }}
.tube.sel {{ stroke: #f08c00 !important; stroke-width: 3.2 !important; }}
.node.sel .ndot {{ stroke: #f08c00; stroke-width: 3; }}
.node.hl .ndot {{ stroke: #ffd43b; stroke-width: 3; }}
.lbl {{ font-size: 14px; font-weight: 600; pointer-events: none; user-select: none; paint-order: stroke; stroke: rgba(255,255,255,.9); }}
.legend {{ position: absolute; left: 8px; bottom: 8px; bottom: calc(8px + env(safe-area-inset-bottom, 0px)); background: rgba(255,255,255,.92); border: 1px solid #dee2e6; border-radius: 6px; padding: 6px 9px; font-size: 12px; line-height: 1.7; color: #495057; z-index: 4; }}
#legendToggle {{ display: none; border: none; background: none; font-size: 13px; color: #495057; cursor: pointer; padding: 2px 4px; }}
.legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
.legend .ln {{ display: inline-block; width: 16px; height: 0; border-top: 2px solid #2c5f8a; margin-right: 5px; vertical-align: middle; }}
#popup {{ position: absolute; left: 8px; right: 8px; bottom: 8px; bottom: calc(8px + env(safe-area-inset-bottom, 0px)); background: #fff; border: 1px solid #adb5bd; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,.18); padding: 10px 12px; font-size: 13px; line-height: 1.65; display: none; max-height: 45%; overflow-y: auto; z-index: 5; }}
#popup h2 {{ font-size: 14px; margin-bottom: 2px; }}
#popup .x {{ float: right; border: none; background: none; font-size: 18px; color: #868e96; cursor: pointer; line-height: 1; }}
#popup table {{ border-collapse: collapse; }}
#popup td {{ padding: 1px 8px 1px 0; vertical-align: top; }}
#popup td.k {{ color: #868e96; white-space: nowrap; }}
#popup .mono {{ font-family: monospace; word-break: break-all; }}
#toast {{ position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: #343a40; color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; display: none; z-index: 6; }}
#verify {{ position: absolute; right: 8px; bottom: 8px; bottom: calc(8px + env(safe-area-inset-bottom, 0px)); background: rgba(255,255,255,.92); border: 1px solid #dee2e6; border-radius: 6px; padding: 6px 9px; font-size: 11px; color: #868e96; text-align: right; line-height: 1.6; }}
@media (max-width: 640px) {{
  #verify {{ display: none; }}
  header h1 {{ font-size: 14px; }}
  /* 窄屏：#wrap 底部预留 Muse 底部导航高度，SVG 适配框 = 实际可见区 */
  #wrap {{ padding-bottom: 64px; padding-bottom: calc(64px + env(safe-area-inset-bottom, 0px)); }}
  /* 窄屏：图例移到顶部，可折叠，默认收起，绝不贴底被导航遮住 */
  .legend {{ top: 8px; bottom: auto; padding: 4px 8px; }}
  #legendToggle {{ display: inline-block; }}
  .legend-body {{ display: none; }}
  .legend.open .legend-body {{ display: block; }}
  .legend.open #legendToggle {{ margin-bottom: 2px; }}
  /* 窄屏：详情弹窗抬起，避开底部导航 */
  #popup {{ bottom: 72px; bottom: calc(72px + env(safe-area-inset-bottom, 0px)); max-height: 38%; }}
}}
</style>
</head>
<body>
<header>
<h1>仪表线束（IP-Harness）2D 展开图 · v4</h1>
<div class="stats">分支 <b>{stats['branches_placed']}/{stats['branches_total']}</b> · 节点 <b>{stats['nodes_placed']}/{stats['nodes_total']}</b> · 线段 <b>{n_seg}</b> · 展开总长 <b>{total_len:.1f} mm</b> · 图纸 <b>{w_mm} × {h_mm} mm</b></div>
{ck_header}
<div class="bar">
<input id="search" type="text" placeholder="搜编号，如 CON01 / CLP01 / BN02 / Body.123" autocomplete="off">
<button id="btnSearch">定位</button>
<button id="btnFit">全图</button>
<button id="btnClear">清除</button>
</div>
</header>
<div id="wrap">
<svg id="svg" viewBox="{vb_x:.1f} {vb_y:.1f} {vb_w:.1f} {vb_h:.1f}" preserveAspectRatio="xMidYMid meet">
<g id="vp">
{svg_inner}
</g>
</svg>
<div class="legend" id="legend"><button id="legendToggle" type="button">图例 ▸</button><div class="legend-body"><span class="ln"></span>管子（分支）<br><i style="background:#e03131"></i>连接器 <i style="background:#2f9e44"></i>卡扣 <i style="background:#f08c00"></i>分支点 <i style="background:#868e96"></i>接头<br><span style="color:#e03131;font-weight:700">✕</span> X 交叉点</div></div>
<div id="verify">拐弯 {stats['bends']} 次 · 残留干涉 {stats['residual_interference_pairs']} 对<br>（X 交叉 {n_x} 对 · 间距&lt;5mm {n_near} 对 · 压着画 {n_ov} 对）<br>最大长度误差 {stats['max_len_err_mm']} mm · 无真实几何环{ck_verify}</div>
<div id="popup"><button class="x" id="btnClose">×</button><div id="popBody"></div></div>
<div id="toast"></div>
</div>
<script>
var DATA = {data_json};
var TYPE_CN = {{"connector":"连接器","clamp":"卡扣","fork":"分支点","joint":"接头"}};
var svg = document.getElementById('svg');
var vp = document.getElementById('vp');
var popup = document.getElementById('popup');
var popBody = document.getElementById('popBody');
var toastEl = document.getElementById('toast');
var nodesByCode = {{}};
DATA.nodes.forEach(function(n) {{ nodesByCode[n.code] = n; }});
var branchesByKey = {{}};
DATA.branches.forEach(function(b) {{ branchesByKey[b.key] = b; }});

// ---- 视图变换（平移 + 缩放） ----
var view = {{ x: 0, y: 0, k: 1 }};
function applyView() {{
  vp.setAttribute('transform', 'translate(' + view.x + ',' + view.y + ') scale(' + view.k + ')');
  // 标签：基础 14（mm 单位），随放大适度变大（√k，上限 2 倍），放大后可读；白晕描边提可读性
  var grow = Math.min(2, Math.sqrt(view.k));
  var fs = 14 * grow / view.k;
  var sw = 1.6 / view.k;
  var dots = document.querySelectorAll('.ndot');
  for (var i = 0; i < dots.length; i++) {{ dots[i].setAttribute('r', 5.0 / view.k); dots[i].setAttribute('stroke-width', 1.2 / view.k); }}
  var lbls = document.querySelectorAll('.lbl');
  for (var j = 0; j < lbls.length; j++) {{ lbls[j].style.fontSize = fs + 'px'; lbls[j].style.strokeWidth = (2.5 * grow / view.k) + 'px'; }}
  var tubes = document.querySelectorAll('.tube');
  for (var t = 0; t < tubes.length; t++) {{ if (!tubes[t].classList.contains('sel')) tubes[t].setAttribute('stroke-width', sw); }}
  var xlines = document.querySelectorAll('.xline');
  for (var m = 0; m < xlines.length; m++) {{ xlines[m].setAttribute('stroke-width', (2.0 / view.k)); }}
}}
function svgPoint(cx, cy) {{
  var pt = svg.createSVGPoint();
  pt.x = cx; pt.y = cy;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}}
function zoomAt(cx, cy, factor) {{
  var p = svgPoint(cx, cy);
  var k2 = Math.max(0.15, Math.min(40, view.k * factor));
  var f = k2 / view.k;
  view.x = p.x - (p.x - view.x) * f;
  view.y = p.y - (p.y - view.y) * f;
  view.k = k2;
  applyView();
}}
function centerOn(x, y, k) {{
  if (k) view.k = k;
  applyView();
  var r = svg.getBoundingClientRect();
  var pt = svg.createSVGPoint(); pt.x = r.width / 2; pt.y = r.height / 2;
  var c = pt.matrixTransform(svg.getScreenCTM().inverse());
  // c 为屏幕中心对应的 viewBox 点；要让图上点 (x,y) 落到屏幕中心：
  // x*k + t = c，故 t = c - x*k（直接赋值，一步到位）
  view.x = c.x - x * view.k;
  view.y = c.y - y * view.k;
  applyView();
}}
function fitAll() {{ view = {{ x: 0, y: 0, k: 1 }}; applyView(); }}

// ---- 指针交互：拖动 / 缩放 / 点按 ----
var pointers = {{}};
var pinchDist = 0, pinchMid = null;
var downX = 0, downY = 0, downT = 0, moved = false, dragging = false;
svg.addEventListener('pointerdown', function(e) {{
  svg.setPointerCapture(e.pointerId);
  pointers[e.pointerId] = {{ x: e.clientX, y: e.clientY }};
  var ids = Object.keys(pointers);
  if (ids.length === 1) {{
    downX = e.clientX; downY = e.clientY; downT = Date.now(); moved = false; dragging = true;
    svg.classList.add('dragging');
  }} else if (ids.length === 2) {{
    dragging = false;
    var a = pointers[ids[0]], b = pointers[ids[1]];
    pinchDist = Math.hypot(a.x - b.x, a.y - b.y);
    pinchMid = {{ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }};
  }}
  e.preventDefault();
}});
svg.addEventListener('pointermove', function(e) {{
  if (!pointers[e.pointerId]) return;
  var prev = pointers[e.pointerId];
  pointers[e.pointerId] = {{ x: e.clientX, y: e.clientY }};
  var ids = Object.keys(pointers);
  if (ids.length === 2) {{
    var a = pointers[ids[0]], b = pointers[ids[1]];
    var d = Math.hypot(a.x - b.x, a.y - b.y);
    var mid = {{ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }};
    if (pinchDist > 0) {{
      zoomAt(mid.x, mid.y, d / pinchDist);
      var p0 = svgPoint(pinchMid.x, pinchMid.y);
      var p1 = svgPoint(mid.x, mid.y);
      view.x += (p1.x - p0.x); view.y += (p1.y - p0.y);
      applyView();
    }}
    pinchDist = d; pinchMid = mid;
    moved = true;
  }} else if (dragging) {{
    var dx = e.clientX - downX, dy = e.clientY - downY;
    if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
    if (moved) {{
      var p0 = svgPoint(prev.x, prev.y);
      var p1 = svgPoint(e.clientX, e.clientY);
      view.x += (p1.x - p0.x); view.y += (p1.y - p0.y);
      applyView();
    }}
  }}
}});
function endPointer(e) {{
  var wasTap = dragging && !moved && (Date.now() - downT) < 400;
  delete pointers[e.pointerId];
  if (Object.keys(pointers).length === 0) {{
    dragging = false;
    svg.classList.remove('dragging');
    pinchDist = 0;
    if (wasTap) handleTap(e);
  }}
}}
svg.addEventListener('pointerup', endPointer);
svg.addEventListener('pointercancel', function(e) {{ delete pointers[e.pointerId]; dragging = false; svg.classList.remove('dragging'); pinchDist = 0; }});
svg.addEventListener('wheel', function(e) {{
  e.preventDefault();
  zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.15 : 1 / 1.15);
}}, {{ passive: false }});
svg.addEventListener('dblclick', function(e) {{ zoomAt(e.clientX, e.clientY, 1.6); }});

// ---- 点按详情 ----
function clearSel() {{
  document.querySelectorAll('.sel').forEach(function(el) {{ el.classList.remove('sel'); }});
  document.querySelectorAll('.node.hl').forEach(function(el) {{ el.classList.remove('hl'); }});
}}
function esc(s) {{ return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }}
function showNode(code) {{
  var n = nodesByCode[code];
  if (!n) return;
  clearSel();
  var g = document.querySelector('.node[data-code="' + code + '"]');
  if (g) g.classList.add('sel');
  var conns = DATA.node_branches[code] || [];
  conns.forEach(function(k) {{
    var pl = document.querySelector('.tube[data-key="' + k + '"]');
    if (pl) pl.classList.add('sel');
  }});
  var rows = '<tr><td class="k">类型</td><td>' + esc(TYPE_CN[n.type] || n.type) + '</td></tr>'
    + '<tr><td class="k">3D 全名</td><td class="mono">' + esc(n.name_3d || '（无实体名）') + '</td></tr>'
    + '<tr><td class="k">2D 坐标</td><td>(' + n.x.toFixed(1) + ', ' + n.y.toFixed(1) + ') mm</td></tr>'
    + '<tr><td class="k">连接管子</td><td class="mono">' + esc(conns.join(', ') || '—') + '</td></tr>';
  popBody.innerHTML = '<h2>' + esc(code) + ' · ' + esc(TYPE_CN[n.type] || n.type) + '</h2><table>' + rows + '</table>';
  popup.style.display = 'block';
}}
function showBranch(key) {{
  var b = branchesByKey[key];
  if (!b) return;
  clearSel();
  var pl = document.querySelector('.tube[data-key="' + key + '"]');
  if (pl) pl.classList.add('sel');
  [b.node0, b.node1].forEach(function(c) {{
    var g = document.querySelector('.node[data-code="' + c + '"]');
    if (g) g.classList.add('hl');
  }});
  var bs = DATA.bends.filter(function(x) {{ return x.branch === key; }});
  var bendTxt = bs.length ? bs.map(function(x) {{ return x.seg + ' @' + x.at + ' ' + (typeof x.delta === 'number' ? (x.delta > 0 ? '+' : '') + x.delta + '°' : x.delta) + '（' + x.note + '）'; }}).join('<br>') : '无';
  var segs = b.pieces.map(function(p) {{ return p.seg + ' ' + p.na + '→' + p.nb; }}).join('<br>');
  var rows = '<tr><td class="k">直径</td><td>Φ' + b.dia + ' mm</td></tr>'
    + '<tr><td class="k">3D 弧长</td><td>' + b.len_3d + ' mm</td></tr>'
    + '<tr><td class="k">2D 长度</td><td>' + b.len_2d + ' mm</td></tr>'
    + '<tr><td class="k">端点</td><td class="mono">' + esc(b.node0) + ' → ' + esc(b.node1) + '</td></tr>'
    + '<tr><td class="k">线段</td><td class="mono">' + segs + '</td></tr>'
    + '<tr><td class="k">拐弯</td><td>' + bendTxt + '</td></tr>';
  popBody.innerHTML = '<h2>管子 ' + esc(key) + '</h2><table>' + rows + '</table>';
  popup.style.display = 'block';
}}
function handleTap(e) {{
  var t = e.target;
  var ng = t.closest ? t.closest('.node') : null;
  if (ng) {{ showNode(ng.getAttribute('data-code')); return; }}
  if (t.classList && t.classList.contains('tube')) {{ showBranch(t.getAttribute('data-key')); return; }}
  popup.style.display = 'none';
  clearSel();
}}
document.getElementById('btnClose').addEventListener('click', function() {{ popup.style.display = 'none'; clearSel(); }});
document.getElementById('btnFit').addEventListener('click', fitAll);
document.getElementById('btnClear').addEventListener('click', function() {{
  popup.style.display = 'none'; clearSel();
  document.getElementById('search').value = '';
}});
function toast(msg) {{
  toastEl.textContent = msg;
  toastEl.style.display = 'block';
  setTimeout(function() {{ toastEl.style.display = 'none'; }}, 2200);
}}
function doSearch() {{
  var q = document.getElementById('search').value.trim().toUpperCase();
  if (!q) return;
  if (nodesByCode[q]) {{
    var n = nodesByCode[q];
    centerOn(n.x, -n.y, Math.max(view.k, 2));
    showNode(q);
    return;
  }}
  var key = q;
  if (/^B\\d+$/.test(q)) key = 'Body.' + q.slice(1);
  if (/^BODY\\.?\\d+$/.test(q)) key = 'Body.' + q.replace(/^BODY\\.?/, '');
  if (branchesByKey[key]) {{
    var b = branchesByKey[key];
    var mx = 0, my = 0;
    b.points.forEach(function(p) {{ mx += p[0]; my += p[1]; }});
    mx /= b.points.length; my /= b.points.length;
    centerOn(mx, -my, Math.max(view.k, 2));
    showBranch(key);
    return;
  }}
  toast('没找到 ' + q);
}}
document.getElementById('btnSearch').addEventListener('click', doSearch);
document.getElementById('search').addEventListener('keydown', function(e) {{ if (e.key === 'Enter') doSearch(); }});
// ---- 图例折叠（窄屏默认收起，点开才展开） ----
document.getElementById('legendToggle').addEventListener('click', function() {{
  var lg = document.getElementById('legend');
  var open = lg.classList.toggle('open');
  this.textContent = open ? '图例 ▾' : '图例 ▸';
}});
// ---- 旧浏览器无 100dvh 时，用 visualViewport 实际高度定 body 高 ----
if (!window.CSS || !CSS.supports('height', '100dvh')) {{
  var fixH = function() {{
    var vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.body.style.height = vh + 'px';
  }};
  fixH();
  window.addEventListener('resize', fixH);
  if (window.visualViewport) window.visualViewport.addEventListener('resize', fixH);
}}
applyView();
</script>
</body>
</html>
'''
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f'wrote {out_path} ({len(html_doc)/1024:.0f} KB)')
    print(f'branches={len(branches)} nodes={len(nodes)} segments={n_seg}')
    print(f'viewBox {vb_x:.1f} {vb_y:.1f} {vb_w:.1f} {vb_h:.1f}')

if __name__ == '__main__':
    main()
