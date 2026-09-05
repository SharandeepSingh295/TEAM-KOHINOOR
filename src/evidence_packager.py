"""
Cryptographic Evidence Packager for VeriFace-Chain.
Constructs canonical, deterministic evidence packages linking facial scans
to discovered web/social media content and produces cryptographic root hashes.
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional
from eth_utils import keccak

from src.face_engine import FaceScanResult
from src.search_engine import SocialPostMatch


class EvidencePackager:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def compute_evidence_hash(
        self,
        face_hash: str,
        media_hash: str,
        source_url: str,
        platform: str,
        timestamp: int,
        verifier_address: str
    ) -> str:
        """
        Calculates deterministic Keccak-256 evidence hash matching the Solidity smart contract:
        keccak256(abi.encodePacked(faceHash, mediaHash, sourceUrl, platform, timestamp, msg.sender))
        """
        # Clean hex prefixes
        fh_bytes = bytes.fromhex(face_hash[2:] if face_hash.startswith("0x") else face_hash)
        mh_bytes = bytes.fromhex(media_hash[2:] if media_hash.startswith("0x") else media_hash)
        addr_clean = verifier_address[2:] if verifier_address.startswith("0x") else verifier_address
        addr_bytes = bytes.fromhex(addr_clean.rjust(40, "0"))
        
        # Packed byte representation
        packed = (
            fh_bytes +
            mh_bytes +
            source_url.encode("utf-8") +
            platform.encode("utf-8") +
            timestamp.to_bytes(32, byteorder="big") +
            addr_bytes
        )
        
        root_hash = "0x" + keccak(packed).hex()
        return root_hash

    def create_package(
        self,
        face_result: FaceScanResult,
        social_match: SocialPostMatch,
        verifier_address: str = "0x0000000000000000000000000000000000000000",
        custom_timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Builds a canonical evidence manifest tying face scan and social post together.
        """
        current_time = custom_timestamp or int(time.time())

        evidence_hash = self.compute_evidence_hash(
            face_hash=face_result.face_hash,
            media_hash=social_match.media_hash,
            source_url=social_match.url,
            platform=social_match.platform,
            timestamp=current_time,
            verifier_address=verifier_address
        )

        manifest = {
            "version": "1.0.0",
            "evidence_hash": evidence_hash,
            "created_at_unix": current_time,
            "verifier_address": verifier_address,
            "face_data": {
                "face_hash": face_result.face_hash,
                "perceptual_hash": face_result.perceptual_hash,
                "bounding_box": list(face_result.bounding_box),
                "crop_path": face_result.crop_path,
                "confidence": face_result.confidence
            },
            "social_media_data": {
                "platform": social_match.platform,
                "post_url": social_match.url,
                "post_title": social_match.title,
                "post_author": social_match.author,
                "media_url": social_match.media_url,
                "local_media_path": social_match.local_media_path,
                "media_hash": social_match.media_hash,
                "search_provider": social_match.search_provider,
                "match_score": social_match.match_score
            },
            "blockchain_status": {
                "anchored": False,
                "network": None,
                "contract_address": None,
                "transaction_hash": None,
                "block_number": None
            }
        }

        # Write manifest file
        manifest_path = os.path.join(self.output_dir, "evidence_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def save_updated_manifest(self, manifest: Dict[str, Any], filepath: Optional[str] = None) -> str:
        """Saves updated manifest with blockchain receipt."""
        target_path = filepath or os.path.join(self.output_dir, "evidence_manifest.json")
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return target_path

    @staticmethod
    def load_manifest(manifest_path: str) -> Dict[str, Any]:
        """Loads and parses an existing evidence manifest file."""
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
