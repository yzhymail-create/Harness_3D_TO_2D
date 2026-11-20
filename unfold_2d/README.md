# unfold_2d — 3D 拓扑 → 2D DXF 展开（树形展开路线）

与仓库 `code/` 的 XY 平面投影路线不同，本目录是树形展开路线：按主干—分支层级把 3D 线束拓扑摊平成 2D 图，长度 1:1、拓扑不变。

## 文件

- `需求说明.md`：最新需求（v6p2，见 §五主干路径定义、§十三正交规则、§十四分支逐层最长路径规则、§十五平行对只画一根与 §十六过路点合并与自环符号；v6p1/v6/v5/v4 见 §十，v3 见 §一～§十二）。需求有更新就写进这里，附日期与变更记录。
- `经验记录.md`：踩过的坑汇总（2026-11-16–2026-11-18，v3→v6p2＋地板）：每条含问题/原因/处理/经验，带日期与提交号；新来的人先读这篇再动代码。
- `topology_audit.py`：拓扑结构自检（7 项检查 A1–A7，见经验记录 §四.21）。
- `merge_joints_v6p2.py`：当前主流程第二步（v6p2）。读 v6p1 的 layout.json 做后处理：§十六 过路点合并（IP：19 个点，13 条合并路径，路径 108→91、节点 110→91，几何不动）＋自环改小圆环（3 处，半径 8px、距节点 30px，不按 1:1，真值在弹窗）。输出合并后 layout.json + merge_report_v6p2.md。IP 实测：非自环长度最大误差 0.0mm，110 根管子全数可查。
- `unfold_2d_v6p1.py`：当前主流程第一步（v6p1，布局生成）。v6 + §十五 平行对只画一根（4 对各留走主干/脊线那根，隐藏整根 Body.48/Body.114 与段 SEG11/SEG22，数据记入 plan.json/Excel/layout.json；打折画法作废）。IP 实测：硬规则 10/10（H1 豁免），分支 108/110，X 交叉 0，图纸 2338.4×1325.2mm。
- `unfold_2d_v6.py`：v6（前主程序，已被 v6p1 取代，留作追溯）。§十四 逐层最长路径：段级生成树上逐层取最长简单路径为脊线、整条拉直垂直于上级脊线；两阶段分离（plan.json 方案先于放置）；硬规则 10 项（任一失败不出图）+ 清单自证；DXF 回读为交付前验证。IP 实测：X 交叉 0 对；H1 竖向居中 14.45% 由用户 2026-11-17 21:39 决定豁免通过（名义阈值仍 5%，清单带 exempt 标记），硬规则 10/10；DXF/Excel 已生成待验证，网页查看器已交付。
- `unfold_2d_v5.py`：v5（主干 = 最长连接器—连接器路径整条拉直；分支逐根挂、非脊线；硬规则 9/9 通过，X 交叉 11 对）。
- `unfold_2d_v4.py`：v4（主干 = 最长单根管子，已作废，留作追溯）。
- `unfold_2d_v3_fix.py`：v3 修正版（PCA 投影 + 主干居中 + 分支点先清点）。
- `unfold_2d_v3.py`：v3 初版（构造式贪心布局，已被 v3-fix/v4/v5 取代，留作追溯；其 `write_dxf`/`write_excel` 仍被后续版本复用，2026-11-17 修过块位移 bug）。
- `unfold_2d.py`：单层级展开（按 v2 层级概念）。
- `unfold_2d_chain.py`：链式展开。
- `unfold_2d_full.py`：整棵树 BFS 全摊一张（旧版，未实现 v3 的块/环形/拐弯/多分量）。
- `make_viewer.py`：由 layout.json 生成单文件网页查看器（SVG、无 CDN，含手机端适配）。
- `make_dxf.py`：由 layout.json 生成 DXF 工程图（独立生成器，见 §二十三）：与网页版同一份几何、同一批标签；按 Harness_3D_TO_2D v2 定义做带属性块——R2000、6 图层（属性跟随块的图层，标签跟随管线图层）、5 个共享块（每类节点一个）带 NAME/FULLNAME 属性，管子为普通多段线；写临时文件→回读核对（图层＋多段线几何＋INSERT 属性值与位置＋标签）→通过才落盘，可选同时出配套 Excel。地板实测 409/409＋409/409＋409/409，0.0000mm；IP 回归 90/90＋91/91＋90/90。
- `test_ring_classification.py`：环分类单测（合成真环/自环/平行对）。

## 用法

```bash
# 第一步：布局（v6p1）
python3 unfold_2d_v6p1.py topology.json -o out_dir
# 第二步：过路点合并 + 自环符号（v6p2 后处理）
python3 merge_joints_v6p2.py out_dir/layout.json topology.json out_dir_v6p2
# 查看器
python3 make_viewer.py out_dir_v6p2/layout.json viewer.html
# DXF 工程图（+ 配套 Excel）
python3 make_dxf.py out_dir_v6p2/layout.json unfold_v6p2.dxf --excel unfold_v6p2.xlsx
```

第一步输出：`unfold_v6p1.dxf`（块输出）、`unfold_v6p1.xlsx`、`layout.json`、`plan.json`、`checklist_v6p1.md`、`branch_layers.md`、`comparison_v6p1.md`（硬规则失败时只出后五项，不出 DXF/Excel）。第二步输出：合并后 `layout.json` + `merge_report_v6p2.md`。第三步（DXF）：`unfold_v6p2.dxf`（R2000，5 个共享属性块＋409 个 INSERT＋409 条多段线）+ `unfold_v6p2.xlsx`（2D管子/2D线段/2D节点/验证 4 表）。

依赖：`ezdxf`、`openpyxl`。输入为四步管线输出的 `topology.json`（branches 含 key/length/dia/node0/node1/polyline，nodes 含 code/type/xyz）。

## 约定

- 需求有更新，写进 `需求说明.md`（附日期与变更记录）；代码有更新，改本文件夹里的代码。
- 改代码后先在已有拓扑数据上自测再提交；提交信息写清改了什么和为什么。
