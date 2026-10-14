#!/usr/bin/env python3
"""
KohinoorGuard Cryptographic Certificate Generator CLI.
Extracts verified biometric records from the smart contract / local ledger
and renders a self-contained, tamper-evident HTML Certificate of Authenticity.
"""

import os
import sys
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.blockchain_client import BlockchainClient, LOCAL_LEDGER_FILE
from src.certificate_generator import CertificateGenerator

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]KohinoorGuard Certificate Issuer[/bold cyan] : [bold white]Cryptographic Biometric Attestation[/bold white]\n"
        "[dim]Self-Contained Verifiable Certificates &bull; SVG Hologram Seal &bull; Scannable QR Proof[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def generate_certificate(
    evidence_hash: str = None,
    manifest_path: str = None,
    chain_mode: str = "local",
    output_dir: str = "output/certificates",
    output_filename: str = None
):
    print_banner()

    record_data = {}
    forensic_data = None

    # Load from manifest if provided
    if manifest_path:
        if not os.path.exists(manifest_path):
            console.print(f"[bold red]Error:[/bold red] Manifest file not found: {manifest_path}")
            sys.exit(1)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        evidence_hash = manifest.get("evidence_hash")
        b_status = manifest.get("blockchain_status", {})
        record_data = {
            "evidence_hash": evidence_hash,
            "face_hash": manifest.get("face_data", {}).get("face_hash"),
            "media_hash": manifest.get("social_media_data", {}).get("media_hash"),
            "platform": manifest.get("social_media_data", {}).get("platform"),
            "source_url": manifest.get("social_media_data", {}).get("post_url"),
            "verifier": manifest.get("verifier_address"),
            "block_number": b_status.get("block_number", 1),
            "transaction_hash": b_status.get("transaction_hash", "0x" + "0" * 64),
            "contract_address": b_status.get("contract_address", "0xF2E246BB7678C62c6AbA282D7B70204689c8395b"),
            "timestamp": manifest.get("created_at_unix"),
            "face_crop_path": manifest.get("face_data", {}).get("crop_path"),
            "record_type": manifest.get("social_media_data", {}).get("search_provider", "GENESIS_ORIGINAL"),
            "is_tampered": False
        }

    # Query from blockchain / ledger
    elif evidence_hash:
        client = BlockchainClient(mode=chain_mode)
        on_chain = client.fetch_record(evidence_hash)
        if not on_chain.get("exists"):
            console.print(f"[bold red]Error:[/bold red] Evidence record '{evidence_hash}' does not exist on blockchain!")
            sys.exit(1)

        # Merge local ledger extra metadata if available
        local_records = client._load_local_ledger()
        local_entry = local_records.get(evidence_hash.lower(), {})

        record_data = {
            "evidence_hash": evidence_hash,
            "face_hash": on_chain.get("face_hash"),
            "media_hash": on_chain.get("media_hash"),
            "platform": on_chain.get("platform"),
            "source_url": on_chain.get("source_url"),
            "verifier": on_chain.get("verifier"),
            "block_number": local_entry.get("block_number", 1),
            "transaction_hash": local_entry.get("transaction_hash", "0x" + "0" * 64),
            "contract_address": client.contract_address,
            "timestamp": on_chain.get("timestamp"),
            "face_crop_path": local_entry.get("face_crop_path"),
            "record_type": local_entry.get("record_type", "GENESIS_ORIGINAL"),
            "is_tampered": local_entry.get("is_tampered", False)
        }
    else:
        console.print("[bold red]Error:[/bold red] Must specify either --hash <EVIDENCE_HASH> or --manifest <PATH>")
        sys.exit(1)

    # Initialize generator
    os.makedirs(output_dir, exist_ok=True)
    generator = CertificateGenerator(output_dir=output_dir)

    filename = output_filename or f"certificate_{evidence_hash[:10]}.html"
    cert_path = generator.generate_certificate_html(
        record_data=record_data,
        forensic_data=forensic_data,
        save_filename=filename
    )

    console.print(Panel(
        f"[bold white]Certificate File:[/bold white] [bold green]{cert_path}[/bold green]\n"
        f"[bold white]Evidence Hash:[/bold white] [bold cyan]{record_data['evidence_hash']}[/bold cyan]\n"
        f"[bold white]Classification:[/bold white] {record_data['record_type']}\n"
        f"[bold white]Features:[/bold white] Embedded Base64 Crop &bull; Scannable QR Stamp &bull; Hologram Seal",
        title="[bold green]✔ Cryptographic Certificate Issued[/bold green]",
        border_style="green"
    ))

    return cert_path


def main():
    parser = argparse.ArgumentParser(description="Generate Cryptographic Biometric Certificate of Authenticity")
    parser.add_argument("--hash", "-H", type=str, default=None, help="Evidence hash of on-chain record")
    parser.add_argument("--manifest", "-m", type=str, default=None, help="Path to evidence manifest JSON")
    parser.add_argument("--chain-mode", "-c", type=str, default="local", choices=["local", "testnet"], help="Chain mode")
    parser.add_argument("--output-dir", "-d", type=str, default="output/certificates", help="Directory to save certificate")
    parser.add_argument("--output", "-o", type=str, default=None, help="Certificate output filename")

    args = parser.parse_args()
    generate_certificate(
        evidence_hash=args.hash,
        manifest_path=args.manifest,
        chain_mode=args.chain_mode,
        output_dir=args.output_dir,
        output_filename=args.output
    )


if __name__ == "__main__":
    main()
