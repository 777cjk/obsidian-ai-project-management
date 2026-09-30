import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class MethodsBenchmarkTests(unittest.TestCase):
    def test_benchmark_keeps_the_portable_contract_explicit(self):
        document = (ROOT / "references" / "methods-benchmark.md").read_text(encoding="utf-8")

        for marker in (
            "## What the sources actually do",
            "## Common core",
            "## Adopt in this Skill now",
            "## Defer until a real canary proves the need",
            "## Portable contract",
            "## Evidence limits",
        ):
            self.assertIn(marker, document)

        protocol = (ROOT / "references" / "protocol.md").read_text(encoding="utf-8")
        self.assertIn("## Query Receipt", protocol)
        self.assertIn("human_usefulness: unknown", protocol)
        self.assertTrue((ROOT / "assets" / "templates" / "Query Receipt.md").is_file())

        for layer in ("raw", "candidate", "memory", "projects", "application result"):
            self.assertIn(layer, document)

        for source in (
            "fortelabs.com/blog/para",
            "zettelkasten.de/atomicity",
            "obsidianmd/obsidian-clipper",
            "swarmclawai/swarmvault",
            "volcengine/OpenViking",
            "infiniflow/ragflow",
            "microsoft/graphrag",
        ):
            self.assertIn(source, document)


if __name__ == "__main__":
    unittest.main()
