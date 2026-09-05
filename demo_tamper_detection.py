"""
Demonstration script showing tamper detection in action.
Creates a copy of the evidence manifest with altered media content,
runs verify_record, and demonstrates the blockchain catching the tamper attempt.
"""

import json
import shutil
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_tamper_demo():
    print("=================================================================")
    print("STEP 1: Creating tampered copy of manifest (modifying image data)")
    print("=================================================================")
    
    with open("output/evidence_manifest.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Simulate an attacker tampering with the media file
    tampered_media_path = "output/tampered_image_fake.jpg"
    with open(tampered_media_path, "wb") as f:
        f.write(b"MALICIOUS_TAMPERED_IMAGE_CONTENT_DEEPFAKE")

    data["social_media_data"]["local_media_path"] = tampered_media_path
    data["social_media_data"]["post_url"] = "https://fake-impersonator-url.com/profile"

    with open("output/tampered_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Tampered manifest created at: output/tampered_manifest.json\n")
    print("=================================================================")
    print("STEP 2: Running verify_record.py against the tampered asset")
    print("=================================================================")

    result = subprocess.run(
        [sys.executable, "verify_record.py", "--evidence", "output/tampered_manifest.json"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print("\n[SUCCESS]: The blockchain smart contract successfully DETECTED the tamper attempt and rejected the data!")

if __name__ == "__main__":
    run_tamper_demo()
