#!/usr/bin/env python3
"""
VeriFace-Chain Pipeline Runner.
Orchestrates:
  1. Face Scan Ingestion & Biometric Feature Extraction
  2. Live Web & Social Media Reverse Discovery
  3. Canonical Cryptographic Evidence Packaging
  4. Blockchain Registration & Smart Contract Anchoring
  5. Immediate On-Chain Re-Verification Check
"""

import os
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.face_engine import FaceEngine
from src.search_engine import WebSocialSearchEngine
from src.evidence_packager import EvidencePackager
from src.blockchain_client import BlockchainClient

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]VeriFace-Chain[/bold cyan] : [bold white]End-to-End Face Verification Pipeline[/bold white]\n"
        "[dim]Face Scan Ingestion -> Live Web/Social Search -> Blockchain Attestation[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def run_pipeline(
    image_path: str,
    chain_mode: str = "local",
    rpc_url: str = None,
    output_dir: str = "output",
    search_query_hint: str = None
):
    print_banner()

    if not os.path.exists(image_path):
        console.print(f"[bold red]Error:[/bold red] Input image '{image_path}' not found!")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------
    # STAGE 1: Face Ingestion & Biometric Feature Extraction
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 1:[/bold yellow] [bold white]Face Scan Ingestion & Biometric Encoding[/bold white]")
    face_engine = FaceEngine()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description="Detecting facial landmarks & computing hashes...", total=None)
        face_result = face_engine.process_face_scan(image_path, output_crop_dir=output_dir)

    stage1_table = Table(show_header=False, box=None)
    stage1_table.add_row("[green]+[/green] Face Detected Bounding Box:", f"{face_result.bounding_box}")
    stage1_table.add_row("[green]+[/green] Detection Confidence:", f"{face_result.confidence * 100:.1f}%")
    stage1_table.add_row("[green]+[/green] Standardized Face Crop:", f"{face_result.crop_path}")
    stage1_table.add_row("[green]+[/green] Face SHA-256 Hash:", f"[bold cyan]{face_result.face_hash}[/bold cyan]")
    stage1_table.add_row("[green]+[/green] Perceptual dHash:", f"{face_result.perceptual_hash[:16]}... (visual fingerprint)")
    console.print(stage1_table)

    # -------------------------------------------------------------
    # STAGE 2: Web & Social Media Discovery
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 2:[/bold yellow] [bold white]Live Web & Social Media Reverse Discovery[/bold white]")
    search_engine = WebSocialSearchEngine(output_dir=output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description="Querying visual search engine for matching social content...", total=None)
        social_match = search_engine.execute_search(
            image_path=face_result.crop_path,
            search_query_hint=search_query_hint
        )

    stage2_table = Table(show_header=False, box=None)
    stage2_table.add_row("[green]+[/green] Search Engine Provider:", f"{social_match.search_provider}")
    stage2_table.add_row("[green]+[/green] Discovered Platform:", f"[bold magenta]{social_match.platform}[/bold magenta]")
    stage2_table.add_row("[green]+[/green] Verified Post URL:", f"[underline blue]{social_match.url}[/underline blue]")
    stage2_table.add_row("[green]+[/green] Content Author/Handle:", f"{social_match.author}")
    stage2_table.add_row("[green]+[/green] Downloaded Media Asset:", f"{social_match.local_media_path}")
    stage2_table.add_row("[green]+[/green] Content SHA-256 Hash:", f"[bold cyan]{social_match.media_hash}[/bold cyan]")
    console.print(stage2_table)

    # -------------------------------------------------------------
    # STAGE 3: Canonical Cryptographic Evidence Packaging
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 3:[/bold yellow] [bold white]Cryptographic Evidence Packaging[/bold white]")
    packager = EvidencePackager(output_dir=output_dir)

    manifest = packager.create_package(
        face_result=face_result,
        social_match=social_match
    )

    stage3_table = Table(show_header=False, box=None)
    stage3_table.add_row("[green]+[/green] Canonical Root Hash:", f"[bold cyan]{manifest['evidence_hash']}[/bold cyan]")
    stage3_table.add_row("[green]+[/green] Manifest Saved:", f"{os.path.join(output_dir, 'evidence_manifest.json')}")
    console.print(stage3_table)

    # -------------------------------------------------------------
    # STAGE 4: Blockchain Registration & Smart Contract Anchoring
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 4:[/bold yellow] [bold white]Blockchain Smart Contract Anchoring[/bold white]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description=f"Connecting to {chain_mode.upper()} chain and recording evidence...", total=None)
        
        blockchain = BlockchainClient(
            mode=chain_mode,
            rpc_url=rpc_url
        )
        
        receipt = blockchain.record_verification(
            evidence_hash=manifest["evidence_hash"],
            face_hash=face_result.face_hash,
            media_hash=social_match.media_hash,
            source_url=social_match.url,
            platform=social_match.platform
        )

    # Update manifest with on-chain receipt
    manifest["blockchain_status"] = {
        "anchored": True,
        "network": receipt["network"],
        "contract_address": receipt["contract_address"],
        "transaction_hash": receipt["transaction_hash"],
        "block_number": receipt["block_number"],
        "gas_used": receipt["gas_used"],
        "verifier_address": receipt["verifier_address"]
    }
    packager.save_updated_manifest(manifest)

    stage4_table = Table(show_header=False, box=None)
    stage4_table.add_row("[green]+[/green] Blockchain Network:", f"{receipt['network']}")
    stage4_table.add_row("[green]+[/green] Smart Contract Address:", f"[bold green]{receipt['contract_address']}[/bold green]")
    stage4_table.add_row("[green]+[/green] Transaction Hash:", f"[bold cyan]{receipt['transaction_hash']}[/bold cyan]")
    stage4_table.add_row("[green]+[/green] Block Number:", f"#{receipt['block_number']}")
    stage4_table.add_row("[green]+[/green] Gas Used:", f"{receipt['gas_used']:,} gas")
    stage4_table.add_row("[green]+[/green] Verifier Address:", f"{receipt['verifier_address']}")
    console.print(stage4_table)

    # -------------------------------------------------------------
    # STAGE 5: Immediate On-Chain Re-Verification Check
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 5:[/bold yellow] [bold white]Immediate On-Chain Re-Verification Check[/bold white]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description="Re-querying contract to attest recorded data...", total=None)
        is_valid = blockchain.verify_integrity(
            evidence_hash=receipt["evidence_hash"],
            expected_media_hash=social_match.media_hash
        )
        on_chain_record = blockchain.fetch_record(receipt["evidence_hash"])

    if is_valid and on_chain_record["exists"]:
        summary_panel = Panel(
            f"[bold green]AUTHENTICITY VERIFIED: DATA RECORDED IMMUTABLY ON-CHAIN[/bold green]\n\n"
            f"[bold white]Evidence Root Hash:[/bold white] {receipt['evidence_hash']}\n"
            f"[bold white]Face Match URL:[/bold white] {on_chain_record['source_url']}\n"
            f"[bold white]Platform:[/bold white] {on_chain_record['platform']}\n"
            f"[bold white]Block Timestamp:[/bold white] {on_chain_record['timestamp']}\n"
            f"[bold white]Tamper-Evidence State:[/bold white] [bold green]UNCOMPROMISED (0% Deviation)[/bold green]\n\n"
            f"[dim]Run `python verify_record.py --evidence {os.path.join(output_dir, 'evidence_manifest.json')}` to verify anytime.[/dim]",
            title="[bold green]✔ PIPELINE EXECUTION SUCCESSFUL[/bold green]",
            border_style="green"
        )
        console.print(summary_panel)
    else:
        console.print(Panel("[bold red]VERIFICATION FAILED OR INTEGRITY COMPROMISED[/bold red]", border_style="red"))


def main():
    parser = argparse.ArgumentParser(
        description="VeriFace-Chain: End-to-End Face Scan Ingestion & Blockchain Attestation Pipeline"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="samples/real_sample_face.jpg",
        help="Path to input face scan image (default: samples/real_sample_face.jpg)"
    )
    parser.add_argument(
        "--chain",
        type=str,
        default="local",
        choices=["local", "testnet"],
        help="Blockchain execution mode: 'local' (simulated EVM) or 'testnet' (Polygon Amoy / Sepolia)"
    )
    parser.add_argument(
        "--rpc",
        type=str,
        default=None,
        help="Custom EVM RPC URL (required if --chain testnet and not set in .env)"
    )
    parser.add_argument(
        "--query-hint",
        type=str,
        default=None,
        help="Optional search query hint for web discovery"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for generated manifests, crops, and assets (default: output)"
    )

    args = parser.parse_args()
    run_pipeline(
        image_path=args.image,
        chain_mode=args.chain,
        rpc_url=args.rpc,
        output_dir=args.output,
        search_query_hint=args.query_hint
    )


if __name__ == "__main__":
    main()
