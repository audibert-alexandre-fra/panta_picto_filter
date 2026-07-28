import os
import glob
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import read_json


def plot_class_distribution(repertoire: str = ".") -> None:
    """Plot class distribution bar charts from classification JSON files.

    Scans *repertoire* for files matching ``*class*.json``, generates one
    bar chart per file showing the percentage of each of the 6 classes,
    and saves the resulting PNG images into an ``images/`` subdirectory.

    Args:
        repertoire: Directory containing classification JSON files.
    """
    output_dir = os.path.join(repertoire, "images")
    os.makedirs(output_dir, exist_ok=True)

    fichiers = glob.glob(os.path.join(repertoire, "*class*.json"))

    if not fichiers:
        return

    all_classes = [1, 2, 3, 4, 5, 6]
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2", "#937860"]
    legend_labels = [
        "1 — Simple, sans coréf., sans entité",
        "2 — Complexe, sans coréf., sans entité",
        "3 — Avec coréférence, sans entité",
        "4 — Sans coréférence, avec entité",
        "5 — Avec coréférence et entité",
        "6 — Non française ou erreur dans la construction du json",
    ]

    for filepath in fichiers:
        try:
            data = read_json(filepath)
            classes = [entry["classe"] for entry in data if "classe" in entry]

            if not classes:
                continue

            total = len(classes)
            counts = Counter(classes)
            pcts = [counts.get(c, 0) / total * 100 for c in all_classes]
            effectifs = [counts.get(c, 0) for c in all_classes]

            fig, ax = plt.subplots(figsize=(10, 5))

            bars = ax.bar(
                [f"Classe {c}" for c in all_classes],
                pcts,
                color=colors,
                edgecolor="white",
                linewidth=0.8,
                width=0.6,
            )

            for bar, pct, n in zip(bars, pcts, effectifs):
                if pct > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.4,
                        f"{pct:.1f}%\n(n={n})",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        color="#333333",
                    )

            nom_fichier = os.path.basename(filepath)
            ax.set_title(
                f"Distribution des classes — {nom_fichier}",
                fontsize=13,
                fontweight="bold",
                pad=15,
            )
            ax.set_xlabel("Classe", fontsize=11)
            ax.set_ylabel("Pourcentage (%)", fontsize=11)
            ax.set_ylim(0, max(pcts) * 1.25 + 5)
            ax.yaxis.grid(True, linestyle="--", alpha=0.5)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)

            handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
            ax.legend(handles, legend_labels, loc="upper right", fontsize=8, framealpha=0.7)

            plt.tight_layout()

            nom_png = os.path.splitext(nom_fichier)[0] + ".png"
            output_path = os.path.join(output_dir, nom_png)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

        except Exception:
            continue


if __name__ == "__main__":
    plot_class_distribution(".")
