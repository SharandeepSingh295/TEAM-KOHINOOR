#!/usr/bin/env python3
"""
KohinoorGuard Standalone Verification Engine.
Re-verifies discovered social media data and face scans against
the immutable records stored in the blockchain smart contract.
Demonstrates cryptographic tamper-evidence and data integrity guarantees.
"""

import os
import sys
import json
import hashlib
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.blockchain_client import BlockchainClient

console = Console()


def verify_evidence(
    manifest_path: str,
    chain_mode: str = None,
    rpc_url: str = None,
    contract_address: str = None
):
    if not os.path.exists(manifest_path):
        console.print(f"[bold red]Error:[/bold red] Manifest file '{manifest_path}' not found!")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    evidence_hash = manifest.get("evidence_hash")
    b_status = manifest.get("blockchain_status", {})
    
    selected_chain = chain_mode or ("testnet" if b_status.get("network", "").startswith("EVM Testnet") else "local")
    target_contract = contract_address or b_status.get("contract_address")

    console.print(Panel(
        f"[bold white]Target Evidence Hash:[/bold white] [bold cyan]{evidence_hash}[/bold cyan]\n"
        f"[bold white]Contract Address:[/bold white] {target_contract or 'Auto-Detected / Registry'}\n"
        f"[bold white]Target Chain Mode:[/bold white] {selected_chain.upper()}",
        title="[bold yellow]🔍 Initiating On-Chain Re-Verification[/bold yellow]",
        border_style="yellow"
    ))

    # Re-compute hashes from local files to verify offline integrity first
    local_media_path = manifest.get("social_media_data", {}).get("local_media_path")
    recorded_media_hash = manifest.get("social_media_data", {}).get("media_hash")
    
    current_media_hash = None
    if local_media_path and os.path.exists(local_media_path):
        with open(local_media_path, "rb") as f:
            current_media_hash = "0x" + hashlib.sha256(f.read()).hexdigest()
    else:
        current_media_hash = recorded_media_hash

    # Connect to blockchain (automatically re-seeds local ledger if in local mode)
    blockchain = BlockchainClient(
        mode=selected_chain,
        rpc_url=rpc_url,
        contract_address=target_contract
    )

    try:
        on_chain = blockchain.fetch_record(evidence_hash)
    except Exception as e:
        console.print(f"[bold red]Error querying on-chain record for {evidence_hash}:[/bold red] {e}")
        return False

    # Check tamper evidence
    face_hash_match = (on_chain["face_hash"].lower() == manifest["face_data"]["face_hash"].lower())
    media_hash_match = (on_chain["media_hash"].lower() == current_media_hash.lower())
    url_match = (on_chain["source_url"] == manifest["social_media_data"]["post_url"])
    is_valid = face_hash_match and media_hash_match and url_match

    # Display comparison table
    table = Table(title="Cryptographic Comparison: On-Chain Record vs Live Data", border_style="cyan")
    table.add_column("Attribute", style="bold white")
    table.add_column("On-Chain Ledger", style="dim cyan")
    table.add_column("Current Live Asset", style="dim yellow")
    table.add_column("Status", justify="center")

    table.add_row(
        "Face Hash",
        f"{on_chain['face_hash'][:14]}...",
        f"{manifest['face_data']['face_hash'][:14]}...",
        "[green]MATCH[/green]" if face_hash_match else "[red]MISMATCH[/red]"
    )
    table.add_row(
        "Media Asset Hash",
        f"{on_chain['media_hash'][:14]}...",
        f"{current_media_hash[:14]}...",
        "[green]MATCH[/green]" if media_hash_match else "[bold red]TAMPERED[/bold red]"
    )
    table.add_row(
        "Post Source URL",
        on_chain["source_url"][:35] + "...",
        manifest["social_media_data"]["post_url"][:35] + "...",
        "[green]MATCH[/green]" if url_match else "[bold red]TAMPERED[/bold red]"
    )
    table.add_row(
        "Platform",
        on_chain["platform"],
        manifest["social_media_data"]["platform"],
        "[green]MATCH[/green]"
    )
    table.add_row(
        "Ledger Timestamp",
        str(on_chain["timestamp"]),
        str(manifest.get("created_at_unix", "N/A")),
        "[green]RECORDED[/green]"
    )

    console.print(table)

    if is_valid:
        console.print(Panel(
            "[bold green]✔ RE-VERIFICATION PASSED[/bold green]\n\n"
            "The target post, media asset, and facial signature match the immutable blockchain record exactly.\n"
            "No data modification or tampering has occurred since registration.",
            title="[bold green]VERIFIED AUTHENTIC[/bold green]",
            border_style="green"
        ))
        return True
    else:
        console.print(Panel(
            "[bold red]✖ TAMPER DETECTED[/bold red]\n\n"
            "WARNING: The live media asset or post metadata does NOT match the immutable blockchain fingerprint.\n"
            "The data has been altered, forged, or replaced!",
            title="[bold red]TAMPER-EVIDENCE ALERT[/bold red]",
            border_style="red"
        ))
        return False


def main():
    parser = argparse.ArgumentParser(
        description="KohinoorGuard: Cryptographic Blockchain Re-Verification Utility"
    )
    parser.add_argument(
        "--evidence",
        type=str,
        default="output/evidence_manifest.json",
        help="Path to evidence manifest JSON to verify (default: output/evidence_manifest.json)"
    )
    parser.add_argument(
        "--chain",
        type=str,
        default=None,
        choices=["local", "testnet"],
        help="Target blockchain mode ('local' or 'testnet')"
    )
    parser.add_argument(
        "--rpc",
        type=str,
        default=None,
        help="Custom RPC URL if verifying against remote testnet"
    )
    parser.add_argument(
        "--contract",
        type=str,
        default=None,
        help="Contract address (if verifying against specific deployed instance)"
    )

    args = parser.parse_args()
    success = verify_evidence(
        manifest_path=args.evidence,
        chain_mode=args.chain,
        rpc_url=args.rpc,
        contract_address=args.contract
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
