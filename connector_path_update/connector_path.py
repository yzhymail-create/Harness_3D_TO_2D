#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exact connector-to-connector longest simple path over segment-level topology."""
import argparse
import json
from collections import defaultdict


def find_longest_connector_path(data):
    nodes = {n["code"]: n for n in data.get("nodes", [])}
    connectors = sorted(k for k, n in nodes.items()
                        if str(n.get("type", "")).lower() == "connector")
    edges, adj, self_loops = [], defaultdict(list), []
    for i, seg in enumerate(data.get("segments", [])):
        a, b = seg.get("na"), seg.get("nb")
        if a not in nodes or b not in nodes:
            continue
        if a == b:
            self_loops.append(seg.get("seg", "edge_%d" % i))
            continue
        weight = float(seg.get("length", 0.0))
        if weight < 0:
            raise ValueError("Negative segment length: %s" % seg.get("seg"))
        eid = len(edges)
        edges.append({"seg": seg.get("seg", "edge_%d" % i),
                      "branch": seg.get("branch"), "na": a, "nb": b,
                      "length": weight})
        adj[a].append((b, eid))
        adj[b].append((a, eid))
    for n in adj:
        adj[n].sort(key=lambda x: (x[0], edges[x[1]]["seg"]))

    best, best_key, explored = None, None, 0
    # Exhaustive DFS is exact. A visited-node set makes every candidate a
    # simple path; the real graph's low cycle rank keeps this practical.
    for i, source in enumerate(connectors):
        for target in connectors[i + 1:]:
            visited, path_edges, path_nodes = {source}, [], [source]

            def dfs(current, total):
                nonlocal best, best_key, explored
                explored += 1
                if current == target:
                    ep = [edges[e] for e in path_edges]
                    segs = [e["seg"] for e in ep]
                    branches = []
                    for e in ep:
                        if e["branch"] is not None and (not branches or branches[-1] != e["branch"]):
                            branches.append(e["branch"])
                    key = (source, target, tuple(segs))
                    if (best is None or total > best["length"] + 1e-9 or
                            (abs(total - best["length"]) <= 1e-9 and key < best_key)):
                        best_key = key
                        best = {"start_connector": source, "end_connector": target,
                                "length": total, "segments": segs, "branches": branches,
                                "nodes": list(path_nodes), "segment_details": ep}
                for nxt, eid in adj.get(current, []):
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    path_edges.append(eid)
                    path_nodes.append(nxt)
                    dfs(nxt, total + edges[eid]["length"])
                    path_nodes.pop()
                    path_edges.pop()
                    visited.remove(nxt)

            dfs(source, 0.0)

    if best is None:
        best = {"start_connector": None, "end_connector": None, "length": 0.0,
                "segments": [], "branches": [], "nodes": [], "segment_details": [],
                "status": "no_connector_pair_path"}
    else:
        best["status"] = "ok"
    best.update({"connector_count": len(connectors), "explored_states": explored,
                 "ignored_self_loops": self_loops,
                 "path_definition": "longest simple path between two distinct connector nodes; sum of source 3D segment lengths"})
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
        print("%s -> %s | %.1f mm | %d segments | %d branch objects | %d search states" %
              (result["start_connector"], result["end_connector"], result["length"],
               len(result["segments"]), len(result["branches"]), result["explored_states"]))
    else:
        print("No connected pair of distinct connectors found.")
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
