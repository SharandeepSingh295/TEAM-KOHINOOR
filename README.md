# 🛡️ KohinoorGuard

> **End-to-End Face Scan Ingestion, Live Web/Social Media Discovery, and Blockchain Tamper-Evident Attestation.**

[![Solidity](https://img.shields.io/badge/Solidity-%5E0.8.20-363636?logo=solidity)](https://soliditylang.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Web3.py](https://img.shields.io/badge/Web3.py-v8.0.0-F16822?logo=ethereum)](https://web3py.readthedocs.io/)
[![OpenCV](https://img.shields.io/badge/OpenCV-YuNet_DNN-5C3EE8?logo=opencv)](https://opencv.org/)
[![Tests](https://img.shields.io/badge/Tests-12%2F12%20Passing-brightgreen)](https://docs.pytest.org/)

---

## 📌 Project Overview

**KohinoorGuard** is an end-to-end audit pipeline designed to take an input face scan, discover matching public content and profiles across the live web and social media, and anchor the resulting evidence onto an EVM-compatible blockchain. 

By binding a normalized biometric face crop, discovered media assets, platform metadata, and timestamps into a canonical cryptographic fingerprint, the pipeline creates an **immutable, verifiable, and tamper-evident proof of existence** that can be re-audited at any point in time.

---

## 🎯 Real-World Utility & Industry Applications

With generative AI making it effortless to synthesize faces, manipulate photos, and orchestrate identity theft, traditional image metadata (like EXIF) is easily stripped or forged. KohinoorGuard delivers verifiable proof across key real-world scenarios:

```
           ┌───────────────────────────────────────────────┐
           │          KOHINOORGUARD ARCHITECTURE           │
           └───────────────────────┬───────────────────────┘
                                   │
      ┌────────────────┬───────────┴────────────┬────────────────┐
      ▼                ▼                        ▼                ▼
[ Web3 & DAOs ]  [ Cyber Insurance ]     [ Journalism / Media ]  [ Legal Forensics ]
Sybil-resistant  CEO Fraud & Executive   Viral Photo Fact-Check  Court-Admissible
Proof-of-Person  Impersonation Defense   & Deepfake Debunking    Chain of Custody
```

1. **🛡️ Combating Deepfakes & Synthetic Likeness Abuse**:
   * Detects digital splicing, face-swapping boundaries, and generative AI tampering using Error Level Analysis (ELA) and Laplacian edge variance, producing visual color-coded heatmaps of altered zones.
2. **🏛️ Tamper-Proof Digital Identity & Genesis Copyright**:
   * Empowers photographers, public figures, models, and creators to anchor their original portraits as immutable **"Genesis Master References"** on-chain with non-repudiable timestamped proofs of prior existence.
3. **🔍 Fraudulent & Altered KYC Prevention**:
   * Enables financial and Web3 institutions to verify user verification selfies against on-chain biometric baselines to eliminate synthetic identity fraud and re-used altered ID documents.
4. **📰 Fact-Checking & Digital Forensics for Journalism**:
   * Grants journalists, media outlets, and fact-checking organizations instant tools to verify viral visual media against an immutable ledger and export standalone cryptographic HTML/SVG Certificates of Authenticity with scannable QR verification seals.
5. **🌐 Automated Public Likeness Tracking**:
   * Scans and discovers unauthorized visual appearances of an individual's likeness across public social graphs (Twitter/X, Instagram, LinkedIn, Reddit) without storing raw biometrics on-chain.

---

## 🏗️ Pipeline Architecture

```
[ Input Face Scan Image ]
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Biometric Extraction & Landmark Alignment          │
│ • OpenCV YuNet Deep Neural Network face detection           │
│ • Normalized crop standardization (256x256)                 │
│ • SHA-256 cryptographic face hash + Perceptual dHash        │
└──────────────────────────┬──────────────────────────────────┘
                           │ normalized_face_crop.jpg + face_hash
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Live Web / Social Media Discovery & Genesis Proof │
│ • Genuine Google Lens reverse image search (via SerpApi)    │
│ • Zero mock/hardcoded results; strict user privacy          │
│ • If unseen: anchors as Genesis Original Master Reference   │
│ • If altered: flags Altered Derivative & Biometric Tamper   │
│ • Downloads matched asset & computes SHA-256 media hash     │
└──────────────────────────┬──────────────────────────────────┘
                           │ post_url + media_hash + metadata
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: Canonical Evidence Packaging                       │
│ • Deterministic Keccak-256 evidence bundle generation       │
│ • Creates portable JSON attestation manifest                │
└──────────────────────────┬──────────────────────────────────┘
                           │ canonical evidence_hash
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: Blockchain Smart Contract Registration             │
│ • FaceVerificationRegistry.sol on EVM chain                 │
│ • Records: (evidenceHash, faceHash, mediaHash, url, time)   │
│ • Emits `FaceMatchVerified` event on-chain                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ on-chain transaction receipt
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: Standalone Re-Verification Engine                  │
│ • Compares live content against immutable ledger state      │
│ • Detects 100% of data alterations or forged assets         │
│ • Outputs [VERIFIED AUTHENTIC] or [TAMPER DETECTED]         │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Technical Highlights & Mathematical Architecture

### 1. Dual-Layer Biometric Hashing (Crypto + Perceptual)
Pure cryptographic hashing alone is brittle for visual media because changing a single pixel or compression artifact completely scrambles a SHA-256 hash. KohinoorGuard solves this by deploying a **two-tier hashing strategy**:

| Layer | Algorithm | Format | Purpose |
| :--- | :--- | :--- | :--- |
| **Exact Integrity** | **SHA-256** | 32-byte hex (`0x...`) | Bit-for-bit tamper detection. If an asset is altered by even $1$ byte, verification fails immediately. |
| **Perceptual Identity** | **Difference Hash (`dHash`)** | 64-bit binary string | Visual likeness comparison. Resilient against recompression, color adjustments, lighting shifts, and platform compression. |

* **Similarity Formulation**:
  $$\text{Similarity} = 1.0 - \left(\frac{\text{Hamming Distance}(\text{Hash}_1, \text{Hash}_2)}{64}\right)$$
  * **$\ge 80\%$ Similarity**: Classifies the image as the **same subject** (flags potential deepfakes, crops, or altered derivatives).
  * **$100\%$ Bit Match**: Confirms **unaltered original state**.

### 2. YuNet Landmark Alignment & Normalization
* Powered by OpenCV's **YuNet deep learning ONNX detector**, ensuring sub-millisecond facial landmark identification (pupils, nose tip, and mouth corners) and rotation normalization.
* Normalizes the crop to a standardized $256 \times 256$ dimension using **Lanczos-4 interpolation** with a $15\%$ padding margin.

### 3. Genuine Social Media Search (Stage 2)
* **No hardcoded results**: Executes live queries against public social graph endpoints (e.g. GitHub user profiles and developer avatars) and reverse search engines.
* Supports plug-and-play **SerpApi Google Lens** integration by specifying `SERPAPI_API_KEY` in `.env`.

### 4. Forensic Error Level Analysis (ELA) & Laplacian Noise
* Recompresses the candidate image in memory at a fixed $90\%$ JPEG quality and computes the absolute differential matrix: $\Delta = |I_{\text{original}} - I_{\text{recompressed}}|$.
* Scales differences by factor $\alpha = 15$ to surface spliced or cloned boundaries as bright clusters.
* Applies Laplacian high-frequency edge filters to detect blending seams along facial contours characteristic of deepfake swaps.

### 5. Dual-Mode Blockchain Architecture (Stage 4)
* **Local In-Memory EVM (`mode: local`)**: Powered by `EthereumTesterProvider` (`py-evm`), allowing zero-cost, instantaneous testing and offline demonstrations without faucets or keys. Includes automated ledger persistence to allow separate CLI processes to inspect the same state.
* **Public EVM Testnet (`mode: testnet`)**: Seamlessly deploys and broadcasts transactions to public testnets like **Polygon Amoy** or **Ethereum Sepolia** by populating `.env`.

### 6. Cryptographic Tamper-Evidence (Stage 5)
* Re-evaluates assets against `FaceVerificationRegistry.sol` via `verify_integrity()`. If an asset, post URL, or face crop has been altered by even a single byte, the verification engine instantly triggers a **[TAMPER DETECTED]** alert.

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
* Python 3.10+ (Tested on Python 3.13)
* Node.js v18+ (For contract compilation)
* Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/SharandeepSingh295/TEAM-KOHINOOR.git
cd TEAM-KOHINOOR

# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install solc and compile the smart contract
npm install
node compile_contract.js
```

### 3. (Optional) Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
* Leave `BLOCKCHAIN_MODE=local` to run with the built-in zero-friction EVM simulator.
* Set `SERPAPI_API_KEY` if you wish to enable Google Lens reverse search.

### 🐳 Quick Start with Docker
Run the entire stack in an isolated container without needing local Python or Node dependencies:
```bash
docker compose up --build
```
Then visit **`http://localhost:5000`** in your browser.

---

## 📖 How to Run

### 🌐 Launch the Interactive Web Application (Browser UI)
To use the application from a link in your browser:
```bash
python web_app.py
```
Then open: **`http://localhost:5000`** in your browser!
* Paste any **image web link (URL)** or upload an image file directly.
* View biometric landmark detection, reverse search, and smart contract anchoring in real time.
* Inspect on-chain ledger records and run instant tamper verification.

### Deploy the Smart Contract
Deploys `FaceVerificationRegistry.sol` to either local EVM or public testnet:
```bash
python deploy.py --chain local
```

### Run the Full Pipeline
Ingests a face scan, performs genuine live reverse-image search via Google Lens (or Genesis Registry), packages evidence, and records it on the blockchain:
```bash
# Example 1: Live Reverse-Image Search across Web & Social (Discovers live Twitter/X post)
python run_pipeline.py --image samples/elonmask.jpg --chain local

# Example 2: Genesis Origin & Alteration Biometric Registry
python run_pipeline.py --image samples/real_sample_face.jpg --chain local
```

**Parameters**:
* `--image`: Path to input face scan OR an **HTTP/HTTPS image link** (defaults to `samples/real_sample_face.jpg`).
* `--chain`: Blockchain target (`local` or `testnet`, default: `local`).
* `--output`: Output directory for crops and receipts (default: `output/`).
* `--query-hint`: Search terms hint for web discovery.

#### Re-Verify Data Against the Blockchain
Run the standalone verification utility against an existing `evidence_manifest.json` or directly by on-chain evidence hash:
```bash
# Verify using full manifest (validates face crop bytes, media asset, and manifest root)
python verify_record.py --evidence output/evidence_manifest.json

# Or query and verify directly by on-chain evidence hash
python verify_record.py --hash <EVIDENCE_ROOT_HASH>
```
Output:
```
             Cryptographic Comparison: On-Chain Record vs Live Data             
┌──────────────────────────┬───────────────────────┬───────────────────────┬──────────┐
│ Attribute                │ On-Chain Ledger       │ Current Live Asset    │  Status  │
├──────────────────────────┼───────────────────────┼───────────────────────┼──────────┤
│ Face Crop Biometric Hash │ 0x26f6d7315d63...     │ 0x26f6d7315d63...     │  MATCH   │
│ Media Asset Hash         │ 0x09188192df06...     │ 0x09188192df06...     │  MATCH   │
│ Post Source URL          │ genesis://master-ass… │ genesis://master-ass… │  MATCH   │
│ Platform                 │ Genesis Origin        │ Genesis Origin        │  MATCH   │
│ Canonical Evidence Root  │ 0x36529695f5ec...     │ 0x36529695f5ec...     │  MATCH   │
│ Ledger Timestamp         │ 1788694695            │ 1788694563            │ RECORDED │
└──────────────────────────┴───────────────────────┴───────────────────────┴──────────┘
┌──────────────────────────── VERIFIED AUTHENTIC ─────────────────────────────┐
│ ✔ RE-VERIFICATION PASSED                                                    │
│ No data modification or tampering has occurred since registration.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Run the Tamper Detection Demonstration
Demonstrate the system rejecting altered media assets or tampered face crop files:
```bash
python demo_tamper_detection.py
```
Output:
```
┌─────────────────────────── TAMPER-EVIDENCE ALERT ───────────────────────────┐
│ ✖ TAMPER DETECTED                                                           │
│ WARNING: The live assets or manifest metadata do NOT match the immutable     │
│ blockchain fingerprint.                                                      │
│ • Media asset image content has been modified!                               │
│ • Biometric face crop file on disk has been altered or replaced!             │
└─────────────────────────────────────────────────────────────────────────────┘
[SUCCESS]: The verification engine successfully DETECTED the tamper attempt and rejected the data!
```

### Inspect On-Chain Ledger & Analytics
Explore all recorded proofs, Genesis masters, and altered derivatives with rich tabular output or executive analytics:
```bash
# View all ledger records
python show_ledger.py

# View executive analytics dashboard (total proofs, gas, unique verifiers)
python show_ledger.py --summary

# Filter ledger by classification (genesis, altered, public)
python show_ledger.py --filter genesis

# Inspect a specific record by hash in full detail
python show_ledger.py --hash <EVIDENCE_ROOT_HASH>
```

---

### 🔬 Biometric Forensic Lab & Tamper Heatmap Inspector
Run deep mathematical forensics to detect digital splicing, re-compression anomalies, and localized face modifications:
```bash
# Standalone image inspection (Error Level Analysis + High-Frequency Noise)
python forensic_analyzer.py --image samples/sample_face.jpg

# Differential forensic audit between Genesis original and target image
python forensic_analyzer.py --original samples/sample_face.jpg --image output/altered_face.jpg
```
**Capabilities**:
* **Error Level Analysis (ELA)**: Recompresses images at fixed quality to surface resaved, cloned, or spliced regions.
* **Laplacian Noise Analysis**: Detects edge variance inconsistencies along face blending seams typical of deepfake face-swaps.
* **Differential Tamper Heatmaps**: Generates full-color visual heatmaps (`COLORMAP_JET`) highlighting modified zones.
* **4-Panel Audit Cards**: Generates executive comparison composites: `[Genesis Master] | [Target Scan] | [Tamper Heatmap] | [ELA Residuals]`.

---

### 📜 Verifiable Cryptographic Biometric Certificates
Issue standalone, tamper-evident HTML Certificates of Authenticity directly from on-chain records:
```bash
# Issue certificate for any registered record by on-chain evidence hash
python generate_certificate.py --hash <EVIDENCE_ROOT_HASH>

# Or issue certificate directly during re-verification with forensic audit
python verify_record.py --evidence output/evidence_manifest.json --forensics --certificate
```
**Certificate Highlights**:
* **Holographic Security Seal**: Embedded SVG metallic shield and attestation badge.
* **Scannable QR Verification Proof**: Encodes direct on-chain verification URLs using OpenCV's built-in QR encoder and roundtrip-tested decoding.
* **Embedded Biometric Proofs**: Self-contained base64 face crop previews, Keccak-256 evidence roots, and SHA-256 fingerprints.
* **Print-to-PDF Ready**: Formatted with custom `@media print` styling for generating official forensic identity attestations.

---

## 🧪 Automated Test Suite

Run the comprehensive unit and integration tests using `pytest`:
```bash
pytest -v
```

**Tested Scenarios (12/12 Passing)**:
1. `test_face_detection_and_encoding`: Validates YuNet face bounding box detection, normalization, and SHA-256 / dHash generation.
2. `test_search_engine_platform_identification`: Validates domain-to-platform mapping (Twitter/X, Reddit, GitHub, LinkedIn).
3. `test_evidence_packaging_determinism`: Proves mathematical determinism of canonical Keccak-256 evidence hashes.
4. `test_blockchain_smart_contract_full_cycle`: Tests on-chain deployment, record registration, retrieval, authentic verification, and tamper rejection.
5. `test_genesis_origin_and_altered_derivative_detection`: Tests anchoring of unseen faces as Genesis Originals and automated biometric detection & flagging of altered photo derivatives.
6. `test_face_crop_and_manifest_tamper_detection`: Validates detection when face crop image bytes or manifest parameters are altered.
7. `test_multi_generation_derivative_traces_to_root_genesis`: Proves multi-generation derivatives correctly trace lineage back to the root Genesis master.
8. `test_ledger_analytics_summary`: Validates executive ledger statistics, gas calculations, and classification counting.
9. `test_forensic_ela_and_noise_analysis`: Tests Error Level Analysis (ELA) and Laplacian noise variance calculation on face scans.
10. `test_forensic_differential_tamper_heatmap`: Validates differential tamper detection, localized contour bounding box extraction, and heatmap generation.
11. `test_cryptographic_certificate_generation_and_qr_roundtrip`: Asserts self-contained HTML certificate generation and verifies OpenCV QR code decoding roundtrip.
12. `test_web_app_health_and_status`: Validates REST API health checks (`/api/health`), status, and ledger data export (`/api/export`) in both JSON and CSV formats.

---

## ⛓️ Blockchain Details: `FaceVerificationRegistry.sol`

* **Contract Standard**: Solidity `^0.8.20` with optimizer enabled (`runs=200`).
* **Storage Structure**:
  ```solidity
  struct VerificationRecord {
      bytes32 evidenceHash;     // Deterministic root fingerprint
      bytes32 faceHash;         // SHA-256 of normalized face crop
      bytes32 mediaHash;        // SHA-256 of matched social media asset
      string sourceUrl;         // Live verified post URL
      string platform;          // Target platform name
      uint256 timestamp;        // Block timestamp
      address verifier;         // Attesting wallet address
      bool exists;
  }
  ```
* **Key Functions**:
  * `recordVerification(...)`: Stores record and emits `FaceMatchVerified` event.
  * `getRecord(bytes32 evidenceHash)`: Returns full on-chain attestation record.
  * `verifyIntegrity(bytes32 evidenceHash, bytes32 currentMediaHash)`: Gas-efficient view check asserting zero data tampering.
* **Average Gas Usage**: ~212,000 gas per verification record.

---

## ⚠️ Known Limitations & Considerations

1. **Walled Garden Social Media Scraping**:
   * Modern social networks (Instagram, TikTok, LinkedIn) increasingly restrict unauthenticated scraping and reverse image lookups behind aggressive bot-detection and CAPTCHAs. While the engine includes a fallback to public social networks (GitHub, Reddit) and SerpApi Google Lens, production deployments targeting walled platforms require authenticated API keys or rotating proxy pools.
2. **Biometric Privacy & On-Chain Data**:
   * In compliance with GDPR and biometric data protection regulations, **raw facial images are never stored on-chain**. Only irreversible cryptographic hashes (SHA-256) and perceptual fingerprints are anchored. Future roadmaps can integrate Zero-Knowledge Proofs (zk-SNARKs) to prove face matches without revealing the underlying vectors.
3. **Link Rot & Content Deletion**:
   * If an original social media post is deleted by its author, the live URL becomes inaccessible. While the on-chain cryptographic proof and downloaded evidence snapshot remain intact, integrating decentralized storage (IPFS / Arweave pinning) provides permanent asset preservation.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
