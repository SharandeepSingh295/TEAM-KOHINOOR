#!/usr/bin/env python3
"""
KohinoorGuard Biometric Forensic Analyzer & Tamper Heatmap Inspector.
Analyzes face scans and derivative images using:
  - Error Level Analysis (ELA) for digital splicing & resaving
  - Laplacian high-frequency edge & noise variance
  - Pixel-level differential heatmap generation
  - 4-panel visual forensic audit cards
"""

import os
import sys
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.forensic_engine import ForensicEngine

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]KohinoorGuard Forensic Lab[/bold cyan] : [bold white]Deepfake & Tamper Heatmap Analyzer[/bold white]\n"
        "[dim]Error Level Analysis (ELA) &bull; Noise Residuals &bull; Differential Heatmaps &bull; Integrity Scoring[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def analyze_images(
    target_image: str,
    original_image: str = None,
    output_dir: str = "output/forensics",
    identifier: str = "audit"
):
    print_banner()

    if not os.path.exists(target_image):
        console.print(f"[bold red]Error:[/bold red] Target image not found: {target_image}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    engine = ForensicEngine(output_dir=output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Executing forensic analysis algorithms...", total=None)

        if original_image:
            if not os.path.exists(original_image):
                console.print(f"[bold red]Error:[/bold red] Reference image not found: {original_image}")
                sys.exit(1)
            report = engine.compare_images(original_image, target_image, identifier=identifier)
            mode_desc = f"Differential Audit vs Genesis Master ({os.path.basename(original_image)})"
        else:
            report = engine.analyze_standalone_image(target_image, identifier=identifier)
            mode_desc = "Standalone ELA & High-Frequency Noise Inspection"

    # Display Verdict Panel
    is_clean = not report.is_tampered
    panel_color = "green" if is_clean else "yellow" if report.tamper_probability < 0.6 else "red"
    verdict_badge = f"[bold {panel_color}]{report.verdict}[/bold {panel_color}]"

    console.print(Panel(
        f"[bold white]Analysis Mode:[/bold white] {mode_desc}\n"
        f"[bold white]Forensic Verdict:[/bold white] {verdict_badge}\n"
        f"[bold white]Integrity Score:[/bold white] [{'green' if report.integrity_score >= 80 else 'red'}]{report.integrity_score}%[/{'green' if report.integrity_score >= 80 else 'red'}] "
        f"[dim](Tamper Probability: {report.tamper_probability * 100:.1f}%)[/dim]",
        title="[bold cyan]🔬 Forensic Analysis Outcome[/bold cyan]",
        border_style=panel_color
    ))

    # Metrics Table
    table = Table(title="Quantitative Forensic Metrics", border_style="cyan")
    table.add_column("Metric / Indicator", style="white", justify="left")
    table.add_column("Observed Value", style="bold cyan", justify="right")
    table.add_column("Forensic Interpretation", style="dim", justify="left")

    table.add_row(
        "Altered Pixel Ratio",
        f"{report.altered_pixel_ratio}%",
        "Spatial area displaying notable variation (> threshold)"
    )
    table.add_row(
        "Mean Squared Error (MSE)",
        f"{report.mean_squared_error}",
        "Deviation metric between pixel matrix representations"
    )
    table.add_row(
        "Peak Signal-to-Noise (PSNR)",
        f"{report.peak_signal_to_noise} dB",
        "Higher is more identical (100 dB = identical)"
    )
    table.add_row(
        "ELA Mean Error",
        f"{report.ela_metrics.get('mean_error', 0.0)}",
        "Average re-compression differential"
    )
    table.add_row(
        "ELA Energy Variance",
        f"{report.ela_metrics.get('energy_variance', 0.0)}",
        "High variance indicates inconsistent editing / splicing"
    )
    table.add_row(
        "Laplacian Noise Variance",
        f"{report.noise_variance}",
        "High-frequency edge texture and sensor noise distribution"
    )
    table.add_row(
        "Detected Alteration Clusters",
        f"{len(report.altered_bounding_boxes)} zones",
        "Localized regions exhibiting spatial divergence"
    )

    console.print(table)

    # Generated Visual Artifacts
    console.print("\n[bold cyan]Generated Forensic Artifacts:[/bold cyan]")
    if report.heatmap_path:
        console.print(f"  [green]✔[/green] Tamper Heatmap Overlay : [bold yellow]{report.heatmap_path}[/bold yellow]")
    if report.ela_path:
        console.print(f"  [green]✔[/green] ELA Residual Image    : [bold yellow]{report.ela_path}[/bold yellow]")
    if report.composite_path:
        console.print(f"  [green]✔[/green] 4-Panel Audit Card    : [bold yellow]{report.composite_path}[/bold yellow]")

    # Save JSON Report
    json_path = os.path.join(output_dir, f"forensic_report_{identifier}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    console.print(f"  [green]✔[/green] Structured JSON Report: [bold yellow]{json_path}[/bold yellow]")

    return report


def main():
    parser = argparse.ArgumentParser(description="KohinoorGuard Biometric Forensic Analyzer & Tamper Heatmap Inspector")
    parser.add_argument("--image", "-i", type=str, required=True, help="Path to target face image to analyze")
    parser.add_argument("--original", "-o", type=str, default=None, help="Optional Genesis master original image for differential audit")
    parser.add_argument("--output-dir", "-d", type=str, default="output/forensics", help="Directory to save visual heatmaps and reports")
    parser.add_argument("--id", type=str, default="audit", help="Unique identifier for generated artifacts")

    args = parser.parse_args()
    analyze_images(
        target_image=args.image,
        original_image=args.original,
        output_dir=args.output_dir,
        identifier=args.id
    )


if __name__ == "__main__":
    main()
