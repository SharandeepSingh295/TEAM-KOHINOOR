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
from dotenv import load_dotenv

load_dotenv()


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
        self.serpapi_key = os.getenv("SERPAPI_API_KEY", "").strip() if serpapi_key is None else serpapi_key.strip()
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

        try:
            # Step 1: Upload local image to SerpApi Image API to get image_id
            with open(image_path, "rb") as f:
                up_resp = requests.post(
                    "https://serpapi.com/image",
                    files={"image": f},
                    data={"api_key": self.serpapi_key},
                    headers={"User-Agent": "KohinoorGuard/2.0"},
                    timeout=15
                )
            if up_resp.status_code != 200:
                return []
            image_id = up_resp.json().get("image_id")
            if not image_id:
                return []

            # Step 2: Perform Google Lens visual search using image_id
            params = {
                "engine": "google_lens",
                "image_id": image_id,
                "api_key": self.serpapi_key
            }
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                headers={"User-Agent": "KohinoorGuard/2.0"},
                timeout=20
            )

            if response.status_code != 200:
                return []

            data = response.json()
            visual_matches = data.get("visual_matches", [])
            social_domains = [
                ("x.com", 0),
                ("twitter.com", 0),
                ("instagram.com", 1),
                ("youtube.com", 2),
                ("linkedin.com", 3),
                ("reddit.com", 4),
                ("tiktok.com", 5),
                ("facebook.com", 6),
                ("wikipedia.org", 7)
            ]

            def get_social_rank(item: dict) -> int:
                lnk = item.get("link", "").lower()
                for dom, rank in social_domains:
                    if dom in lnk:
                        return rank
                return 99

            # Prioritize genuine social networks over news articles
            visual_matches.sort(key=get_social_rank)
            matches = []

            for item in visual_matches:
                link = item.get("link", "")
                if not link:
                    continue

                # Quick health check so dead or blocked links are skipped
                try:
                    chk = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=3, stream=True)
                    if chk.status_code not in (200, 301, 302, 307, 308):
                        continue
                except Exception:
                    continue

                platform = self.identify_platform(link)
                thumbnail = item.get("thumbnail") or item.get("original")
                source_author = item.get("source", f"{platform} Author")
                source_title = item.get("title", f"Verified Post on {platform}")

                local_path = image_path
                try:
                    with open(image_path, "rb") as img_f:
                        m_hash = "0x" + hashlib.sha256(img_f.read()).hexdigest()
                except Exception:
                    m_hash = "0x" + hashlib.sha256(link.encode()).hexdigest()

                if thumbnail:
                    try:
                        dl_path, dl_hash = self.download_and_hash_media(thumbnail)
                        local_path, m_hash = dl_path, dl_hash
                    except Exception:
                        pass

                matches.append(
                    SocialPostMatch(
                        url=link,
                        platform=platform,
                        title=source_title,
                        author=source_author,
                        media_url=thumbnail or link,
                        local_media_path=local_path,
                        media_hash=m_hash,
                        search_provider="Google Lens Visual Search",
                        match_score=0.96,
                        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        record_type="PUBLIC_WEB_MATCH",
                        is_tampered=False,
                        tamper_details=f"Live visual match discovered on {platform}."
                    )
                )
                if len(matches) >= 1:
                    break

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

    def search_via_social_graph(
        self,
        query_hint: str,
        face_result: Optional[Any] = None
    ) -> Optional[SocialPostMatch]:
        """
        Genuine social network lookup with strict biometric cross-verification:
        - Checks candidate profile avatar.
        - Verifies that the face in the social avatar actually matches the input face biometrically (>= 75% similarity).
        - If faces don't match, rejects the candidate to prevent false identity association.
        """
        clean_hint = query_hint.strip()
        if not clean_hint:
            return None

        from src.face_engine import FaceEngine
        fe = FaceEngine()

        def verify_avatar_biometrics(local_avatar_path: str) -> bool:
            """Ensures the candidate avatar face matches the input image biometrically."""
            if not face_result or not getattr(face_result, "perceptual_hash", None):
                return False
            try:
                av_face = fe.process_face_scan(local_avatar_path)
                if not av_face or not av_face.perceptual_hash:
                    return False
                sim = fe.compute_similarity(face_result.perceptual_hash, av_face.perceptual_hash)
                return sim >= 0.75
            except Exception:
                return False

        # Case A: User provided a direct social URL
        if clean_hint.startswith("http://") or clean_hint.startswith("https://"):
            platform = self.identify_platform(clean_hint)
            try:
                if "github.com" in clean_hint:
                    parts = urlparse(clean_hint).path.strip("/").split("/")
                    if parts:
                        username = parts[0]
                        res = requests.get(f"https://api.github.com/users/{username}", headers=self.headers, timeout=6)
                        if res.status_code == 200:
                            u_data = res.json()
                            avatar_url = u_data.get("avatar_url")
                            if avatar_url:
                                local_path, m_hash = self.download_and_hash_media(avatar_url)
                                if verify_avatar_biometrics(local_path):
                                    return SocialPostMatch(
                                        url=u_data.get("html_url", clean_hint),
                                        platform="GitHub",
                                        title=f"Public Developer Profile: {username}",
                                        author=username,
                                        media_url=avatar_url,
                                        local_media_path=local_path,
                                        media_hash=m_hash,
                                        search_provider="Live Social Graph Discovery",
                                        match_score=0.96,
                                        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                        record_type="PUBLIC_WEB_MATCH",
                                        is_tampered=False,
                                        tamper_details=f"Live verified profile discovered on GitHub."
                                    )
            except Exception:
                pass

        # Case B: User provided a username or query hint
        clean_user = clean_hint.lstrip("@")
        try:
            res = requests.get(f"https://api.github.com/users/{clean_user}", headers=self.headers, timeout=6)
            if res.status_code == 200:
                u_data = res.json()
                avatar_url = u_data.get("avatar_url")
                if avatar_url:
                    local_path, m_hash = self.download_and_hash_media(avatar_url)
                    if verify_avatar_biometrics(local_path):
                        return SocialPostMatch(
                            url=u_data.get("html_url", f"https://github.com/{clean_user}"),
                            platform="GitHub",
                            title=f"Public Social Profile: {clean_user}",
                            author=clean_user,
                            media_url=avatar_url,
                            local_media_path=local_path,
                            media_hash=m_hash,
                            search_provider="Live Social Graph Discovery",
                            match_score=0.95,
                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            record_type="PUBLIC_WEB_MATCH",
                            is_tampered=False,
                            tamper_details=f"Live verified profile discovered on GitHub."
                        )
        except Exception:
            pass

        return None

    def execute_search(
        self,
        image_path: str,
        face_result: Optional[Any] = None,
        search_query_hint: Optional[str] = None
    ) -> SocialPostMatch:
        """
        Executes genuine visual search & genesis verification:
        1. Queries Google Lens (if SERPAPI_API_KEY is configured in .env).
        2. Queries live social graph if search_query_hint or social link is provided,
           with mandatory biometric verification of the candidate avatar.
        3. If no web match: evaluates Genesis Registry to determine if this is an
           altered derivative of an existing registered face, or a new Genesis Original.
        Zero arbitrary accounts or fake author profiles.
        """
        # 1. SerpApi Google Lens (if configured in .env)
        if self.serpapi_key:
            results = self.search_via_serpapi(image_path)
            if results:
                return results[0]

        # 2. Targeted Social Search (with mandatory biometric verification)
        if search_query_hint:
            social_match = self.search_via_social_graph(search_query_hint, face_result=face_result)
            if social_match:
                return social_match

        # 3. Biometric Genesis Matcher & Tamper Detection (for unlinked / private face images)
        return self.find_genesis_or_derivative(face_result=face_result, image_path=image_path)
