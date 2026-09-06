#!/usr/bin/env python3
"""
VeriFace-Chain Ledger Viewer.
Displays all on-chain verification records, Genesis master proofs,
and altered derivative alerts stored in the local blockchain ledger.
"""

import os
import sys
import json
import datetime
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Fix UTF-8 encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()
LEDGER_FILE = os.path.join("output", "local_ledger.json")
MANIFEST_FILE = os.path.join("output", "evidence_manifest.json")


def display_ledger():
    if not os.path.exists(LEDGER_FILE):
        console.print("[bold yellow]No blockchain ledger records found yet.[/bold yellow] Run the pipeline first!")
        return

    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    if not ledger:
        console.print("[bold yellow]Blockchain ledger is currently empty.[/bold yellow]")
        return

    table = Table(
        title=f"⛓️ VeriFace-Chain On-Chain Ledger ({len(ledger)} Recorded Attestations)",
        border_style="cyan",
        header_style="bold magenta"
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Evidence Root Hash", style="bold cyan", width=20)
    table.add_column("Classification", justify="center", width=20)
    table.add_column("Platform / URL", style="white", width=26)
    table.add_column("Block", justify="right", style="yellow", width=7)
    table.add_column("Face Hash (Crop)", style="dim", width=14)
    table.add_column("Integrity & Tamper Status", style="italic", width=30)

    for idx, (ev_hash, rec) in enumerate(ledger.items(), 1):
        rec_type = rec.get("record_type", "LEGACY_RECORD")
        is_tampered = rec.get("is_tampered", False)
        block_no = f"#{rec.get('block_number', '?')}"
        short_ev = ev_hash[:10] + "..." + ev_hash[-6:] if len(ev_hash) > 18 else ev_hash
        short_face = rec.get("face_hash", "")[:10] + "..." if rec.get("face_hash") else "N/A"
        platform = rec.get("platform", "Web")
        url = rec.get("source_url", "")
        if len(url) > 24:
            url_display = url[:22] + "..."
        else:
            url_display = url or platform

        if is_tampered or rec_type == "ALTERED_DERIVATIVE":
            badge = "[bold red]✖ ALTERED COPY[/bold red]"
            status_desc = f"[red]⚠ {rec.get('tamper_details', 'Tampered asset!')[:32]}[/red]"
        elif rec_type == "GENESIS_ORIGINAL":
            badge = "[bold green]✔ GENESIS MASTER[/bold green]"
            status_desc = "[green]Authentic Master Proof[/green]"
        elif rec_type == "PUBLIC_WEB_MATCH":
            badge = "[bold blue]🌐 PUBLIC MATCH[/bold blue]"
            status_desc = f"[blue]Discovered on {platform}[/blue]"
        else:
            badge = "[white]RECORDED[/white]"
            status_desc = "[dim]On-Chain Attestation[/dim]"

        table.add_row(
            str(idx),
            short_ev,
            badge,
            f"{platform}\n[dim]{url_display}[/dim]",
            block_no,
            short_face,
            status_desc
        )

    console.print(table)
    console.print("\n[dim white]Tip: Run with [bold cyan]--latest[/bold cyan] to inspect full JSON details of the most recent scan.[/dim white]")


def display_latest_manifest():
    if not os.path.exists(MANIFEST_FILE):
        console.print("[bold yellow]No evidence manifest found at output/evidence_manifest.json[/bold yellow]")
        return

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    console.print(Panel(
        json.dumps(manifest, indent=2),
        title="📄 Full Evidence Manifest (output/evidence_manifest.json)",
        border_style="green"
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeriFace-Chain Ledger Viewer")
    parser.add_argument("--latest", action="store_true", help="Print full JSON details of the latest evidence manifest")
    args = parser.parse_args()

    if args.latest:
        display_latest_manifest()
    else:
        display_ledger()
