import os
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
    manifest_path = "output/evidence_manifest.json"
    if not os.path.exists(manifest_path):
        print("=================================================================")
        print("STEP 0: Bootstrapping baseline verification on sample face image")
        print("=================================================================")
        from run_pipeline import run_pipeline
        run_pipeline(
            image_path="samples/real_sample_face.jpg",
            chain_mode="local",
            output_dir="output"
        )
        print("\n[INFO] Baseline verification established and anchored on-chain.\n")

    print("=================================================================")
    print("DEMO TEST 1: Tampering with Matched Social Media Image Asset")
    print("=================================================================")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
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
    print("Running verify_record.py against the tampered media asset...")

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
        print("[SUCCESS]: The blockchain smart contract successfully DETECTED media asset tampering!\n")

    print("=================================================================")
    print("DEMO TEST 2: Tampering with Biometric Face Crop File on Disk")
    print("=================================================================")
    with open(manifest_path, "r", encoding="utf-8") as f:
        face_data = json.load(f)

    tampered_crop_path = "output/tampered_crop_fake.jpg"
    with open(tampered_crop_path, "wb") as f:
        f.write(b"ALTERED_BIOMETRIC_FACE_CROP_PIXELS")

    face_data["face_data"]["crop_path"] = tampered_crop_path
    with open("output/tampered_face_manifest.json", "w", encoding="utf-8") as f:
        json.dump(face_data, f, indent=2)

    print("Tampered face crop manifest created at: output/tampered_face_manifest.json\n")
    print("Running verify_record.py against the tampered face crop...")

    result_face = subprocess.run(
        [sys.executable, "verify_record.py", "--evidence", "output/tampered_face_manifest.json"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(result_face.stdout)
    if result_face.stderr:
        print(result_face.stderr)

    if result_face.returncode != 0:
        print("[SUCCESS]: The verification engine successfully DETECTED biometric face crop tampering!\n")


if __name__ == "__main__":
    run_tamper_demo()
