# unfold_2d — 3D 拓扑 → 2D DXF 展开（树形展开路线）

与仓库 `code/` 的 XY 平面投影路线不同，本目录是树形展开路线：按主干—分支层级把 3D 线束拓扑摊平成 2D 图，长度 1:1、拓扑不变。

## 文件

- `需求说明.md`：最新需求（v6，见 §五主干路径定义、§十三正交规则与 §十四分支逐层最长路径规则；v5/v4 见 §十，v3 见 §一～§十二）。需求有更新就写进这里，附日期与变更记录。
- `unfold_2d_v6.py`：当前主程序（v6）。§十四 逐层最长路径：段级生成树上逐层取最长简单路径为脊线、整条拉直垂直于上级脊线；两阶段分离（plan.json 方案先于放置）；硬规则 10 项（任一失败不出图）+ 清单自证；DXF 回读为交付前验证。IP 实测：X 交叉 0 对；H1 竖向居中 14.45% 由用户 2026-11-17 21:39 决定豁免通过（名义阈值仍 5%，清单带 exempt 标记），硬规则 10/10；DXF/Excel 已生成待验证，网页查看器已交付。
- `unfold_2d_v5.py`：v5（主干 = 最长连接器—连接器路径整条拉直；分支逐根挂、非脊线；硬规则 9/9 通过，X 交叉 11 对）。
- `unfold_2d_v4.py`：v4（主干 = 最长单根管子，已作废，留作追溯）。
- `unfold_2d_v3_fix.py`：v3 修正版（PCA 投影 + 主干居中 + 分支点先清点）。
- `unfold_2d_v3.py`：v3 初版（构造式贪心布局，已被 v3-fix/v4/v5 取代，留作追溯；其 `write_dxf`/`write_excel` 仍被后续版本复用，2026-11-17 修过块位移 bug）。
- `unfold_2d.py`：单层级展开（按 v2 层级概念）。
- `unfold_2d_chain.py`：链式展开。
- `unfold_2d_full.py`：整棵树 BFS 全摊一张（旧版，未实现 v3 的块/环形/拐弯/多分量）。
- `make_viewer.py`：由 layout.json 生成单文件网页查看器（SVG、无 CDN，含手机端适配）。
- `test_ring_classification.py`：环分类单测（合成真环/自环/平行对）。

## 用法

```bash
python3 unfold_2d_v6.py topology.json -o out_dir
```

输出：`unfold_v6.dxf`（块输出）、`unfold_v6.xlsx`、`layout.json`、`plan.json`、`checklist_v6.md`、`branch_layers.md`、`comparison_v6.md`（硬规则失败时只出后五项，不出 DXF/Excel）。

依赖：`ezdxf`、`openpyxl`。输入为四步管线输出的 `topology.json`（branches 含 key/length/dia/node0/node1/polyline，nodes 含 code/type/xyz）。

## 约定

- 需求有更新，写进 `需求说明.md`（附日期与变更记录）；代码有更新，改本文件夹里的代码。
- 改代码后先在已有拓扑数据上自测再提交；提交信息写清改了什么和为什么。
