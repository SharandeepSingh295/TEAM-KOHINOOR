"""
Automated Test Suite for KohinoorGuard.
Tests face detection, search engine asset hashing, evidence packaging,
and end-to-end blockchain smart contract attestation & tampering detection.
"""

import os
import hashlib
import uuid
import pytest
from src.face_engine import FaceEngine
from src.search_engine import WebSocialSearchEngine, SocialPostMatch
from src.evidence_packager import EvidencePackager
from src.blockchain_client import BlockchainClient
from samples.generate_sample import create_synthetic_face


@pytest.fixture(scope="session")
def sample_image():
    path = "samples/sample_face.jpg"
    if not os.path.exists(path):
        create_synthetic_face(path)
    return path


def test_face_detection_and_encoding(sample_image):
    engine = FaceEngine()
    result = engine.process_face_scan(sample_image, output_crop_dir="output/test_crops")

    # Assert valid SHA-256 hex string with 0x prefix
    assert result.face_hash.startswith("0x")
    assert len(result.face_hash) == 66  # '0x' + 64 hex chars

    # Assert perceptual hash is a valid binary string
    assert len(result.perceptual_hash) == 64
    assert set(result.perceptual_hash).issubset({"0", "1"})

    # Assert crop was saved
    assert os.path.exists(result.crop_path)
    assert result.image_width > 0
    assert result.image_height > 0


def test_search_engine_platform_identification():
    engine = WebSocialSearchEngine(output_dir="output/test_search")
    
    assert engine.identify_platform("https://x.com/username/status/123") == "Twitter/X"
    assert engine.identify_platform("https://twitter.com/user/status/456") == "Twitter/X"
    assert engine.identify_platform("https://www.reddit.com/r/tech/comments/xyz") == "Reddit"
    assert engine.identify_platform("https://linkedin.com/in/profile") == "LinkedIn"
    assert engine.identify_platform("https://instagram.com/p/abc1234") == "Instagram"
    assert engine.identify_platform("https://example.com/page") == "Web"


def test_evidence_packaging_determinism(sample_image):
    face_engine = FaceEngine()
    face_result = face_engine.process_face_scan(sample_image, output_crop_dir="output/test_crops")

    social_match = SocialPostMatch(
        url="https://x.com/example/status/987654321",
        platform="Twitter/X",
        title="Sample verification post",
        author="@testuser",
        media_url="https://example.com/image.jpg",
        local_media_path="output/test_search/dummy.jpg",
        media_hash="0x" + hashlib.sha256(b"test_image_bytes").hexdigest(),
        search_provider="Unit Test",
        match_score=0.99,
        timestamp="2026-09-05T00:00:00Z"
    )

    packager = EvidencePackager(output_dir="output/test_evidence")
    fixed_ts = 1757000000
    verifier = "0x1111111111111111111111111111111111111111"

    manifest = packager.create_package(
        face_result=face_result,
        social_match=social_match,
        verifier_address=verifier,
        custom_timestamp=fixed_ts
    )

    # Recompute independently to assert absolute mathematical determinism
    expected_hash = packager.compute_evidence_hash(
        face_hash=face_result.face_hash,
        media_hash=social_match.media_hash,
        source_url=social_match.url,
        platform=social_match.platform,
        timestamp=fixed_ts,
        verifier_address=verifier
    )

    assert manifest["evidence_hash"] == expected_hash
    assert manifest["evidence_hash"].startswith("0x")
    assert len(manifest["evidence_hash"]) == 66


