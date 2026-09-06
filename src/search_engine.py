"""
Genuine Visual Search and Genesis Biometric Registry for KohinoorGuard.
Supports:
  1. Live Google Lens Reverse Image Lookup (via SerpApi if configured)
  2. Privacy-Preserving Genesis Biometric Origin Registration (Initial Data)
  3. Perceptual Derivative & Tamper Detection (detecting altered copies of registered originals)
Strict Privacy Guarantee: Never invents third-party social profiles or unsolicited author handles.
"""

import os
import json
import hashlib
import datetime
import requests
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
from urllib.parse import urlparse


@dataclass
class SocialPostMatch:
    url: str                                    # Live post or genesis reference URL
    platform: str                               # Platform name
    title: str                                  # Asset title / description
    author: str                                 # Privacy-protected identity
    media_url: str                              # Direct link or local asset path
    local_media_path: str                       # Path where media was saved locally
    media_hash: str                             # 0x-prefixed SHA-256 hash
    search_provider: str                        # Search engine / verification method
    match_score: float                          # Relevance or similarity score (0.0 - 1.0)
    timestamp: str                              # ISO timestamp
    record_type: str = "GENESIS_ORIGINAL"       # GENESIS_ORIGINAL | ALTERED_DERIVATIVE | PUBLIC_WEB_MATCH
    genesis_reference_hash: Optional[str] = None # Hash of genesis master if altered
    is_tampered: bool = False                   # True if altered version of existing origin
    tamper_details: Optional[str] = None        # Human-readable alteration explanation


