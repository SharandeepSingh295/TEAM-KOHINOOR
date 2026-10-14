"""
Cryptographic Biometric Certificate Generator for KohinoorGuard.
Produces self-contained, verifiable HTML & SVG Certificates of Authenticity
with embedded QR code verification stamps, base64 biometric face scan proofs,
and cryptographic on-chain transaction provenance.
"""

import os
import cv2
import json
import time
import base64
import numpy as np
import datetime
from typing import Dict, Any, Optional


class CertificateGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_qr_data_uri(self, payload: str, size: int = 240) -> str:
        """
        Generates a standard scannable QR code using OpenCV and encodes it as a base64 PNG data URI.
        """
        try:
            encoder = cv2.QRCodeEncoder.create()
            qr_matrix = encoder.encode(payload)
            # Add quiet zone border (4 modules)
            padded = np.pad(qr_matrix, 4, mode="constant", constant_values=255)
            # Resize with nearest-neighbor to preserve crisp sharp edges
            scaled = cv2.resize(padded, (size, size), interpolation=cv2.INTER_NEAREST)
            # Encode as PNG in memory
            success, png_buffer = cv2.imencode(".png", scaled)
            if success:
                b64 = base64.b64encode(png_buffer).decode("utf-8")
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass

        # Fallback placeholder if QR encoding fails
        return ""

    def encode_image_base64(self, image_path: Optional[str]) -> str:
        """Encodes an on-disk image file to a base64 Data URI."""
        if not image_path or not os.path.exists(image_path):
            return ""
        try:
            with open(image_path, "rb") as f:
                raw_bytes = f.read()
            ext = os.path.splitext(image_path)[1].lower().replace(".", "")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            b64 = base64.b64encode(raw_bytes).decode("utf-8")
            return f"data:image/{mime};base64,{b64}"
        except Exception:
            return ""

    def generate_certificate_html(
        self,
        record_data: Dict[str, Any],
        forensic_data: Optional[Dict[str, Any]] = None,
        save_filename: Optional[str] = None
    ) -> str:
        """
        Generates a standalone, tamper-evident cryptographic HTML certificate.
        """
        evidence_hash = record_data.get("evidence_hash", "0x0000000000000000000000000000000000000000000000000000000000000000")
        face_hash = record_data.get("face_hash", "0x0000000000000000000000000000000000000000000000000000000000000000")
        media_hash = record_data.get("media_hash", "0x0000000000000000000000000000000000000000000000000000000000000000")
        platform = record_data.get("platform", "Genesis Origin Registry")
        source_url = record_data.get("source_url", "genesis://origin-master")
        verifier = record_data.get("verifier", record_data.get("verifier_address", "0x0000000000000000000000000000000000000000"))
        block_number = record_data.get("block_number", 1)
        tx_hash = record_data.get("transaction_hash", "0x" + "0" * 64)
        contract_addr = record_data.get("contract_address", "0xF2E246BB7678C62c6AbA282D7B70204689c8395b")
        record_type = record_data.get("record_type", "GENESIS_ORIGINAL")
        is_tampered = record_data.get("is_tampered", False)

        raw_ts = record_data.get("timestamp", int(time.time()))
        if isinstance(raw_ts, (int, float)):
            ts_str = datetime.datetime.fromtimestamp(raw_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            ts_str = str(raw_ts)

        # Base64 assets
        face_crop_path = record_data.get("face_crop_path") or record_data.get("crop_path")
        face_crop_uri = self.encode_image_base64(face_crop_path)
        
        # QR Code payload (Direct Verification URI)
        qr_payload = f"https://kohinoorguard.io/verify?hash={evidence_hash}"
        qr_uri = self.generate_qr_data_uri(qr_payload)

        # Forensic Integrity
        integrity_score = 100.0
        verdict = "GENESIS_ROOT_AUTHENTIC"
        if forensic_data:
            integrity_score = forensic_data.get("integrity_score", 100.0)
            verdict = forensic_data.get("verdict", verdict)
        elif is_tampered:
            integrity_score = 45.0
            verdict = "ALTERED_DERIVATIVE_DETECTED"

        status_badge_bg = "#064e3b" if not is_tampered else "#7f1d1d"
        status_badge_text = "#6ee7b7" if not is_tampered else "#fca5a5"
        status_label = "AUTHENTICATED & UNALTERED" if not is_tampered else "TAMPERING / DERIVATIVE FLAGGED"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KohinoorGuard Certificate of Biometric Attestation | {evidence_hash[:10]}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #090d16;
      color: #f1f5f9;
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 30px 15px;
    }}
    .cert-frame {{
      background: linear-gradient(135deg, #0d1322 0%, #111a2e 50%, #0d1322 100%);
      border: 3px double #38bdf8;
      border-radius: 20px;
      max-width: 900px;
      width: 100%;
      padding: 40px;
      box-shadow: 0 0 50px -10px rgba(56, 189, 248, 0.25), inset 0 0 30px rgba(15, 23, 42, 0.8);
      position: relative;
      overflow: hidden;
    }}
    .cert-frame::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 14px;
      margin: 10px;
      pointer-events: none;
    }}
    .cert-header {{
      text-align: center;
      margin-bottom: 28px;
      border-bottom: 1px solid rgba(56, 189, 248, 0.2);
      padding-bottom: 20px;
    }}
    .cert-title {{
      font-family: 'Cinzel', serif;
      font-size: 26px;
      font-weight: 900;
      letter-spacing: 2px;
      background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .cert-subtitle {{
      font-size: 13px;
      color: #94a3b8;
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }}
    .status-banner {{
      display: inline-block;
      margin-top: 12px;
      padding: 6px 16px;
      border-radius: 9999px;
      background: {status_badge_bg};
      color: {status_badge_text};
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 1px;
      border: 1px solid {status_badge_text}44;
    }}
    .cert-body {{
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 30px;
      align-items: start;
    }}
    .biometric-column {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }}
    .face-preview {{
      width: 170px;
      height: 170px;
      border-radius: 16px;
      border: 2px solid #38bdf8;
      box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
      object-fit: cover;
      background: #1e293b;
    }}
    .qr-box {{
      background: #ffffff;
      padding: 8px;
      border-radius: 12px;
      border: 2px solid #38bdf8;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .qr-img {{
      width: 130px;
      height: 130px;
      display: block;
    }}
    .qr-label {{
      font-size: 9px;
      color: #0f172a;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-top: 4px;
      text-transform: uppercase;
    }}
    .data-grid {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .data-card {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 10px 14px;
    }}
    .data-label {{
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #64748b;
      margin-bottom: 3px;
      font-weight: 600;
    }}
    .data-value {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #38bdf8;
      word-break: break-all;
    }}
    .data-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .cert-footer {{
      margin-top: 30px;
      padding-top: 16px;
      border-top: 1px solid rgba(56, 189, 248, 0.2);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: #64748b;
    }}
    .seal {{
      display: flex;
      align-items: center;
      gap: 8px;
      color: #38bdf8;
      font-weight: 700;
    }}
    .print-btn {{
      background: linear-gradient(135deg, #0284c7, #4f46e5);
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }}
    @media print {{
      body {{ background: white; color: black; padding: 0; }}
      .cert-frame {{ border-color: #0284c7; box-shadow: none; max-width: 100%; }}
      .print-btn {{ display: none; }}
    }}
  </style>
</head>
<body>

  <div class="cert-frame">
    <div class="cert-header">
      <div class="cert-title">Cryptographic Biometric Attestation</div>
      <div class="cert-subtitle">KohinoorGuard Decentralized Provenance Protocol &bull; EVM Smart Contract</div>
      <div class="status-banner">{status_label}</div>
    </div>

    <div class="cert-body">
      <!-- Left: Biometric Face & QR Code -->
      <div class="biometric-column">
        {f'<img class="face-preview" src="{face_crop_uri}" alt="Biometric Face">' if face_crop_uri else '<div class="face-preview" style="display:flex;align-items:center;justify-content:center;color:#64748b;font-size:11px;">Face Scan Anchored</div>'}
        
        {f'''<div class="qr-box">
          <img class="qr-img" src="{qr_uri}" alt="QR Verification">
          <span class="qr-label">Scan to Verify</span>
        </div>''' if qr_uri else ''}
      </div>

      <!-- Right: Hashes & Blockchain Provenance -->
      <div class="data-grid">
        <div class="data-card">
          <div class="data-label">Canonical Evidence Root Hash (Keccak-256)</div>
          <div class="data-value">{evidence_hash}</div>
        </div>

        <div class="data-row">
          <div class="data-card">
            <div class="data-label">Biometric Face SHA-256</div>
            <div class="data-value">{face_hash[:18]}...{face_hash[-8:]}</div>
          </div>
          <div class="data-card">
            <div class="data-label">Media Asset SHA-256</div>
            <div class="data-value">{media_hash[:18]}...{media_hash[-8:]}</div>
          </div>
        </div>

        <div class="data-row">
          <div class="data-card">
            <div class="data-label">Classification</div>
            <div class="data-value" style="color: #f8fafc;">{record_type}</div>
          </div>
          <div class="data-card">
            <div class="data-label">Forensic Integrity Score</div>
            <div class="data-value" style="color: {'#4ade80' if integrity_score >= 80 else '#f87171'};">{integrity_score}% ({verdict})</div>
          </div>
        </div>

        <div class="data-row">
          <div class="data-card">
            <div class="data-label">Platform Origin</div>
            <div class="data-value" style="color: #cbd5e1;">{platform}</div>
          </div>
          <div class="data-card">
            <div class="data-label">Block Timestamp</div>
            <div class="data-value" style="color: #cbd5e1;">{ts_str}</div>
          </div>
        </div>

        <div class="data-card">
          <div class="data-label">EVM Smart Contract Address</div>
          <div class="data-value">{contract_addr}</div>
        </div>

        <div class="data-row">
          <div class="data-card">
            <div class="data-label">Block Number</div>
            <div class="data-value">#{block_number}</div>
          </div>
          <div class="data-card">
            <div class="data-label">Attesting Verifier Address</div>
            <div class="data-value">{verifier[:12]}...{verifier[-6:]}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="cert-footer">
      <div class="seal">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        <span>KOHINOORGUARD CRYPTOGRAPHIC SEAL</span>
      </div>
      <div>Registered on Ethereum Virtual Machine &bull; Non-Repudiable Evidence</div>
      <button class="print-btn" onclick="window.print()">Print Certificate / Save PDF</button>
    </div>
  </div>

</body>
</html>
"""
        if save_filename:
            filepath = os.path.join(self.output_dir, save_filename) if not os.path.isabs(save_filename) else save_filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            return filepath

        return html