def test_blockchain_smart_contract_full_cycle():
    client = BlockchainClient(mode="local")
    assert client.contract_address is not None
    assert client.contract_address.startswith("0x")

    test_face_hash = "0x" + hashlib.sha256(b"sample_face").hexdigest()
    test_media_hash = "0x" + hashlib.sha256(b"sample_media").hexdigest()
    test_url = "https://reddit.com/r/technology/post123"
    test_platform = "Reddit"

    unique_id = uuid.uuid4().hex
    test_evidence_hash = "0x" + hashlib.sha256(f"sample_evidence_bundle_{unique_id}".encode()).hexdigest()

    # 1. Record on-chain
    receipt = client.record_verification(
        evidence_hash=test_evidence_hash,
        face_hash=test_face_hash,
        media_hash=test_media_hash,
        source_url=test_url,
        platform=test_platform
    )

    evidence_hash = receipt["evidence_hash"]
    assert receipt["status"] == "CONFIRMED"
    assert receipt["block_number"] >= 1
    assert receipt["gas_used"] > 0

    # 2. Query record from blockchain
    record = client.fetch_record(evidence_hash)
    assert record["face_hash"].lower() == test_face_hash.lower()
    assert record["media_hash"].lower() == test_media_hash.lower()
    assert record["source_url"] == test_url
    assert record["platform"] == test_platform
    assert record["exists"] is True

    # 3. Test integrity verification (Authentic state)
    is_authentic = client.verify_integrity(evidence_hash, test_media_hash)
    assert is_authentic is True

    # 4. Test Tamper Detection (Simulate modified/altered media asset)
    tampered_media_hash = "0x" + hashlib.sha256(b"tampered_fake_media").hexdigest()
    is_tampered_valid = client.verify_integrity(evidence_hash, tampered_media_hash)
    assert is_tampered_valid is False, "Smart contract MUST detect cryptographic tampering!"


def test_genesis_origin_and_altered_derivative_detection(sample_image, tmp_path):
    import cv2
    face_engine = FaceEngine()
    orig_face = face_engine.process_face_scan(sample_image, output_crop_dir=str(tmp_path))

    tmp_ledger = str(tmp_path / "local_ledger.json")
    search_engine = WebSocialSearchEngine(output_dir=str(tmp_path), ledger_file=tmp_ledger)
    orig_match = search_engine.execute_search(image_path=sample_image, face_result=orig_face)

    # First upload of unseen face MUST be classified as Genesis Original
    assert orig_match.record_type == "GENESIS_ORIGINAL"
    assert orig_match.is_tampered is False
    assert orig_match.platform == "Genesis Origin Registry"

    # Package evidence
    packager = EvidencePackager(output_dir=str(tmp_path))
    manifest = packager.create_package(face_result=orig_face, social_match=orig_match)

    client = BlockchainClient(mode="local", ledger_file=tmp_ledger)
    extra_meta = {
        "perceptual_hash": orig_face.perceptual_hash,
        "face_crop_path": orig_face.crop_path,
        "record_type": orig_match.record_type,
        "is_tampered": False
    }
    receipt = client.record_verification(
        evidence_hash=manifest["evidence_hash"],
        face_hash=orig_face.face_hash,
        media_hash=orig_match.media_hash,
        source_url=orig_match.url,
        platform=orig_match.platform,
        extra_metadata=extra_meta
    )
    assert receipt["status"] == "CONFIRMED"

    # Create an altered/modified version of the same image (brightness/contrast tweak)
    img = cv2.imread(sample_image)
    altered_img = cv2.convertScaleAbs(img, alpha=1.05, beta=10)
    altered_path = str(tmp_path / "altered_face.jpg")
    cv2.imwrite(altered_path, altered_img)

    altered_face = face_engine.process_face_scan(altered_path, output_crop_dir=str(tmp_path))
    sim = FaceEngine.compute_similarity(orig_face.perceptual_hash, altered_face.perceptual_hash)
    assert sim >= 0.80

    # Searching with altered image MUST detect the Genesis origin and flag alteration/tampering
    alt_match = search_engine.execute_search(image_path=altered_path, face_result=altered_face)
    assert alt_match.record_type == "ALTERED_DERIVATIVE"
    assert alt_match.is_tampered is True
    assert alt_match.genesis_reference_hash == receipt["evidence_hash"]
    assert "modified" in alt_match.tamper_details.lower()
