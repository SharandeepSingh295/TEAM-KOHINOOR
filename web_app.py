#!/usr/bin/env python3
"""
VeriFace-Chain Interactive Web Application.
Provides a web user interface accessible from your browser link (http://localhost:5000).
Supports:
  - Inputting Face Images via Direct Web URL / Link or File Upload
  - Live Biometric Extraction, Reverse Web/Social Discovery & Evidence Packaging
  - On-Chain Smart Contract Registration & Cryptographic Tamper Checking
  - Interactive Ledger Explorer
"""

import os
import sys
import json
import uuid
import time
import requests
from pathlib import Path
from aiohttp import web
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.face_engine import FaceEngine
from src.search_engine import WebSocialSearchEngine
from src.evidence_packager import EvidencePackager
from src.blockchain_client import BlockchainClient, LOCAL_LEDGER_FILE

OUTPUT_DIR = os.path.abspath("output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VeriFace-Chain | Decentralized Biometric Verification</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0b0f19; color: #e2e8f0; font-family: system-ui, -apple-system, sans-serif; }
    .glass { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glass-card { background: rgba(31, 41, 55, 0.6); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.06); }
    .glow { box-shadow: 0 0 25px -5px rgba(59, 130, 246, 0.4); }
    .glow-green { box-shadow: 0 0 25px -5px rgba(16, 185, 129, 0.4); }
    .glow-red { box-shadow: 0 0 25px -5px rgba(239, 68, 68, 0.4); }
  </style>
</head>
<body class="min-h-screen flex flex-col justify-between">
  <!-- Top Navbar -->
  <header class="border-b border-gray-800 bg-gray-950/80 sticky top-0 z-50 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg">
          <i class="fa-solid fa-shield-halved text-lg"></i>
        </div>
        <div>
          <h1 class="font-extrabold text-xl tracking-tight text-white flex items-center gap-2">
            VeriFace<span class="text-blue-500">Chain</span>
            <span class="text-xs font-mono uppercase bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/30">EVM DApp</span>
          </h1>
          <p class="text-xs text-gray-400">Decentralized Face Ingestion & Immutable Ledger Attestation</p>
        </div>
      </div>
      <div class="flex items-center space-x-4 text-xs font-mono">
        <div class="hidden sm:flex items-center space-x-2 bg-gray-900 border border-gray-800 px-3 py-1.5 rounded-lg">
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span class="text-gray-400">Contract:</span>
          <span id="nav-contract" class="text-gray-200">0xF2E2...395b</span>
        </div>
        <a href="https://github.com/SharandeepSingh295/TEAM-KOHINOOR" target="_blank" class="bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded-lg flex items-center gap-2 transition">
          <i class="fa-brands fa-github"></i>
          <span>GitHub</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-grow w-full">
    <!-- Hero Banner -->
    <div class="mb-8 rounded-2xl p-6 sm:p-8 bg-gradient-to-r from-blue-900/30 via-indigo-950/20 to-gray-900 border border-blue-500/20">
      <div class="max-w-3xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-3">
          <i class="fa-solid fa-cube"></i> Live Smart Contract Connected
        </div>
        <h2 class="text-2xl sm:text-3xl font-bold text-white mb-2">Cryptographic Biometric Attestation & Reverse Discovery</h2>
        <p class="text-gray-400 text-sm leading-relaxed">
          Provide an image via <strong>Web Link (URL)</strong> or upload a local file. The pipeline extracts biometric feature vectors, performs live web and social media reverse lookup, generates a tamper-evident evidence bundle, and anchors the proof onto an immutable smart contract.
        </p>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex border-b border-gray-800 mb-8 space-x-6 text-sm font-semibold">
      <button onclick="switchTab('pipeline')" id="tab-btn-pipeline" class="py-3 px-1 border-b-2 border-blue-500 text-blue-400 flex items-center gap-2">
        <i class="fa-solid fa-fingerprint"></i> 1. Run Ingestion & Blockchain Attestation
      </button>
      <button onclick="switchTab('verify')" id="tab-btn-verify" class="py-3 px-1 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2">
        <i class="fa-solid fa-magnifying-glass-chart"></i> 2. Verify Record / Tamper Check
      </button>
      <button onclick="switchTab('ledger')" id="tab-btn-ledger" class="py-3 px-1 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2">
        <i class="fa-solid fa-list-check"></i> 3. On-Chain Ledger Records (<span id="ledger-count">0</span>)
      </button>
    </div>

    <!-- TAB 1: RUN PIPELINE -->
    <div id="tab-pipeline" class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Input Form (Left 5 Cols) -->
      <div class="lg:col-span-5 space-y-6">
        <div class="glass p-6 rounded-2xl space-y-5">
          <h3 class="font-bold text-lg text-white flex items-center gap-2">
            <i class="fa-solid fa-cloud-arrow-up text-blue-400"></i> Face Scan Input
          </h3>

          <!-- Method 1: Web Link (URL) -->
          <div>
            <label class="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              <i class="fa-solid fa-link text-blue-400 mr-1"></i> Option A: Image Web Link (URL)
            </label>
            <input type="url" id="image-url-input" placeholder="https://example.com/face_photo.jpg" 
                   class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            <p class="text-xs text-gray-500 mt-1">Paste any public direct link to an image (JPEG, PNG, WebP).</p>
          </div>

          <div class="relative flex py-1 items-center">
            <div class="flex-grow border-t border-gray-800"></div>
            <span class="flex-shrink mx-4 text-gray-500 text-xs font-mono uppercase">or</span>
            <div class="flex-grow border-t border-gray-800"></div>
          </div>

          <!-- Method 2: File Upload -->
          <div>
            <label class="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              <i class="fa-solid fa-upload text-blue-400 mr-1"></i> Option B: Upload Image File
            </label>
            <div class="border-2 border-dashed border-gray-700 hover:border-blue-500 rounded-xl p-4 text-center cursor-pointer transition bg-gray-900/50" onclick="document.getElementById('file-upload-input').click()">
              <input type="file" id="file-upload-input" accept="image/*" class="hidden" onchange="handleFileSelected(event)">
              <i class="fa-solid fa-image text-gray-500 text-2xl mb-1"></i>
              <p id="file-upload-text" class="text-xs text-gray-400">Click to choose image file or drop here</p>
            </div>
          </div>

          <!-- Sample Quick Button -->
          <div class="flex items-center justify-between pt-2">
            <span class="text-xs text-gray-400">Want to test instantly?</span>
            <button type="button" onclick="useSampleImage()" class="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 bg-blue-500/10 px-2.5 py-1 rounded-lg border border-blue-500/20">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Load Demo Sample
            </button>
          </div>

          <hr class="border-gray-800">

          <!-- Network Mode -->
          <div>
            <label class="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              <i class="fa-solid fa-network-wired text-blue-400 mr-1"></i> Blockchain Network
            </label>
            <select id="chain-mode-select" class="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
              <option value="local">Simulated Local EVM (Instant zero-gas test)</option>
              <option value="testnet">Polygon Amoy Testnet (Public chain via .env)</option>
            </select>
          </div>

          <!-- Submit Button -->
          <button id="btn-submit-pipeline" onclick="executePipeline()" class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm tracking-wide shadow-lg shadow-blue-500/20 transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-bolt"></i> Run Verification & Anchor On-Chain
          </button>
        </div>
      </div>

      <!-- Results Display (Right 7 Cols) -->
      <div class="lg:col-span-7 space-y-6">
        <!-- Initial Blank Slate -->
        <div id="pipeline-idle" class="glass p-8 rounded-2xl flex flex-col items-center justify-center text-center min-h-[380px]">
          <div class="w-16 h-16 rounded-full bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-500 mb-4">
            <i class="fa-solid fa-shield-virus text-2xl"></i>
          </div>
          <h4 class="font-bold text-white text-lg mb-1">Awaiting Face Scan Ingestion</h4>
          <p class="text-sm text-gray-400 max-w-sm">Provide an image link or file and trigger the pipeline to generate biometric hashes and anchor proofs to the smart contract.</p>
        </div>

        <!-- Running Spinner -->
        <div id="pipeline-loading" class="hidden glass p-12 rounded-2xl flex flex-col items-center justify-center text-center min-h-[380px]">
          <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <h4 class="font-bold text-white text-lg mb-2">Executing 5-Stage Verification Engine</h4>
          <p id="loading-stage-text" class="text-sm text-gray-400">Detecting landmarks, computing hashes, discovering web assets, and broadcasting smart contract transaction...</p>
        </div>

        <!-- Success Result Container -->
        <div id="pipeline-result" class="hidden space-y-6">
          <!-- Main Attestation Banner -->
          <div class="p-6 rounded-2xl bg-green-950/40 border border-green-500/30 glow-green">
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-lg">
                  <i class="fa-solid fa-check-double"></i>
                </div>
                <div>
                  <h4 class="font-bold text-green-400 text-lg">Verification Successful & Anchored On-Chain</h4>
                  <p class="text-xs text-green-300/80">Tamper-evidence verification passed with 0% deviation</p>
                </div>
              </div>
              <span class="text-xs font-mono bg-green-500/20 text-green-300 px-3 py-1 rounded-full font-bold">CONFIRMED</span>
            </div>

            <!-- Evidence Hash Box -->
            <div class="bg-gray-900/90 rounded-xl p-3 border border-gray-800 font-mono text-xs break-all">
              <div class="text-gray-400 text-[10px] uppercase font-sans mb-0.5">Canonical Evidence Root Hash:</div>
              <span id="res-evidence-hash" class="text-cyan-400 font-bold"></span>
            </div>
          </div>

          <!-- 4 Breakdown Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Stage 1 Card -->
            <div class="glass-card p-4 rounded-xl space-y-3">
              <h5 class="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-user-check"></i> Stage 1: Face Analysis
              </h5>
              <div class="flex items-center gap-3">
                <img id="res-face-crop-img" src="" alt="Face Crop" class="w-16 h-16 rounded-lg object-cover border border-gray-700 bg-gray-900">
                <div class="text-xs space-y-1">
                  <div>Confidence: <strong id="res-face-conf" class="text-white"></strong></div>
                  <div class="text-gray-400 text-[11px] font-mono break-all">Hash: <span id="res-face-hash" class="text-gray-300"></span></div>
                </div>
              </div>
            </div>

            <!-- Stage 2 Card -->
            <div class="glass-card p-4 rounded-xl space-y-3">
              <h5 class="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-globe"></i> Stage 2: Web / Social Match
              </h5>
              <div class="flex items-center gap-3">
                <img id="res-matched-asset-img" src="" alt="Matched Media" class="w-16 h-16 rounded-lg object-cover border border-gray-700 bg-gray-900">
                <div class="text-xs space-y-1 overflow-hidden">
                  <div>Platform: <strong id="res-platform" class="text-purple-300"></strong></div>
                  <div class="truncate text-gray-400">URL: <a id="res-source-url" href="#" target="_blank" class="text-blue-400 underline"></a></div>
                  <div class="text-gray-400 text-[11px] font-mono break-all">Media Hash: <span id="res-media-hash" class="text-gray-300"></span></div>
                </div>
              </div>
            </div>

            <!-- Stage 4 Card -->
            <div class="glass-card p-4 rounded-xl space-y-2 md:col-span-2">
              <h5 class="text-xs font-bold text-yellow-400 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-link"></i> Stage 4: On-Chain Smart Contract Receipt
              </h5>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div class="bg-gray-900/60 p-2.5 rounded-lg border border-gray-800">
                  <div class="text-gray-500 text-[10px]">Block Number</div>
                  <div id="res-block-no" class="font-mono font-bold text-white text-sm"></div>
                </div>
                <div class="bg-gray-900/60 p-2.5 rounded-lg border border-gray-800">
                  <div class="text-gray-500 text-[10px]">Gas Used</div>
                  <div id="res-gas-used" class="font-mono font-bold text-white text-sm"></div>
                </div>
                <div class="bg-gray-900/60 p-2.5 rounded-lg border border-gray-800 col-span-2">
                  <div class="text-gray-500 text-[10px]">Transaction Hash</div>
                  <div id="res-tx-hash" class="font-mono text-cyan-400 truncate text-xs"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: VERIFY TAMPER -->
    <div id="tab-verify" class="hidden max-w-3xl mx-auto space-y-6">
      <div class="glass p-6 sm:p-8 rounded-2xl space-y-5">
        <div>
          <h3 class="font-bold text-lg text-white mb-1 flex items-center gap-2">
            <i class="fa-solid fa-shield-halved text-blue-400"></i> Smart Contract Re-Verification & Tamper Checker
          </h3>
          <p class="text-xs text-gray-400">
            Query the deployed smart contract with an existing <code>evidenceHash</code> to verify whether the media asset or social post data has been modified.
          </p>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Evidence Hash (32-byte Hex)</label>
          <input type="text" id="verify-hash-input" placeholder="0x..." class="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 font-mono text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500">
        </div>

        <button onclick="executeVerify()" class="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm tracking-wide shadow-lg transition flex items-center justify-center gap-2">
          <i class="fa-solid fa-magnifying-glass"></i> Check On-Chain Integrity
        </button>
      </div>

      <!-- Verification Result Box -->
      <div id="verify-result-box" class="hidden glass p-6 rounded-2xl">
        <div id="verify-content"></div>
      </div>
    </div>

    <!-- TAB 3: LEDGER EXPLORER -->
    <div id="tab-ledger" class="hidden space-y-6">
      <div class="glass p-6 rounded-2xl">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="font-bold text-lg text-white">Anchored Records Ledger</h3>
            <p class="text-xs text-gray-400">All discoveries recorded and verifiable on the smart contract</p>
          </div>
          <button onclick="loadLedger()" class="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition">
            <i class="fa-solid fa-arrows-rotate"></i> Refresh
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-gray-300">
            <thead class="bg-gray-900/80 text-gray-400 uppercase font-mono text-[10px] border-b border-gray-800">
              <tr>
                <th class="py-3 px-4">Evidence Hash</th>
                <th class="py-3 px-4">Platform</th>
                <th class="py-3 px-4">Source URL</th>
                <th class="py-3 px-4">Block #</th>
                <th class="py-3 px-4">Timestamp</th>
                <th class="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body" class="divide-y divide-gray-800/60 font-mono">
              <tr>
                <td colspan="6" class="text-center py-8 text-gray-500 font-sans">Loading ledger records...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="border-t border-gray-800 py-6 text-center text-xs text-gray-500 bg-gray-950/60">
    <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>VeriFace-Chain &copy; 2026 &bull; TEAM KOHINOOR</p>
      <p class="font-mono text-gray-400">Contract Address: <span id="footer-contract" class="text-blue-400 font-bold">0xF2E246BB76DF876Cef8b38ae84130F4F55De395b</span></p>
    </div>
  </footer>

  <script>
    let selectedFile = null;

    function switchTab(tabId) {
      ['pipeline', 'verify', 'ledger'].forEach(t => {
        document.getElementById('tab-' + t).classList.add('hidden');
        document.getElementById('tab-btn-' + t).className = 'py-3 px-1 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2';
      });
      document.getElementById('tab-' + tabId).classList.remove('hidden');
      document.getElementById('tab-btn-' + tabId).className = 'py-3 px-1 border-b-2 border-blue-500 text-blue-400 flex items-center gap-2';
      if (tabId === 'ledger') loadLedger();
    }

    function useSampleImage() {
      document.getElementById('image-url-input').value = 'samples/real_sample_face.jpg';
      selectedFile = null;
      document.getElementById('file-upload-text').innerText = 'Using local demo sample';
    }

    function handleFileSelected(e) {
      if (e.target.files && e.target.files[0]) {
        selectedFile = e.target.files[0];
        document.getElementById('file-upload-text').innerText = 'Selected: ' + selectedFile.name;
        document.getElementById('image-url-input').value = '';
      }
    }

    async function executePipeline() {
      const urlInput = document.getElementById('image-url-input').value.trim();
      const chainMode = document.getElementById('chain-mode-select').value;

      if (!urlInput && !selectedFile) {
        alert('Please enter an image web link (URL) or select an image file to upload.');
        return;
      }

      document.getElementById('pipeline-idle').classList.add('hidden');
      document.getElementById('pipeline-result').classList.add('hidden');
      document.getElementById('pipeline-loading').classList.remove('hidden');

      const formData = new FormData();
      formData.append('chain', chainMode);
      if (selectedFile) {
        formData.append('file', selectedFile);
      } else {
        formData.append('image_url', urlInput);
      }

      try {
        const resp = await fetch('/api/run', {
          method: 'POST',
          body: formData
        });
        const data = await resp.json();

        document.getElementById('pipeline-loading').classList.add('hidden');

        if (!data.success) {
          alert('Pipeline error: ' + (data.error || 'Unknown failure'));
          document.getElementById('pipeline-idle').classList.remove('hidden');
          return;
        }

        // Render Results
        document.getElementById('res-evidence-hash').innerText = data.evidence_hash;
        document.getElementById('res-face-crop-img').src = data.face_crop_url;
        document.getElementById('res-face-conf').innerText = (data.face_confidence * 100).toFixed(1) + '%';
        document.getElementById('res-face-hash').innerText = data.face_hash.substring(0, 18) + '...';

        document.getElementById('res-matched-asset-img').src = data.matched_asset_url;
        document.getElementById('res-platform').innerText = data.platform;
        document.getElementById('res-source-url').innerText = data.source_url;
        document.getElementById('res-source-url').href = data.source_url;
        document.getElementById('res-media-hash').innerText = data.media_hash.substring(0, 18) + '...';

        document.getElementById('res-block-no').innerText = '#' + data.block_number;
        document.getElementById('res-gas-used').innerText = Number(data.gas_used).toLocaleString() + ' gas';
        document.getElementById('res-tx-hash').innerText = data.transaction_hash;

        document.getElementById('pipeline-result').classList.remove('hidden');
        loadStatus();
      } catch (err) {
        document.getElementById('pipeline-loading').classList.add('hidden');
        document.getElementById('pipeline-idle').classList.remove('hidden');
        alert('Network / Server Error: ' + err.message);
      }
    }

    async function executeVerify() {
      const hash = document.getElementById('verify-hash-input').value.trim();
      if (!hash) {
        alert('Please enter an evidence hash.');
        return;
      }
      try {
        const resp = await fetch('/api/verify?hash=' + encodeURIComponent(hash));
        const res = await resp.json();
        const box = document.getElementById('verify-result-box');
        const content = document.getElementById('verify-content');
        box.classList.remove('hidden');

        if (!res.found) {
          content.innerHTML = `
            <div class="p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-400">
              <h4 class="font-bold flex items-center gap-2"><i class="fa-solid fa-triangle-exclamation"></i> Record Not Found</h4>
              <p class="text-xs text-red-300/80 mt-1">Evidence hash <code>${hash}</code> is not recorded in the smart contract ledger.</p>
            </div>
          `;
          return;
        }

        content.innerHTML = `
          <div class="p-4 rounded-xl bg-green-950/40 border border-green-500/30 text-green-400 mb-4">
            <h4 class="font-bold flex items-center gap-2"><i class="fa-solid fa-circle-check"></i> On-Chain Record Verified</h4>
            <p class="text-xs text-green-300/80 mt-1">Confirmed authentic on network: ${res.record.network || 'Simulated Local EVM'}</p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
            <div class="bg-gray-900 p-3 rounded-lg border border-gray-800">
              <div class="text-gray-500 text-[10px]">Platform</div>
              <div class="font-bold text-white">${res.record.platform}</div>
            </div>
            <div class="bg-gray-900 p-3 rounded-lg border border-gray-800">
              <div class="text-gray-500 text-[10px]">Block Number</div>
              <div class="font-bold text-white">#${res.record.block_number}</div>
            </div>
            <div class="bg-gray-900 p-3 rounded-lg border border-gray-800 sm:col-span-2">
              <div class="text-gray-500 text-[10px]">Source URL</div>
              <a href="${res.record.source_url}" target="_blank" class="text-blue-400 underline truncate block">${res.record.source_url}</a>
            </div>
          </div>
        `;
      } catch (err) {
        alert('Verification error: ' + err.message);
      }
    }

    async function loadLedger() {
      try {
        const resp = await fetch('/api/records');
        const list = await resp.json();
        document.getElementById('ledger-count').innerText = list.length;
        const tbody = document.getElementById('ledger-table-body');
        if (list.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-gray-500 font-sans">No records anchored yet.</td></tr>';
          return;
        }
        tbody.innerHTML = list.map(item => `
          <tr class="hover:bg-gray-900/50 transition">
            <td class="py-3 px-4 text-cyan-400 font-bold">${item.evidence_hash.substring(0, 14)}...</td>
            <td class="py-3 px-4 text-purple-300 font-sans font-semibold">${item.platform || 'Web'}</td>
            <td class="py-3 px-4 font-sans"><a href="${item.source_url}" target="_blank" class="text-blue-400 hover:underline max-w-[200px] truncate block">${item.source_url}</a></td>
            <td class="py-3 px-4">#${item.block_number}</td>
            <td class="py-3 px-4 text-gray-500">${new Date(item.timestamp * 1000).toLocaleTimeString()}</td>
            <td class="py-3 px-4 text-right font-sans">
              <button onclick="inspectRecord('${item.evidence_hash}')" class="text-blue-400 hover:text-blue-300 text-xs font-semibold bg-blue-500/10 px-2.5 py-1 rounded-lg border border-blue-500/20">
                Verify
              </button>
            </td>
          </tr>
        `).join('');
      } catch (e) {
        console.error(e);
      }
    }

    function inspectRecord(hash) {
      switchTab('verify');
      document.getElementById('verify-hash-input').value = hash;
      executeVerify();
    }

    async function loadStatus() {
      try {
        const resp = await fetch('/api/status');
        const st = await resp.json();
        if (st.contract_address) {
          document.getElementById('nav-contract').innerText = st.contract_address.substring(0, 6) + '...' + st.contract_address.substring(38);
          document.getElementById('footer-contract').innerText = st.contract_address;
        }
        if (st.records_count !== undefined) {
          document.getElementById('ledger-count').innerText = st.records_count;
        }
      } catch(e) {}
    }

    window.onload = () => {
      loadStatus();
      loadLedger();
    };
  </script>
</body>
</html>
"""


async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")


async def handle_status(request):
    contract_addr = "0xF2E246BB76DF876Cef8b38ae84130F4F55De395b"
    records_count = 0
    if os.path.exists(LOCAL_LEDGER_FILE):
        try:
            with open(LOCAL_LEDGER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                records_count = len(data)
        except Exception:
            pass
    return web.json_response({
        "contract_address": contract_addr,
        "records_count": records_count,
        "status": "ready"
    })


async def handle_records(request):
    records = []
    if os.path.exists(LOCAL_LEDGER_FILE):
        try:
            with open(LOCAL_LEDGER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = list(data.values())
        except Exception:
            pass
    return web.json_response(records)


async def handle_verify(request):
    ev_hash = request.query.get("hash", "").strip()
    if not ev_hash or not os.path.exists(LOCAL_LEDGER_FILE):
        return web.json_response({"found": False})

    with open(LOCAL_LEDGER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if ev_hash in data:
        return web.json_response({"found": True, "record": data[ev_hash]})
    return web.json_response({"found": False})


async def handle_run(request):
    reader = await request.multipart()
    image_path = None
    chain_mode = "local"

    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == "chain":
            chain_mode = (await part.text()).strip()
        elif part.name == "image_url":
            url = (await part.text()).strip()
            if url:
                if url.startswith(("http://", "https://")):
                    # Fetch image from web link
                    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    temp_name = f"url_upload_{uuid.uuid4().hex[:8]}.jpg"
                    image_path = os.path.join(OUTPUT_DIR, temp_name)
                    with open(image_path, "wb") as f:
                        f.write(resp.content)
                elif os.path.exists(url):
                    image_path = url
        elif part.name == "file":
            filename = part.filename or f"upload_{uuid.uuid4().hex[:8]}.jpg"
            image_path = os.path.join(OUTPUT_DIR, filename)
            with open(image_path, "wb") as f:
                while True:
                    chunk = await part.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)

    if not image_path or not os.path.exists(image_path):
        # Fallback to sample face
        sample_path = "samples/real_sample_face.jpg"
        if os.path.exists(sample_path):
            image_path = sample_path
        else:
            return web.json_response({"success": False, "error": "No valid image provided."})

    try:
        # Stage 1: Face Analysis
        face_engine = FaceEngine()
        face_result = face_engine.process_face_scan(image_path, output_crop_dir=OUTPUT_DIR)

        # Stage 2: Web / Social Match
        search_engine = WebSocialSearchEngine(output_dir=OUTPUT_DIR)
        social_match = search_engine.execute_search(image_path=face_result.crop_path)

        # Stage 3: Evidence Packaging
        packager = EvidencePackager(output_dir=OUTPUT_DIR)
        manifest = packager.create_package(face_result=face_result, social_match=social_match)

        # Stage 4: Blockchain Anchoring
        blockchain = BlockchainClient(mode=chain_mode)
        receipt = blockchain.record_verification(
            evidence_hash=manifest["evidence_hash"],
            face_hash=face_result.face_hash,
            media_hash=social_match.media_hash,
            source_url=social_match.url,
            platform=social_match.platform
        )

        # Update manifest
        manifest["blockchain_status"] = receipt
        packager.save_updated_manifest(manifest)

        return web.json_response({
            "success": True,
            "evidence_hash": manifest["evidence_hash"],
            "face_confidence": face_result.confidence,
            "face_hash": face_result.face_hash,
            "face_crop_url": f"/output/{os.path.basename(face_result.crop_path)}",
            "platform": social_match.platform,
            "source_url": social_match.url,
            "media_hash": social_match.media_hash,
            "matched_asset_url": f"/output/{os.path.basename(social_match.local_media_path)}",
            "block_number": receipt["block_number"],
            "gas_used": receipt["gas_used"],
            "transaction_hash": receipt["transaction_hash"],
            "contract_address": receipt["contract_address"]
        })
    except Exception as err:
        return web.json_response({"success": False, "error": str(err)})


def create_app():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/records", handle_records)
    app.router.add_get("/api/verify", handle_verify)
    app.router.add_post("/api/run", handle_run)
    app.router.add_static("/output", OUTPUT_DIR)
    app.router.add_static("/samples", os.path.abspath("samples"))
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print("\n=======================================================")
    print(" VeriFace-Chain Web DApp Live!")
    print(f" Web link: http://localhost:{port}")
    print("=======================================================\n")
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=port)
