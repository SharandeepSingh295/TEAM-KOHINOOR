#!/usr/bin/env python3
"""
KohinoorGuard Ledger Viewer.
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


def get_ledger_stats(ledger: dict) -> dict:
    """Computes aggregated metrics from blockchain ledger records."""
    total = len(ledger)
    genesis_count = sum(1 for r in ledger.values() if r.get("record_type") == "GENESIS_ORIGINAL")
    altered_count = sum(1 for r in ledger.values() if r.get("is_tampered") or r.get("record_type") == "ALTERED_DERIVATIVE")
    public_count = sum(1 for r in ledger.values() if r.get("record_type") == "PUBLIC_WEB_MATCH")
    total_gas = sum(r.get("gas_used", 0) for r in ledger.values())
    unique_verifiers = len(set(r.get("verifier_address") for r in ledger.values() if r.get("verifier_address")))
    return {
        "total": total,
        "genesis_count": genesis_count,
        "altered_count": altered_count,
        "public_count": public_count,
        "total_gas": total_gas,
        "unique_verifiers": unique_verifiers
    }


def display_summary(ledger_file: str = None):
    """Displays an executive cryptographic analytics dashboard for the ledger."""
    target_file = ledger_file or LEDGER_FILE
    if not os.path.exists(target_file):
        console.print("[bold yellow]No blockchain ledger records found yet.[/bold yellow] Run the pipeline first!")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    if not ledger:
        console.print("[bold yellow]Blockchain ledger is currently empty.[/bold yellow]")
        return

    stats = get_ledger_stats(ledger)

    summary_table = Table(
        title="📊 KohinoorGuard Blockchain Attestation Analytics",
        border_style="magenta",
        header_style="bold cyan"
    )
    summary_table.add_column("Metric / Dimension", style="bold white", width=36)
    summary_table.add_column("Count / Value", style="bold yellow", justify="right", width=20)
    summary_table.add_column("Integrity Implication", style="dim", width=40)

    summary_table.add_row("Total Blockchain Attestations", f"{stats['total']:,}", "All immutable proofs anchored on-chain")
    summary_table.add_row("Genesis Master References", f"[green]{stats['genesis_count']:,}[/green]", "Authentic unedited master face proofs")
    summary_table.add_row("Altered Derivatives / Tampers", f"[red]{stats['altered_count']:,}[/red]", "Detected pixel alterations & edits")
    summary_table.add_row("Public Web / Social Discoveries", f"[blue]{stats['public_count']:,}[/blue]", "Cross-verified social media profiles")
    summary_table.add_row("Cumulative Gas Consumed", f"{stats['total_gas']:,} gas", "Total execution compute on EVM")
    summary_table.add_row("Unique Attesting Verifiers", f"{stats['unique_verifiers']:,}", "Independent attestation wallets")

    console.print(summary_table)


def inspect_record(evidence_hash: str, ledger_file: str = None):
    """Inspects a specific evidence record in depth."""
    target_file = ledger_file or LEDGER_FILE
    if not os.path.exists(target_file):
        console.print("[bold red]Ledger file not found.[/bold red]")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    # Allow prefix lookup
    matched_key = None
    for k in ledger.keys():
        if k.lower() == evidence_hash.lower() or k.lower().startswith(evidence_hash.lower()):
            matched_key = k
            break

    if not matched_key:
        console.print(f"[bold red]Record not found for evidence hash:[/bold red] {evidence_hash}")
        return

    rec = ledger[matched_key]
    console.print(Panel(
        json.dumps(rec, indent=2),
        title=f"🔍 Evidence Record: {matched_key}",
        border_style="cyan"
    ))


def display_ledger(ledger_file: str = None, filter_type: str = None):
    target_file = ledger_file or LEDGER_FILE
    if not os.path.exists(target_file):
        console.print("[bold yellow]No blockchain ledger records found yet.[/bold yellow] Run the pipeline first!")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    if not ledger:
        console.print("[bold yellow]Blockchain ledger is currently empty.[/bold yellow]")
        return

    # Apply filter if requested
    filtered_items = []
    for ev_hash, rec in ledger.items():
        rec_type = rec.get("record_type", "LEGACY_RECORD").upper()
        if filter_type:
            ft = filter_type.strip().upper()
            if ft in ("GENESIS", "GENESIS_ORIGINAL") and rec_type != "GENESIS_ORIGINAL":
                continue
            elif ft in ("ALTERED", "TAMPERED", "ALTERED_DERIVATIVE") and rec_type != "ALTERED_DERIVATIVE":
                continue
            elif ft in ("PUBLIC", "WEB", "PUBLIC_WEB_MATCH") and rec_type != "PUBLIC_WEB_MATCH":
                continue
        filtered_items.append((ev_hash, rec))

    if not filtered_items:
        console.print(f"[yellow]No records match filter: {filter_type}[/yellow]")
        return

    table = Table(
        title=f"⛓️ KohinoorGuard On-Chain Ledger ({len(filtered_items)} Displayed / {len(ledger)} Total)",
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

    for idx, (ev_hash, rec) in enumerate(filtered_items, 1):
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
    console.print("\n[dim white]Tip: Run with [bold cyan]--summary[/bold cyan] for stats dashboard or [bold cyan]--hash <id>[/bold cyan] to inspect a record.[/dim white]")


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
    parser = argparse.ArgumentParser(description="KohinoorGuard Ledger Viewer & Analytics Utility")
    parser.add_argument("--latest", action="store_true", help="Print full JSON details of the latest evidence manifest")
    parser.add_argument("--summary", action="store_true", help="Display aggregated blockchain analytics dashboard")
    parser.add_argument("--filter", type=str, choices=["genesis", "altered", "public"], help="Filter records by classification")
    parser.add_argument("--hash", type=str, help="Inspect a specific record in full detail by evidence hash")
    parser.add_argument("--json", action="store_true", help="Output raw ledger records as formatted JSON")
    args = parser.parse_args()

    if args.latest:
        display_latest_manifest()
    elif args.summary:
        display_summary()
    elif args.hash:
        inspect_record(args.hash)
    elif args.json:
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, "r") as f:
                print(f.read())
        else:
            print("{}")
    else:
        display_ledger(filter_type=args.filter)
