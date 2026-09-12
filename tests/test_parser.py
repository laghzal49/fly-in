"""Regression tests for literal brackets in hub names."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from parser import Hub, Parser


class BracketNamesTests(unittest.TestCase):
    def test_hubs_keep_literal_brackets(self) -> None:
        for name in ("[", "]", "[]", "a[b]", "a[", "b]"):
            for suffix in ("", " [zone=priority]", "[zone=priority]"):
                with self.subTest(name=name, suffix=suffix):
                    hub = Parser().hub_parse(name + " 0 1" + suffix, 1)
                    self.assertEqual(hub.name, name)
                    self.assertEqual(hub.zone,
                                     "priority" if suffix else "normal")

    def test_connections_keep_literal_brackets(self) -> None:
        for source, target in (("[", "]"), ("a[b]", "end[]"),
                               ("a[", "end[max_link_capacity=2]")):
            for suffix in ("", " [max_link_capacity=3]",
                           "[max_link_capacity=3]"):
                with self.subTest(source=source, target=target, suffix=suffix):
                    parser = Parser()
                    parser.hubs = {name: Hub(name, i, 0) for i, name in
                                   enumerate((source, target, "end"))}
                    link = parser.connection_parsing(
                        source + "-" + target + suffix, 1)
                    self.assertEqual((link.from_hub, link.to_hub),
                                     (source, target))
                    self.assertEqual(link.max_link_capacity,
                                     3 if suffix else 1)

    def test_bad_metadata_remains_invalid(self) -> None:
        for suffix in ("[max_link_capacity=2", "[unknown=2]",
                       "[max_link_capacity=0]", "[] trailing",
                       "[max_link_capacity=2 max_link_capacity=3]"):
            with self.subTest(suffix=suffix):
                parser = Parser()
                parser.hubs = {name: Hub(name, i, 0) for i, name in
                               enumerate(("a[]", "b[]"))}
                with self.assertRaises(ValueError):
                    parser.connection_parsing("a[]-b[] " + suffix, 1)

    def test_routing_and_output_only_change_literal_names(self) -> None:
        template = ("nb_drones: 3\nstart_hub: {start} 0 0\n"
                    "hub: {middle} 1 0 [zone=restricted]\n"
                    "end_hub: {end} 2 0\n"
                    "connection: {start}-{middle}\n"
                    "connection: {middle}-{end} [max_link_capacity=2]\n")
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            outputs = []
            for names in (("start", "middle", "end"),
                          ("start[", "mid[]dle", "end]")):
                path = Path(directory) / "map.txt"
                path.write_text(template.format(
                    start=names[0], middle=names[1], end=names[2]))
                result = subprocess.run(
                    [sys.executable, str(root / "main.py"), str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                output = result.stdout
                for name, normal in zip(names, ("start", "middle", "end")):
                    output = output.replace(name, normal)
                outputs.append(output)
            self.assertEqual(outputs[0], outputs[1])
