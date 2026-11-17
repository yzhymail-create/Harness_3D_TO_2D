#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""连接器到连接器全局最长简单路径（segment 级、真实长度、确定性）。

无环连通分量使用树直径双遍历，时间 O(V+E)；含环分量使用精确 DFS，
每个起点只遍历一次并同时比较所有后续连接器，避免旧版对每一对连接器
重复搜索。含环图的最长简单路径本质上可能是指数复杂度，不能伪称多项式。
"""
import argparse
import json
import math
from collections import defaultdict


_EPS = 1e-9


def _path_record(source, target, edge_ids, node_path, edges):
    details = [edges[eid] for eid in edge_ids]
    branches = []
    for edge in details:
        branch = edge["branch"]
        if branch is not None and (not branches or branches[-1] != branch):
            branches.append(branch)
    return {
        "start_connector": source,
        "end_connector": target,
        "length": sum(edge["length"] for edge in details),
        "segments": [edge["seg"] for edge in details],
        "branches": branches,
        "nodes": list(node_path),
        "segment_details": details,
    }


def _is_better(candidate, best):
    if best is None or candidate["length"] > best["length"] + _EPS:
        return True
    if abs(candidate["length"] - best["length"]) <= _EPS:
        a = (candidate["start_connector"], candidate["end_connector"],
             tuple(candidate["segments"]))
        b = (best["start_connector"], best["end_connector"],
             tuple(best["segments"]))
        return a < b
    return False


def _tree_diameter(connectors, component_nodes, component_edges, adj, edges):
    """树中连接器终端集合的加权直径；两次树遍历即可精确求解。"""
    if len(connectors) < 2:
        return None

    def farthest(start):
        stack = [(start, None, 0.0, [start], [])]
        far_node, far_dist, far_nodes, far_edges = None, -1.0, None, None
        while stack:
            node, parent, dist, node_path, edge_path = stack.pop()
            if node in connectors and node != start:
                if (dist > far_dist + _EPS or
                        (abs(dist - far_dist) <= _EPS and
                         (far_node is None or node < far_node))):
                    far_node, far_dist = node, dist
                    far_nodes, far_edges = node_path, edge_path
            for nxt, eid in reversed(adj[node]):
                if nxt == parent:
                    continue
                stack.append((nxt, node, dist + edges[eid]["length"],
                              node_path + [nxt], edge_path + [eid]))
        return far_node, far_dist, far_nodes, far_edges

    first, _, _, _ = farthest(connectors[0])
    if first is None:
        return None
    second, _, node_path, edge_path = farthest(first)
    if second is None:
        return None
    if first <= second:
        source, target = first, second
    else:
        source, target = second, first
        node_path = list(reversed(node_path))
        edge_path = list(reversed(edge_path))
    return _path_record(source, target, edge_path, node_path, edges)


def find_longest_connector_path(data):
    if not isinstance(data, dict):
        raise TypeError("topology data must be a JSON object")
    raw_nodes = data.get("nodes", [])
    raw_segments = data.get("segments", [])
    nodes = {}
    for node in raw_nodes:
        code = node.get("code")
        if code is None:
            raise ValueError("Every node must have a non-empty 'code'")
        if code in nodes:
            raise ValueError("Duplicate node code: %s" % code)
        nodes[code] = node

    connectors = sorted(
        code for code, node in nodes.items()
        if str(node.get("type", "")).strip().lower() == "connector"
    )
    edges, adj, self_loops = [], defaultdict(list), []
    for i, seg in enumerate(raw_segments):
        a, b = seg.get("na"), seg.get("nb")
        seg_name = seg.get("seg", "edge_%d" % i)
        if a not in nodes or b not in nodes:
            raise ValueError("Segment %s references an unknown node (%r, %r)" %
                             (seg_name, a, b))
        if a == b:
            self_loops.append(seg_name)
            continue
        try:
            weight = float(seg["length"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Segment %s has an invalid/missing length" % seg_name)
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("Segment %s length must be finite and non-negative" % seg_name)
        eid = len(edges)
        edges.append({"seg": seg_name, "branch": seg.get("branch"),
                      "na": a, "nb": b, "length": weight})
        adj[a].append((b, eid))
        adj[b].append((a, eid))
    for node in adj:
        adj[node].sort(key=lambda item: (item[0], edges[item[1]]["seg"], item[1]))

    # 先按连通分量处理，避免在互不连通的区域间搜索。
    unseen = set(nodes)
    components = []
    while unseen:
        root = min(unseen)
        stack, comp_nodes, comp_edge_ids = [root], set(), set()
        unseen.remove(root)
        while stack:
            cur = stack.pop()
            comp_nodes.add(cur)
            for nxt, eid in adj.get(cur, []):
                comp_edge_ids.add(eid)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        comp_connectors = sorted(set(connectors) & comp_nodes)
        if len(comp_connectors) >= 2:
            components.append((comp_nodes, comp_edge_ids, comp_connectors))

    best, explored = None, 0
    for comp_nodes, comp_edge_ids, comp_connectors in components:
        # 简单树分量直接求终端直径，不做指数搜索。
        if len(comp_edge_ids) == len(comp_nodes) - 1:
            candidate = _tree_diameter(comp_connectors, comp_nodes,
                                       comp_edge_ids, adj, edges)
            if candidate and _is_better(candidate, best):
                best = candidate
            continue

        # 有环/平行边分量：精确搜索。每个 source 一次，同时评估所有
        # source < target 的连接器；节点不可重复，确保是简单路径。
        total_weight = sum(edges[eid]["length"] for eid in comp_edge_ids)
        for source in comp_connectors:
            visited = {source}
            path_edges, path_nodes = [], [source]

            def dfs(current, total, unused_weight):
                nonlocal best, explored
                explored += 1
                if current in comp_connectors and current != source and source < current:
                    candidate = _path_record(source, current, path_edges,
                                              path_nodes, edges)
                    if _is_better(candidate, best):
                        best = candidate

                # 所有未使用边权重之和是安全上界（偏松但不会漏掉最优解）。
                if best is not None and total + unused_weight < best["length"] - _EPS:
                    return
                for nxt, eid in adj.get(current, []):
                    if nxt in visited:
                        continue
                    weight = edges[eid]["length"]
                    visited.add(nxt)
                    path_edges.append(eid)
                    path_nodes.append(nxt)
                    dfs(nxt, total + weight, unused_weight - weight)
                    path_nodes.pop()
                    path_edges.pop()
                    visited.remove(nxt)

            dfs(source, 0.0, total_weight)

    if best is None:
        best = {
            "start_connector": None, "end_connector": None, "length": 0.0,
            "segments": [], "branches": [], "nodes": [], "segment_details": [],
            "status": "no_connector_pair_path",
        }
    else:
        best["status"] = "ok"
    best.update({
        "connector_count": len(connectors),
        "explored_states": explored,
        "ignored_self_loops": self_loops,
        "path_definition": (
            "longest simple path between two distinct connector nodes; "
            "sum of source 3D segment lengths; intermediate connectors are allowed"
        ),
        "search_method": "tree_terminal_diameter_plus_exact_cyclic_dfs",
    })
    return best


def main():
    parser = argparse.ArgumentParser(description="线束连接器到连接器全局最长路径分析")
    parser.add_argument("topology_json")
    parser.add_argument("-o", "--output", default="connector_longest_path.json")
    args = parser.parse_args()
    with open(args.topology_json, encoding="utf-8") as f:
        result = find_longest_connector_path(json.load(f))
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    if result["status"] == "ok":
        print("%s -> %s | %.1f mm | %d segments | %d branch objects | %d cyclic-search states" %
              (result["start_connector"], result["end_connector"], result["length"],
               len(result["segments"]), len(result["branches"]), result["explored_states"]))
    else:
        print("No connected pair of distinct connectors found.")
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
