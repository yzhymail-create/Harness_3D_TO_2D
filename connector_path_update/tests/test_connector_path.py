import unittest
from connector_path import find_longest_connector_path


def n(code, kind="junction"):
    return {"code": code, "type": kind}


def s(code, a, b, length, branch):
    return {"seg": code, "na": a, "nb": b, "length": length, "branch": branch}


class LongestPathTests(unittest.TestCase):
    def test_multisegment_branch_crosses_multiple_branches(self):
        d = {"nodes": [n("C1", "connector"), n("J1"), n("J2"),
                       n("C2", "connector"), n("C3", "connector")],
             "segments": [s("S1", "C1", "J1", 10, "B1"),
                          s("S2", "J1", "J2", 20, "B1"),
                          s("S3", "J2", "C2", 30, "B2"),
                          s("S4", "J1", "C3", 15, "B3")]}
        r = find_longest_connector_path(d)
        self.assertEqual(r["length"], 65)
        self.assertEqual(r["segments"], ["S3", "S2", "S4"])
        self.assertEqual(r["branches"], ["B2", "B1", "B3"])
        self.assertEqual(r["nodes"], ["C2", "J2", "J1", "C3"])
        self.assertEqual(r["search_method"], "tree_terminal_diameter_plus_exact_cyclic_dfs")

    def test_cycle_longer_simple_route(self):
        d = {"nodes": [n("C1", "connector"), n("A"), n("B"), n("C2", "connector")],
             "segments": [s("S1", "C1", "A", 2, "B1"),
                          s("S2", "A", "C2", 2, "B2"),
                          s("S3", "A", "B", 8, "B3"),
                          s("S4", "B", "C2", 8, "B4")]}
        r = find_longest_connector_path(d)
        self.assertEqual(r["length"], 18)
        self.assertEqual(r["segments"], ["S1", "S3", "S4"])

    def test_path_can_continue_through_intermediate_connector(self):
        d = {"nodes": [n("C1", "connector"), n("C2", "connector"), n("C3", "connector")],
             "segments": [s("S1", "C1", "C2", 10, "B1"),
                          s("S2", "C2", "C3", 20, "B2")]}
        r = find_longest_connector_path(d)
        self.assertEqual(r["length"], 30)
        self.assertEqual(r["nodes"], ["C1", "C2", "C3"])

    def test_self_loop_is_excluded_and_reported(self):
        d = {"nodes": [n("C1", "connector"), n("C2", "connector"), n("J")],
             "segments": [s("LOOP", "J", "J", 1000, "BL"),
                          s("A", "C1", "J", 3, "B1"),
                          s("B", "J", "C2", 4, "B2")]}
        r = find_longest_connector_path(d)
        self.assertEqual(r["length"], 7)
        self.assertEqual(r["ignored_self_loops"], ["LOOP"])

    def test_no_connector_pair(self):
        d = {"nodes": [n("C1", "connector"), n("J")],
             "segments": [s("S1", "C1", "J", 3, "B1")]}
        self.assertEqual(find_longest_connector_path(d)["status"], "no_connector_pair_path")

    def test_disconnected_connector_components_do_not_join(self):
        d = {"nodes": [n("C1", "connector"), n("A"), n("C2", "connector"),
                       n("C3", "connector"), n("B"), n("C4", "connector")],
             "segments": [s("S1", "C1", "A", 5, "B1"),
                          s("S2", "A", "C2", 7, "B2"),
                          s("S3", "C3", "B", 4, "B3"),
                          s("S4", "B", "C4", 4, "B4")]}
        r = find_longest_connector_path(d)
        self.assertEqual(r["length"], 12)
        self.assertEqual({r["start_connector"], r["end_connector"]}, {"C1", "C2"})

    def test_invalid_segment_data_is_rejected(self):
        d = {"nodes": [n("C1", "connector"), n("C2", "connector")],
             "segments": [s("S1", "C1", "C2", float("nan"), "B1")]}
        with self.assertRaises(ValueError):
            find_longest_connector_path(d)

    def test_unknown_node_reference_is_rejected(self):
        d = {"nodes": [n("C1", "connector")],
             "segments": [s("S1", "C1", "MISSING", 3, "B1")]}
        with self.assertRaises(ValueError):
            find_longest_connector_path(d)


if __name__ == "__main__":
    unittest.main()
