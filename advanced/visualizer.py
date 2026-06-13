#!/usr/bin/env python3
"""
visualizer.py — Patent map visualization using IPC-based classification.

Generates:
  1. Top-N assignee bar chart
  2. Annual filing trend
  3. Country distribution
  4. Technology-Effect matrix (heat map) with Blue Ocean cells highlighted
  5. Assignee × Year activity heatmap  (competitor timing analysis)
  6. IPC subclass treemap              (squarify; falls back to bar chart)
  7. Citation analysis                 (network graph if edges provided;
                                        top-cited bar chart otherwise)

Usage:
    python visualizer.py --csv patents.csv --outdir ./output --title "Atomizer"
    from advanced.visualizer import build_all_charts
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent))

plt.rcParams["font.family"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["year"] = pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce")
    return df


def _apply_ipc_classification(df: pd.DataFrame) -> pd.DataFrame:
    """Add tech/effect columns using IPC classifier (IPC-first, title-fallback)."""
    try:
        from advanced.ipc_classifier import classify_tech, classify_effect
    except ImportError:
        from ipc_classifier import classify_tech, classify_effect

    techs, effects = [], []
    for _, row in df.iterrows():
        ipc     = str(row.get("ipc", "") or "")
        title   = str(row.get("title", "") or "")
        abstract= str(row.get("abstract", "") or "")
        techs.append(classify_tech(ipc, title, abstract))
        effects.append(classify_effect(ipc, title, abstract))

    df = df.copy()
    df["tech"]   = techs
    df["effects"] = effects
    return df


# ── Chart generators ──────────────────────────────────────────────────────────

def chart_assignee(df: pd.DataFrame, outdir: Path, top_n: int = 12) -> Path:
    """Top-N assignees bar chart."""
    top = df["assignee"].value_counts().head(top_n)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("Set2", len(top))
    ax.barh(top.index[::-1], top.values[::-1], color=colors[::-1])
    ax.set_title(f"前 {top_n} 大專利申請人", fontsize=13, fontweight="bold")
    ax.set_xlabel("專利件數")
    plt.tight_layout()
    out = outdir / "chart_assignee.png"
    fig.savefig(out, dpi=150)
    plt.close()
    return out


def chart_annual_trend(df: pd.DataFrame, outdir: Path) -> Path:
    """Annual filing trend with lifecycle annotation."""
    df_y = df.dropna(subset=["year"])
    df_y = df_y[df_y["year"] >= 2000]
    trend = df_y.groupby("year").size().reset_index(name="count")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(trend["year"], trend["count"], color="#3A7EBF", alpha=0.85)
    ax.set_title("年度專利申請趨勢", fontsize=13, fontweight="bold")
    ax.set_xlabel("申請年份")
    ax.set_ylabel("件數")

    if len(trend) > 0:
        ymin, ymax = int(trend["year"].min()), int(trend["year"].max())
        mid = ymin + (ymax - ymin) // 2
        ax.axvspan(ymin,    mid,  alpha=0.07, color="gray",   label="成長期")
        ax.axvspan(mid,     ymax, alpha=0.07, color="orange", label="成熟/競爭期")
        ax.legend(fontsize=9)

    plt.tight_layout()
    out = outdir / "chart_annual_trend.png"
    fig.savefig(out, dpi=150)
    plt.close()
    return out


def chart_country(df: pd.DataFrame, outdir: Path) -> Path:
    """Country distribution bar chart."""
    cnt = df["country"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(cnt.index, cnt.values, color="#E8703A", alpha=0.85)
    ax.set_title("各國專利數量分布", fontsize=13, fontweight="bold")
    ax.set_xlabel("國家/地區")
    ax.set_ylabel("件數")
    for i, v in enumerate(cnt.values):
        ax.text(i, v + 0.2, str(v), ha="center", fontsize=9)
    plt.tight_layout()
    out = outdir / "chart_country.png"
    fig.savefig(out, dpi=150)
    plt.close()
    return out


def chart_tech_effect_matrix(df: pd.DataFrame, outdir: Path) -> tuple:
    """
    Technology × Effect heatmap.
    Returns (path, blue_ocean_cells) where blue_ocean_cells is a list of (tech, effect).
    """
    try:
        from advanced.ipc_classifier import TECH_DIMS, EFFECT_DIMS
    except ImportError:
        from ipc_classifier import TECH_DIMS, EFFECT_DIMS

    # Explode multi-effect rows
    rows = []
    for _, row in df.iterrows():
        tech    = row.get("tech", "其他")
        effects = row.get("effects", ["未分類"])
        if isinstance(effects, str):
            import ast
            try:
                effects = ast.literal_eval(effects)
            except Exception:
                effects = [effects]
        for eff in effects:
            rows.append({"tech": tech, "effect": eff})

    matrix_df = pd.DataFrame(rows)
    matrix = matrix_df.groupby(["tech", "effect"]).size().unstack(fill_value=0)

    # Ensure all defined dimensions appear
    for col in EFFECT_DIMS:
        if col not in matrix.columns:
            matrix[col] = 0
    show_effects = [e for e in EFFECT_DIMS if e in matrix.columns]
    matrix = matrix[show_effects]

    show_techs = [t for t in TECH_DIMS if t in matrix.index]
    matrix = matrix.reindex(show_techs, fill_value=0)
    matrix = matrix[matrix.sum(axis=1) > 0]  # drop all-zero rows

    if matrix.empty:
        return None, []

    # Blue Ocean = zero cells excluding the "未分類" column (which means unknown, not truly empty)
    blue_ocean = [
        (t, e) for t in matrix.index for e in matrix.columns
        if matrix.loc[t, e] == 0 and e != "未分類"
    ]

    # Build annotation: show count, mark zeros as "○"
    annot = matrix.copy().astype(object)
    for t in matrix.index:
        for e in matrix.columns:
            annot.loc[t, e] = "○" if matrix.loc[t, e] == 0 else str(int(matrix.loc[t, e]))

    fig, ax = plt.subplots(figsize=(14, max(6, len(matrix) * 0.8 + 2)))
    sns.heatmap(
        matrix, annot=annot, fmt="", cmap="YlOrRd",
        linewidths=0.5, linecolor="lightgray",
        ax=ax, cbar_kws={"label": "專利件數"},
        annot_kws={"size": 10},
        mask=(matrix == 0),       # white for zero cells
    )
    # Overlay zero cells with a light blue tint to mark as Blue Ocean
    sns.heatmap(
        (matrix == 0).astype(int), annot=annot, fmt="",
        cmap=matplotlib.colors.ListedColormap(["white", "#D6EAF8"]),
        linewidths=0.5, linecolor="lightgray",
        ax=ax, cbar=False,
        annot_kws={"size": 9, "color": "#2471A3"},
        mask=(matrix != 0),
    )

    ax.set_title(
        "技術功效矩陣  (○ = 技術空白 / Blue Ocean)",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.set_xlabel("功效目的", fontsize=11)
    ax.set_ylabel("技術手段", fontsize=11)
    ax.tick_params(axis="x", rotation=20, labelsize=9)
    ax.tick_params(axis="y", rotation=0,  labelsize=9)

    legend_patches = [
        mpatches.Patch(color="#D6EAF8", label="○ 技術空白 (Blue Ocean)"),
        mpatches.Patch(color="#FDEDEC", label="1–2 件"),
        mpatches.Patch(color="#E74C3C", label="5+ 件 (競爭激烈)"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=8,
              bbox_to_anchor=(1.0, -0.15), ncol=3)

    plt.tight_layout()
    out = outdir / "chart_tech_effect_matrix.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out, blue_ocean


def chart_assignee_year_heatmap(df: pd.DataFrame, outdir: Path, top_n: int = 10) -> Path:
    """
    Assignee × Year activity heatmap.
    Reveals when each competitor entered, peaked, and exited the technology space.
    """
    top_assignees = df["assignee"].value_counts().head(top_n).index.tolist()
    df_top = df[df["assignee"].isin(top_assignees)].copy()
    df_top = df_top.dropna(subset=["year"])
    df_top = df_top[df_top["year"].between(2000, 2030)]
    df_top["year"] = df_top["year"].astype(int)

    if df_top.empty:
        return None

    pivot = df_top.groupby(["assignee", "year"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(top_assignees, fill_value=0).sort_index(axis=1)

    fig, ax = plt.subplots(
        figsize=(max(12, len(pivot.columns) * 0.55 + 3),
                 max(5,  len(top_assignees) * 0.65 + 2))
    )
    sns.heatmap(
        pivot, annot=True, fmt="d", cmap="Blues",
        linewidths=0.3, linecolor="lightgray",
        ax=ax, cbar_kws={"label": "件數"},
        annot_kws={"size": 8},
    )
    ax.set_title(f"前 {top_n} 大申請人 × 年度佈局熱圖", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("申請年份", fontsize=10)
    ax.set_ylabel("申請人", fontsize=10)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", rotation=0,  labelsize=9)
    plt.tight_layout()
    out = outdir / "chart_assignee_year_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out


def chart_ipc_treemap(df: pd.DataFrame, outdir: Path, top_n: int = 20) -> Path:
    """
    IPC subclass distribution treemap (requires squarify).
    Falls back to horizontal bar chart when squarify is not installed.
    Each tile = one IPC subclass (4-char prefix, e.g. A61M).
    Tile area proportional to patent count.
    """
    ipc_series = df["ipc"].dropna().astype(str)
    ipc_series = ipc_series[ipc_series.str.len() >= 4]
    counts = ipc_series.str[:4].str.upper().value_counts().head(top_n)

    if counts.empty:
        return None

    try:
        import squarify
        _use_treemap = True
    except ImportError:
        _use_treemap = False

    colors = sns.color_palette("tab20", len(counts))

    if _use_treemap:
        fig, ax = plt.subplots(figsize=(14, 8))
        labels = [f"{ipc}\n({cnt})" for ipc, cnt in counts.items()]
        squarify.plot(
            sizes=counts.values, label=labels, color=colors, alpha=0.85, ax=ax,
            text_kwargs={"fontsize": 9, "fontweight": "bold"},
        )
        ax.set_title("IPC 分類分布 Treemap", fontsize=13, fontweight="bold")
        ax.axis("off")
    else:
        fig, ax = plt.subplots(figsize=(10, max(5, len(counts) * 0.45 + 2)))
        ax.barh(counts.index[::-1], counts.values[::-1], color=colors[::-1])
        ax.set_title(f"IPC 分類分布（前 {top_n} 子類）", fontsize=13, fontweight="bold")
        ax.set_xlabel("件數")
        for i, v in enumerate(counts.values[::-1]):
            ax.text(v + 0.2, i, str(v), va="center", fontsize=8)

    plt.tight_layout()
    out = outdir / "chart_ipc_treemap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out


def chart_citation_network(
    df: pd.DataFrame,
    outdir: Path,
    citation_edges: list = None,
    top_n: int = 20,
) -> Path:
    """
    Citation analysis chart — two modes:

    Network mode (citation_edges provided):
        Draws a directed citation graph using networkx.
        citation_edges = list of (citing_id, cited_id) tuples.
        Node size scales with citation_count if column exists.
        Requires: pip install networkx

    Fallback mode (no edges or networkx missing):
        Draws a horizontal bar chart of the top-N most-cited patents,
        surfacing "pioneer patents" from the citation_count column.
    """
    # ── Network graph ─────────────────────────────────────────────────────────
    if citation_edges:
        try:
            import networkx as nx

            G = nx.DiGraph()
            G.add_edges_from(citation_edges)

            id_to_count: dict = {}
            if "citation_count" in df.columns and "publication_number" in df.columns:
                id_to_count = dict(zip(
                    df["publication_number"].astype(str),
                    pd.to_numeric(df["citation_count"], errors="coerce").fillna(0),
                ))

            node_sizes = [max(150, id_to_count.get(n, 0) * 40 + 150) for n in G.nodes()]
            # Color by in-degree (how many times cited)
            in_deg = dict(G.in_degree())
            max_deg = max(in_deg.values(), default=1)
            node_colors = [plt.cm.YlOrRd(in_deg.get(n, 0) / max(max_deg, 1)) for n in G.nodes()]

            fig, ax = plt.subplots(figsize=(14, 10))
            pos = nx.spring_layout(G, k=2.5, seed=42)
            nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                                   node_color=node_colors, alpha=0.85)
            nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#BBBBBB",
                                   arrows=True, arrowsize=12, alpha=0.6)
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=6, font_color="#1A1A1A")

            sm = plt.cm.ScalarMappable(cmap="YlOrRd",
                                       norm=plt.Normalize(vmin=0, vmax=max_deg))
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label="被引用次數 (in-degree)", shrink=0.6)

            ax.set_title("引證網路圖 (Citation Network)\n節點顏色 = 被引用次數，大小 = 總引用數",
                         fontsize=12, fontweight="bold")
            ax.axis("off")
            plt.tight_layout()
            out = outdir / "chart_citation_network.png"
            fig.savefig(out, dpi=150, bbox_inches="tight")
            plt.close()
            return out

        except ImportError:
            print("[VIZ] networkx not installed (pip install networkx) — using bar chart fallback")

    # ── Fallback: top-cited patents bar chart ─────────────────────────────────
    if "citation_count" not in df.columns:
        print("[VIZ] No citation_count column — skipping citation chart")
        return None

    df_c = df[["publication_number", "title", "assignee", "citation_count"]].copy()
    df_c["citation_count"] = pd.to_numeric(df_c["citation_count"], errors="coerce").fillna(0)
    df_c = (df_c[df_c["citation_count"] > 0]
            .sort_values("citation_count", ascending=False)
            .head(top_n))

    if df_c.empty:
        print("[VIZ] All citation_count values are 0 — skipping citation chart")
        return None

    labels = df_c.apply(
        lambda r: f"{r['publication_number']}  {str(r['title'])[:28]}...", axis=1
    )
    fig, ax = plt.subplots(figsize=(12, max(6, len(df_c) * 0.5 + 2)))
    colors = sns.color_palette("YlOrRd", len(df_c))[::-1]
    ax.barh(labels.values[::-1], df_c["citation_count"].values[::-1], color=colors)
    ax.set_title(f"引用次數最多的 {top_n} 件專利（基礎/關鍵專利識別）",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("被引用次數")
    for i, v in enumerate(df_c["citation_count"].values[::-1]):
        ax.text(v + 0.3, i, str(int(v)), va="center", fontsize=8)
    plt.tight_layout()
    out = outdir / "chart_citation_top.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out


# ── Main entry ────────────────────────────────────────────────────────────────

def build_all_charts(
    csv_path: str,
    outdir: str,
    title: str = "Patent Map",
    enrich: bool = False,
    enrich_max: int = 0,
    enrich_delay: float = 3.0,
    use_tor: bool = True,
    citation_edges: list = None,
) -> dict:
    """
    Generate all patent map charts from a CSV file.

    CSV must contain at minimum: publication_number, title, assignee, year, country, ipc
    Optional columns: abstract (improves classification), citation_count (enables citation chart)

    Parameters:
        enrich          — if True, auto-fetch abstracts and IPC codes before classification
        enrich_max      — max patents to enrich (0 = all, default)
        enrich_delay    — seconds between detail page requests (default 3.0)
        use_tor         — use Tor proxy for enrichment requests (default True)
        citation_edges  — list of (citing_id, cited_id) tuples for citation network graph;
                          if None, chart_citation_network falls back to top-cited bar chart

    Returns dict with paths of generated PNG files and blue_ocean / classify_rate metadata.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # ── Optional enrichment step ──────────────────────────────────────────────
    if enrich:
        enriched_csv = str(Path(outdir) / "patents_enriched.csv")
        try:
            from advanced.abstract_enricher import enrich_csv
        except ImportError:
            from abstract_enricher import enrich_csv
        limit_msg = f"up to {enrich_max}" if enrich_max > 0 else "all"
        print(f"[VIZ] Enrichment mode ON — fetching abstracts for {limit_msg} patents...")
        enrich_csv(csv_path, enriched_csv, max_enrich=enrich_max,
                   use_tor=use_tor, delay=enrich_delay)
        csv_path = enriched_csv
        print(f"[VIZ] Using enriched CSV: {enriched_csv}")

    df = _load(csv_path)
    df = _apply_ipc_classification(df)

    results = {}

    # ── Core charts ───────────────────────────────────────────────────────────
    results["assignee"] = str(chart_assignee(df, outdir))
    results["trend"]    = str(chart_annual_trend(df, outdir))
    results["country"]  = str(chart_country(df, outdir))
    matrix_path, blue_ocean = chart_tech_effect_matrix(df, outdir)
    results["matrix"]   = str(matrix_path) if matrix_path else None
    results["blue_ocean"] = blue_ocean

    # ── Extended charts ───────────────────────────────────────────────────────
    heatmap_path = chart_assignee_year_heatmap(df, outdir)
    results["assignee_year_heatmap"] = str(heatmap_path) if heatmap_path else None

    treemap_path = chart_ipc_treemap(df, outdir)
    results["ipc_treemap"] = str(treemap_path) if treemap_path else None

    citation_path = chart_citation_network(df, outdir, citation_edges=citation_edges)
    results["citation"] = str(citation_path) if citation_path else None

    # ── Summary ───────────────────────────────────────────────────────────────
    results["total_patents"] = len(df)
    results["classified"]    = int((df["tech"] != "其他").sum())
    results["classify_rate"] = f"{results['classified'] / max(len(df), 1) * 100:.1f}%"

    n_charts = len([v for v in results.values() if v and "png" in str(v)])
    print(f"[VIZ] Generated {n_charts} charts")
    print(f"[VIZ] IPC classification rate: {results['classify_rate']} "
          f"({results['classified']}/{results['total_patents']})")
    if blue_ocean:
        print(f"[VIZ] Blue Ocean cells: {len(blue_ocean)}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patent Map Visualizer")
    parser.add_argument("--csv",           required=True,  help="Input CSV file")
    parser.add_argument("--outdir",        required=True,  help="Output directory")
    parser.add_argument("--title",         default="Patent Map", help="Chart title prefix")
    parser.add_argument("--enrich",        action="store_true", help="Fetch abstracts/IPC before classification")
    parser.add_argument("--enrich-max",    type=int,   default=0,   help="Max patents to enrich (0 = all)")
    parser.add_argument("--enrich-delay",  type=float, default=3.0, help="Delay between requests (default 3.0)")
    parser.add_argument("--no-tor",        action="store_true", help="Disable Tor for enrichment")
    parser.add_argument("--citations",     default=None, help="Path to citation edges CSV (columns: citing,cited)")
    args = parser.parse_args()

    citation_edges = None
    if args.citations:
        import csv as _csv
        with open(args.citations, encoding="utf-8-sig") as f:
            citation_edges = [(r["citing"], r["cited"]) for r in _csv.DictReader(f)]

    results = build_all_charts(
        args.csv, args.outdir, args.title,
        enrich=args.enrich,
        enrich_max=args.enrich_max,
        enrich_delay=args.enrich_delay,
        use_tor=not args.no_tor,
        citation_edges=citation_edges,
    )
    print("\n[DONE] Output files:")
    for k, v in results.items():
        if v and "png" in str(v):
            print(f"  {k}: {v}")
    if results.get("blue_ocean"):
        print("\n[BLUE OCEAN] Top 5 candidate cells:")
        for tech, eff in results["blue_ocean"][:5]:
            print(f"  [{tech}] x [{eff}]")
