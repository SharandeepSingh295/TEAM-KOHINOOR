"""
Blockchain Client and Web3 Interface for VeriFace-Chain.
Manages smart contract deployment, evidence registration, and on-chain
cryptographic verification supporting both local EVM and public testnets.
"""

import os
import json
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account


LOCAL_LEDGER_FILE = os.path.join("output", "local_ledger.json")


class BlockchainClient:
    def __init__(
        self,
        mode: str = "local",
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        contract_address: Optional[str] = None,
        contract_artifact_path: str = "contracts/compiled_contract.json"
    ):
        self.mode = mode.lower()
        self.contract_artifact_path = contract_artifact_path
        self.contract_address = contract_address

        # Load compiled contract ABI and Bytecode
        if not os.path.exists(self.contract_artifact_path):
            raise FileNotFoundError(
                f"Compiled contract artifact not found at {self.contract_artifact_path}. "
                "Run `node compile_contract.js` to compile the smart contract."
            )

        with open(self.contract_artifact_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
            self.abi = artifact["abi"]
            self.bytecode = artifact["bytecode"]

        # Initialize Web3 provider based on mode
        if self.mode == "testnet":
            url = rpc_url or os.getenv("RPC_URL", "https://rpc-amoy.polygon.technology")
            self.w3 = Web3(Web3.HTTPProvider(url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to testnet RPC at {url}")

            pk = private_key or os.getenv("PRIVATE_KEY")
            if not pk or pk.startswith("0x00000000"):
                raise ValueError("Valid PRIVATE_KEY is required for testnet mode.")
            
            self.account = Account.from_key(pk)
            self.wallet_address = self.account.address
            self.network_name = f"EVM Testnet (Chain ID: {self.w3.eth.chain_id})"
        else:
            # Mode: local (EthereumTesterProvider)
            from web3.providers.eth_tester import EthereumTesterProvider
            self.provider = EthereumTesterProvider()
            self.w3 = Web3(self.provider)
            self.account = None
            self.wallet_address = self.w3.eth.accounts[0]
            self.network_name = "Simulated Local EVM (Py-EVM / Eth-Tester)"

        # Initialize contract instance
        if self.contract_address and self.mode == "testnet":
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.abi
            )
        else:
            # Auto-deploy contract (always needed for fresh local EVM in a new process)
            self.deploy_contract()

        # In local mode, restore any previously anchored records
        if self.mode == "local":
            self._restore_local_ledger()

    def deploy_contract(self) -> str:
        """
        Deploys FaceVerificationRegistry.sol to the active blockchain.
        """
        contract_factory = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)

        if self.mode == "testnet":
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            tx = contract_factory.constructor().build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": 3000000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            deployed_address = receipt.contractAddress
        else:
            # Local deployment
            tx_hash = contract_factory.constructor().transact({"from": self.wallet_address})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            deployed_address = receipt.contractAddress

        self.contract_address = deployed_address
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.abi
        )
        return self.contract_address

    def _to_bytes32(self, val: str) -> bytes:
        """Helper to ensure 32-byte hex bytes."""
        clean = val[2:] if val.startswith("0x") else val
        return bytes.fromhex(clean.rjust(64, "0"))

    def _persist_local_ledger(self, record_data: Dict[str, Any]):
        """Persists local records to disk for cross-process local testing."""
        os.makedirs(os.path.dirname(LOCAL_LEDGER_FILE), exist_ok=True)
        ledger = {}
        if os.path.exists(LOCAL_LEDGER_FILE):
            try:
                with open(LOCAL_LEDGER_FILE, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except Exception:
                ledger = {}
        ledger[record_data["evidence_hash"]] = record_data
        with open(LOCAL_LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)

    def _restore_local_ledger(self):
        """Restores persisted records onto the in-memory provider."""
        if not os.path.exists(LOCAL_LEDGER_FILE):
            return
        try:
            with open(LOCAL_LEDGER_FILE, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            for ev_hash, item in ledger.items():
                ev_b = self._to_bytes32(ev_hash)
                f_b = self._to_bytes32(item["face_hash"])
                m_b = self._to_bytes32(item["media_hash"])
                try:
                    self.contract.functions.recordVerification(
                        ev_b, f_b, m_b, item["source_url"], item["platform"]
                    ).transact({"from": self.wallet_address})
                except Exception:
                    pass
        except Exception:
            pass

    def record_verification(
        self,
        evidence_hash: str,
        face_hash: str,
        media_hash: str,
        source_url: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Submits verification record to the blockchain registry using canonical evidenceHash.
        Returns transaction receipt and evidence details.
        """
        ev_bytes = self._to_bytes32(evidence_hash)
        f_bytes = self._to_bytes32(face_hash)
        m_bytes = self._to_bytes32(media_hash)

        if self.mode == "testnet":
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            func_call = self.contract.functions.recordVerification(
                ev_bytes, f_bytes, m_bytes, source_url, platform
            )
            tx = func_call.build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        else:
            tx_hash = self.contract.functions.recordVerification(
                ev_bytes, f_bytes, m_bytes, source_url, platform
            ).transact({"from": self.wallet_address})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        # Parse logs to extract event
        event_logs = self.contract.events.FaceMatchVerified().process_receipt(receipt)
        timestamp = event_logs[0]["args"]["timestamp"] if event_logs else 0

        result = {
            "evidence_hash": evidence_hash,
            "face_hash": face_hash,
            "media_hash": media_hash,
            "source_url": source_url,
            "platform": platform,
            "transaction_hash": "0x" + tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "contract_address": self.contract_address,
            "network": self.network_name,
            "verifier_address": self.wallet_address,
            "timestamp": timestamp,
            "status": "CONFIRMED"
        }

        if self.mode == "local":
            self._persist_local_ledger(result)

        return result

    def fetch_record(self, evidence_hash: str) -> Dict[str, Any]:
        """
        Queries smart contract for stored record by evidence hash.
        """
        ev_bytes = self._to_bytes32(evidence_hash)
        record = self.contract.functions.getRecord(ev_bytes).call()
        
        return {
            "face_hash": "0x" + record[0].hex(),
            "media_hash": "0x" + record[1].hex(),
            "source_url": record[2],
            "platform": record[3],
            "timestamp": record[4],
            "verifier": record[5],
            "exists": record[6]
        }

    def verify_integrity(self, evidence_hash: str, expected_media_hash: str) -> bool:
        """
        Directly queries the smart contract's verifyIntegrity view method.
        """
        ev_bytes = self._to_bytes32(evidence_hash)
        m_bytes = self._to_bytes32(expected_media_hash)
        return self.contract.functions.verifyIntegrity(ev_bytes, m_bytes).call()
