#!/usr/bin/env python3
"""
Deployment script for FaceVerificationRegistry.sol.
Supports:
  - Local simulated EVM (EthereumTesterProvider / py-evm)
  - Public EVM Testnets (e.g., Polygon Amoy, Ethereum Sepolia)
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from src.blockchain_client import BlockchainClient

console = Console()


def deploy(
    chain_mode: str = "local",
    rpc_url: str = None,
    private_key: str = None,
    output_receipt: str = "output/deployment_receipt.json"
):
    console.print(Panel(
        "[bold cyan]FaceVerificationRegistry Smart Contract Deployment[/bold cyan]\n"
        f"[dim]Deploying to target network mode: [bold white]{chain_mode.upper()}[/bold white][/dim]",
        border_style="cyan",
        expand=False
    ))

    # Check compiled contract
    artifact_path = "contracts/compiled_contract.json"
    if not os.path.exists(artifact_path):
        console.print("[yellow]Compiled contract artifact not found. Running compilation first...[/yellow]")
        exit_code = os.system("node compile_contract.js")
        if exit_code != 0:
            console.print("[bold red]Contract compilation failed![/bold red]")
            sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description=f"Connecting to {chain_mode.upper()} and deploying contract...", total=None)

        client = BlockchainClient(
            mode=chain_mode,
            rpc_url=rpc_url,
            private_key=private_key,
            contract_artifact_path=artifact_path
        )

    # Get deployment transaction details
    receipt_data = {
        "contract_name": "FaceVerificationRegistry",
        "contract_address": client.contract_address,
        "network": client.network_name,
        "mode": client.mode,
        "deployer_address": client.wallet_address,
        "timestamp": int(time.time()),
        "deployed_at_iso": datetime.now(timezone.utc).isoformat(),
        "abi": client.abi
    }

    # Save deployment receipt
    os.makedirs(os.path.dirname(output_receipt), exist_ok=True)
    with open(output_receipt, "w", encoding="utf-8") as f:
        json.dump(receipt_data, f, indent=2)

    # Display Deployment Summary
    summary_table = Table(title="🚀 Smart Contract Deployment Succeeded", border_style="green")
    summary_table.add_column("Property", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="bold white")

    summary_table.add_row("Contract Name", "FaceVerificationRegistry")
    summary_table.add_row("Deployed Address", f"[bold green]{client.contract_address}[/bold green]")
    summary_table.add_row("Network", client.network_name)
    summary_table.add_row("Deployer Wallet", client.wallet_address)
    summary_table.add_row("Artifact Receipt", output_receipt)

    console.print(summary_table)

    console.print(f"\n[green]✔ Contract successfully deployed and ready for on-chain attestations![/green]\n")
    return client.contract_address


def main():
    parser = argparse.ArgumentParser(
        description="Deploy FaceVerificationRegistry smart contract to EVM."
    )
    parser.add_argument(
        "--chain",
        choices=["local", "testnet"],
        default=os.getenv("BLOCKCHAIN_MODE", "local"),
        help="Target blockchain network: 'local' (simulated EVM) or 'testnet' (default: local)"
    )
    parser.add_argument(
        "--rpc",
        default=os.getenv("RPC_URL"),
        help="EVM RPC URL for testnet deployment"
    )
    parser.add_argument(
        "--private-key",
        default=os.getenv("PRIVATE_KEY"),
        help="Deployer private key (required for testnet)"
    )
    parser.add_argument(
        "--output",
        default="output/deployment_receipt.json",
        help="Path to write deployment receipt json"
    )

    args = parser.parse_args()
    deploy(
        chain_mode=args.chain,
        rpc_url=args.rpc,
        private_key=args.private_key,
        output_receipt=args.output
    )


if __name__ == "__main__":
    main()