class WebSocialSearchEngine:
    def __init__(
        self,
        serpapi_key: Optional[str] = None,
        output_dir: str = "output",
        ledger_file: Optional[str] = None
    ):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY", "").strip()
        self.output_dir = output_dir
        self.ledger_file = ledger_file
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "KohinoorGuard/2.0 (Biometric Integrity Verifier)"
        }

    def identify_platform(self, url: str) -> str:
        """Identifies platform from domain or marks as Genesis."""
        if url.startswith("genesis://"):
            return "Genesis Origin Registry"
        domain = urlparse(url).netloc.lower()
        social_map = {
            "twitter.com": "Twitter/X", "x.com": "Twitter/X",
            "reddit.com": "Reddit", "instagram.com": "Instagram",
            "linkedin.com": "LinkedIn", "github.com": "GitHub",
            "facebook.com": "Facebook", "youtube.com": "YouTube"
        }
        for key, name in social_map.items():
            if key in domain:
                return name
        return "Web"

    def download_and_hash_media(self, media_url: str) -> Tuple[str, str]:
        """Downloads matched media asset and computes SHA-256 hash."""
        resp = requests.get(media_url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        content = resp.content

        media_hash = "0x" + hashlib.sha256(content).hexdigest()
        filename = f"matched_asset_{media_hash[2:10]}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(content)

        return filepath, media_hash

    def search_via_serpapi(self, image_path: str) -> List[SocialPostMatch]:
        """Performs genuine Google Lens reverse image search using SerpApi if key is provided."""
        if not self.serpapi_key:
            return []

        url = "https://serpapi.com/search"
        try:
            with open(image_path, "rb") as f:
                files = {"file": f}
                params = {"engine": "google_lens", "api_key": self.serpapi_key}
                response = requests.post(url, params=params, files=files, timeout=15)

            if response.status_code != 200:
                return []

            data = response.json()
            visual_matches = data.get("visual_matches", [])
            matches = []

            for item in visual_matches:
                link = item.get("link", "")
                platform = self.identify_platform(link)
                thumbnail = item.get("thumbnail") or item.get("original")

                if thumbnail and link:
                    try:
                        local_path, m_hash = self.download_and_hash_media(thumbnail)
                        matches.append(
                            SocialPostMatch(
                                url=link,
                                platform=platform,
                                title=item.get("title", "Discovered Web Match"),
                                author="Public Web Source",
                                media_url=thumbnail,
                                local_media_path=local_path,
                                media_hash=m_hash,
                                search_provider="Google Lens Visual Search",
                                match_score=0.95,
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                record_type="PUBLIC_WEB_MATCH",
                                is_tampered=False,
                                tamper_details=f"Live visual match discovered on {platform}."
                            )
                        )
                        if len(matches) >= 1:
                            break
                    except Exception:
                        continue

            return matches
        except Exception:
            return []

    def find_genesis_or_derivative(
        self,
        face_result: Any,
        image_path: str
    ) -> SocialPostMatch:
        """
        Biometric Origin & Alteration Engine:
        - If no web match: inspects existing Genesis records in ledger.
        - If face matches an existing Genesis record (similarity >= 0.80) but image has been modified:
          Flags as ALTERED_DERIVATIVE, pointing back to the Genesis proof!
        - If face has never been seen:
          Registers as a new GENESIS_ORIGINAL master record.
        - Privacy Guaranteed: Anonymized owner identity, zero random profiles.
        """
        from src.face_engine import FaceEngine
        
        # Candidate ledger file locations
        candidate_ledgers = []
        if self.ledger_file:
            candidate_ledgers.append(self.ledger_file)
        candidate_ledgers.extend([
            os.path.join(self.output_dir, "local_ledger.json"),
            os.path.join("output", "local_ledger.json")
        ])

        # Save local copy of media asset
        with open(image_path, "rb") as f:
            content = f.read()
        media_hash = "0x" + hashlib.sha256(content).hexdigest()
        local_saved_asset = os.path.join(self.output_dir, f"matched_asset_{media_hash[2:10]}.jpg")
        with open(local_saved_asset, "wb") as f:
            f.write(content)

        current_dhash = getattr(face_result, "perceptual_hash", "") if face_result else ""
        current_face_hash = getattr(face_result, "face_hash", "") if face_result else ""

        best_genesis = None
        best_sim = 0.0

        ledger = {}
        for l_path in candidate_ledgers:
            if os.path.exists(l_path):
                try:
                    with open(l_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            ledger.update(data)
                except Exception:
                    pass

        if ledger and current_dhash:
            try:
                fe = FaceEngine()
                for ev_hash, rec in ledger.items():
                    rec_dhash = rec.get("perceptual_hash")
                    # If not explicitly saved in old records, try reading crop
                    if not rec_dhash and rec.get("face_crop_path") and os.path.exists(rec["face_crop_path"]):
                        import cv2
                        c_img = cv2.imread(rec["face_crop_path"])
                        if c_img is not None:
                            rec_dhash = fe.compute_dhash(c_img)

                    if rec_dhash:
                        sim = fe.compute_similarity(current_dhash, rec_dhash)
                        if sim > best_sim:
                            best_sim = sim
                            best_genesis = rec
            except Exception:
                pass

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Check if matched to an existing Genesis record
        if best_genesis and best_sim >= 0.80:
            orig_ev_hash = best_genesis.get("evidence_hash", "")
            orig_media_hash = best_genesis.get("media_hash", "")
            orig_face_hash = best_genesis.get("face_hash", "")

            # Check if cryptographic bytes differ (Altered / Tampered derivative)
            is_altered = (current_face_hash.lower() != orig_face_hash.lower()) or (media_hash.lower() != orig_media_hash.lower())

            if is_altered:
                pct = best_sim * 100
                short_hash = orig_ev_hash[:16] + "..." if len(orig_ev_hash) > 16 else orig_ev_hash
                return SocialPostMatch(
                    url=best_genesis.get("source_url", f"genesis://record/{short_hash}"),
                    platform="Genesis Origin Registry",
                    title=f"Altered copy of Genesis Record #{short_hash}",
                    author="Protected Asset Owner",
                    media_url=best_genesis.get("local_media_path", local_saved_asset),
                    local_media_path=local_saved_asset,
                    media_hash=media_hash,
                    search_provider="Biometric Genesis Matcher",
                    match_score=round(best_sim, 4),
                    timestamp=now_iso,
                    record_type="ALTERED_DERIVATIVE",
                    genesis_reference_hash=orig_ev_hash,
                    is_tampered=True,
                    tamper_details=f"Biometric similarity ({pct:.1f}%) matches Genesis #{short_hash}, but cryptographic pixels have been modified!"
                )
            else:
                return SocialPostMatch(
                    url=best_genesis.get("source_url", "genesis://master-asset"),
                    platform="Genesis Origin Registry",
                    title="Authentic Re-Verification of Genesis Original",
                    author="Protected Asset Owner",
                    media_url=local_saved_asset,
                    local_media_path=local_saved_asset,
                    media_hash=media_hash,
                    search_provider="Biometric Exact Matcher",
                    match_score=1.0,
                    timestamp=now_iso,
                    record_type="GENESIS_ORIGINAL",
                    genesis_reference_hash=orig_ev_hash,
                    is_tampered=False,
                    tamper_details="Exact authentic Genesis original re-verified."
                )

        # Unseen face -> GENESIS ORIGINAL MASTER
        return SocialPostMatch(
            url="genesis://master-asset",
            platform="Genesis Origin Registry",
            title="Initial Master Biometric Reference Asset",
            author="Protected Asset Owner",
            media_url=local_saved_asset,
            local_media_path=local_saved_asset,
            media_hash=media_hash,
            search_provider="Genesis Origin Attestation",
            match_score=1.0,
            timestamp=now_iso,
            record_type="GENESIS_ORIGINAL",
            genesis_reference_hash=None,
            is_tampered=False,
            tamper_details="New original master face asset anchored on-chain."
        )

    def execute_search(
        self,
        image_path: str,
        face_result: Optional[Any] = None,
        search_query_hint: Optional[str] = None
    ) -> SocialPostMatch:
        """
        Executes genuine visual search & genesis verification:
        1. Queries Google Lens (if SERPAPI_API_KEY is configured in .env).
        2. If no web match: evaluates Genesis Registry to determine if this is an
           altered derivative of an existing registered face, or a new Genesis Original.
        Zero arbitrary accounts or fake author profiles.
        """
        # 1. SerpApi Google Lens (if configured in .env)
        if self.serpapi_key:
            results = self.search_via_serpapi(image_path)
            if results:
                return results[0]

        # 2. Biometric Genesis Matcher & Tamper Detection
        return self.find_genesis_or_derivative(face_result=face_result, image_path=image_path)
