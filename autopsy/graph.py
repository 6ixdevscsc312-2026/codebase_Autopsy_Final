"""
graph.py
Builds a module-level dependency graph from the ModuleInfo objects
produced by ingest.py. This is what lets us reason about structure:
which modules depend on which, and where cycles or hubs hide.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from autopsy.ingest import ModuleInfo


@dataclass
class RepoGraph:
    modules: dict[str, ModuleInfo]  # path -> ModuleInfo
    edges: dict[str, set[str]] = field(default_factory=dict)  # path -> set of paths it imports

    def add_edge(self, src: str, dst: str) -> None:
        self.edges.setdefault(src, set()).add(dst)

    def in_degree(self, path: str) -> int:
        return sum(1 for edges in self.edges.values() if path in edges)

    def out_degree(self, path: str) -> int:
        return len(self.edges.get(path, set()))

    def find_cycles(self) -> list[list[str]]:
        """Simple DFS-based cycle detection. Returns list of cycles (as path lists)."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        stack: list[str] = []
        on_stack: set[str] = set()

        def dfs(node: str) -> None:
            visited.add(node)
            stack.append(node)
            on_stack.add(node)
            for neighbor in self.edges.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in on_stack:
                    idx = stack.index(neighbor)
                    cycles.append(stack[idx:] + [neighbor])
            stack.pop()
            on_stack.discard(node)

        for node in self.modules:
            if node not in visited:
                dfs(node)

        return cycles


def _module_name_to_path(mod_name: str, all_paths: list[str]) -> str | None:
    """Best-effort match of an import name like 'pkg.sub' to a file path
    like 'pkg/sub.py' or 'pkg/sub/__init__.py' within the repo."""
    candidate = mod_name.replace(".", os.sep)
    for p in all_paths:
        no_ext = p[:-3] if p.endswith(".py") else p
        if no_ext == candidate or no_ext.endswith(os.sep + candidate):
            return p
        if p.endswith(os.sep + "__init__.py") and p[: -len("__init__.py") - 1] == candidate:
            return p
    return None


def build_graph(modules: list[ModuleInfo]) -> RepoGraph:
    mod_map = {m.path: m for m in modules}
    all_paths = list(mod_map.keys())
    graph = RepoGraph(modules=mod_map)

    for m in modules:
        for imp in m.imports:
            target = _module_name_to_path(imp, all_paths)
            if target and target != m.path:
                graph.add_edge(m.path, target)

    return graph


if __name__ == "__main__":
    import sys
    from autopsy.ingest import walk_repo

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    mods = walk_repo(target)
    g = build_graph(mods)

    print(f"Graph: {len(g.modules)} nodes, {sum(len(v) for v in g.edges.values())} edges")

    cycles = g.find_cycles()
    if cycles:
        print(f"\nFound {len(cycles)} import cycle(s):")
        for c in cycles[:5]:
            print("  " + " -> ".join(c))
    else:
        print("\nNo import cycles found.")

    print("\nTop modules by in-degree (most depended-upon):")
    ranked = sorted(g.modules.keys(), key=g.in_degree, reverse=True)
    for p in ranked[:5]:
        print(f"  {p}: in={g.in_degree(p)} out={g.out_degree(p)}")
