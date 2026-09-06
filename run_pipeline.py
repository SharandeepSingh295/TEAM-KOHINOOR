#!/usr/bin/env python3
"""
KohinoorGuard Pipeline Runner.
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
        "[bold cyan]KohinoorGuard[/bold cyan] : [bold white]End-to-End Face Verification Pipeline[/bold white]\n"
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

    os.makedirs(output_dir, exist_ok=True)

    # If an HTTP/HTTPS link is provided, download it locally
    if image_path.startswith(("http://", "https://")):
        console.print(f"[cyan]Fetching input image from web link:[/cyan] {image_path}")
        try:
            import requests
            resp = requests.get(image_path, timeout=20, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            resp.raise_for_status()
            downloaded_path = os.path.join(output_dir, "url_input_face.jpg")
            with open(downloaded_path, "wb") as f:
                f.write(resp.content)
            image_path = downloaded_path
            console.print(f"[green]✔ Image downloaded successfully to {downloaded_path}[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to download image from link:[/bold red] {e}")
            sys.exit(1)
    elif not os.path.exists(image_path):
        console.print(f"[bold red]Error:[/bold red] Input image '{image_path}' not found!")
        sys.exit(1)

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
    # STAGE 2: Web & Genesis Biometric Origin Discovery
    # -------------------------------------------------------------
    console.print("\n[bold yellow]STAGE 2:[/bold yellow] [bold white]Genuine Web Search & Genesis Biometric Registry[/bold white]")
    search_engine = WebSocialSearchEngine(output_dir=output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description="Checking live web index and Genesis biometric registry...", total=None)
        social_match = search_engine.execute_search(
            image_path=image_path,
            face_result=face_result,
            search_query_hint=search_query_hint
        )

    stage2_table = Table(show_header=False, box=None)
    stage2_table.add_row("[green]+[/green] Verification Status:", f"[bold {'red' if social_match.is_tampered else 'green'}]{social_match.record_type}[/bold {'red' if social_match.is_tampered else 'green'}]")
    stage2_table.add_row("[green]+[/green] Engine / Provider:", f"{social_match.search_provider}")
    stage2_table.add_row("[green]+[/green] Origin / Platform:", f"[bold magenta]{social_match.platform}[/bold magenta]")
    stage2_table.add_row("[green]+[/green] Verified Identifier URL:", f"[underline blue]{social_match.url}[/underline blue]")
    stage2_table.add_row("[green]+[/green] Media Asset Fingerprint:", f"[bold cyan]{social_match.media_hash}[/bold cyan]")
    if social_match.genesis_reference_hash:
        stage2_table.add_row("[yellow]![/yellow] Genesis Master Hash:", f"[bold yellow]{social_match.genesis_reference_hash}[/bold yellow]")
    if social_match.tamper_details:
        stage2_table.add_row("[yellow]![/yellow] Integrity Notice:", f"[italic white]{social_match.tamper_details}[/italic white]")
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

        extra_meta = {
            "perceptual_hash": face_result.perceptual_hash,
            "face_crop_path": face_result.crop_path,
            "record_type": social_match.record_type,
            "genesis_reference_hash": social_match.genesis_reference_hash,
            "is_tampered": social_match.is_tampered,
            "tamper_details": social_match.tamper_details
        }

        receipt = blockchain.record_verification(
            evidence_hash=manifest["evidence_hash"],
            face_hash=face_result.face_hash,
            media_hash=social_match.media_hash,
            source_url=social_match.url,
            platform=social_match.platform,
            extra_metadata=extra_meta
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

    if social_match.is_tampered:
        summary_panel = Panel(
            f"[bold red]⚠ ALTERED DERIVATIVE DETECTED (INTEGRITY ALERT)[/bold red]\n\n"
            f"[bold white]Status:[/bold white] [bold red]MODIFIED / ALTERED PHOTO[/bold red]\n"
            f"[bold white]Genesis Reference Master:[/bold white] {social_match.genesis_reference_hash}\n"
            f"[bold white]Notice:[/bold white] {social_match.tamper_details}\n"
            f"[bold white]On-Chain Attestation Root:[/bold white] {receipt['evidence_hash']}\n\n"
            f"[dim]The system successfully matched the subject to the Genesis proof and detected unauthorized pixel tampering.[/dim]",
            title="[bold red]✖ TAMPER / ALTERATION DETECTED[/bold red]",
            border_style="red"
        )
    elif is_valid and on_chain_record["exists"]:
        summary_panel = Panel(
            f"[bold green]GENESIS ORIGINAL: MASTER RECORD ANCHORED IMMUTABLY ON-CHAIN[/bold green]\n\n"
            f"[bold white]Evidence Root Hash:[/bold white] {receipt['evidence_hash']}\n"
            f"[bold white]Record Classification:[/bold white] [bold green]GENESIS MASTER REFERENCE[/bold green]\n"
            f"[bold white]Origin URI:[/bold white] {on_chain_record['source_url']}\n"
            f"[bold white]Registry:[/bold white] {on_chain_record['platform']}\n"
            f"[bold white]Block Timestamp:[/bold white] {on_chain_record['timestamp']}\n"
            f"[bold white]Integrity Status:[/bold white] [bold green]100% UNCOMPROMISED (Original Master)[/bold green]\n\n"
            f"[dim]Run `python verify_record.py --evidence {os.path.join(output_dir, 'evidence_manifest.json')}` anytime.[/dim]",
            title="[bold green]✔ PIPELINE EXECUTION SUCCESSFUL[/bold green]",
            border_style="green"
        )
    else:
        summary_panel = Panel("[bold red]Re-verification failed.[/bold red]", border_style="red")
    console.print(summary_panel)


def main():
    parser = argparse.ArgumentParser(
        description="KohinoorGuard: End-to-End Face Scan Ingestion & Blockchain Attestation Pipeline"
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
