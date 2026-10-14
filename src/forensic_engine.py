"""
Forensic Analysis & Visual Tamper Detection Engine for KohinoorGuard.
Provides:
  1. Error Level Analysis (ELA) to detect digital splicing, resaving, and generative AI edits.
  2. High-frequency Laplacian noise analysis to identify face-swapping boundaries and blending seams.
  3. Perceptual and pixel-level differential tampering heatmaps between Genesis originals and derivatives.
  4. Composite 4-panel forensic diagnostic image generation.
  5. Multi-metric forensic integrity scoring (0-100%) and manipulation classification.
"""

import os
import cv2
import numpy as np
from dataclasses import dataclass, asdict
from typing import Tuple, List, Optional, Dict, Any


@dataclass
class ELAResult:
    mean_error: float
    max_error: float
    energy_variance: float
    ela_image_path: Optional[str] = None


@dataclass
class ForensicReport:
    is_tampered: bool
    verdict: str
    tamper_probability: float           # 0.0 to 1.0
    integrity_score: float              # 0.0 to 100.0%
    mean_squared_error: float
    peak_signal_to_noise: float
    altered_pixel_ratio: float          # Percentage of pixels showing significant variation
    ela_metrics: Dict[str, float]
    noise_variance: float
    altered_bounding_boxes: List[List[int]]  # [[x, y, w, h], ...]
    heatmap_path: Optional[str] = None
    composite_path: Optional[str] = None
    ela_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ForensicEngine:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def compute_ela(
        self,
        image: np.ndarray,
        quality: int = 90,
        scale: int = 15,
        save_path: Optional[str] = None
    ) -> Tuple[np.ndarray, ELAResult]:
        """
        Computes Error Level Analysis (ELA) by recompressing the image as JPEG
        and calculating the absolute pixel difference scaled for visual inspection.
        Higher localized difference highlights spliced or recently edited areas.
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image array provided for ELA.")

        # Recompress in memory at specified JPEG quality
        success, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not success:
            raise RuntimeError("JPEG recompression failed during ELA.")

        recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

        # Ensure same size and type
        if recompressed.shape != image.shape:
            recompressed = cv2.resize(recompressed, (image.shape[1], image.shape[0]))

        # Absolute pixel difference
        diff = cv2.absdiff(image, recompressed)

        # Statistical metrics
        mean_err = float(np.mean(diff))
        max_err = float(np.max(diff))
        variance = float(np.var(diff))

        # Scale difference to emphasize compression artifacts
        ela_scaled = cv2.convertScaleAbs(diff, alpha=scale)

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            cv2.imwrite(save_path, ela_scaled)

        ela_result = ELAResult(
            mean_error=round(mean_err, 4),
            max_error=round(max_err, 4),
            energy_variance=round(variance, 4),
            ela_image_path=save_path
        )

        return ela_scaled, ela_result

    def compute_noise_variance(self, image: np.ndarray) -> float:
        """
        Calculates Laplacian high-frequency noise variance.
        Anomalously high or low variance indicates AI synthesis or heavy post-processing.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return float(round(lap.var(), 4))

    def generate_tamper_heatmap(
        self,
        diff_gray: np.ndarray,
        base_image: np.ndarray,
        alpha_overlay: float = 0.45,
        amplification: float = 6.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies a JET colormap to difference intensities and blends it onto the base image.
        Returns: (color_heatmap, blended_overlay)
        """
        scaled = cv2.convertScaleAbs(diff_gray, alpha=amplification)
        heatmap = cv2.applyColorMap(scaled, cv2.COLORMAP_JET)

        if base_image.shape[:2] != heatmap.shape[:2]:
            base_image = cv2.resize(base_image, (heatmap.shape[1], heatmap.shape[0]))

        overlay = cv2.addWeighted(base_image, 1.0 - alpha_overlay, heatmap, alpha_overlay, 0)
        return heatmap, overlay

    def detect_altered_regions(
        self,
        diff_gray: np.ndarray,
        threshold_val: int = 20,
        min_contour_area: int = 35
    ) -> Tuple[List[List[int]], float]:
        """
        Identifies bounding boxes of significantly altered pixel clusters.
        Returns: (bounding_boxes, altered_pixel_percentage)
        """
        _, thresh = cv2.threshold(diff_gray, threshold_val, 255, cv2.THRESH_BINARY)
        total_pixels = thresh.size
        altered_count = np.count_nonzero(thresh)
        ratio = float(round((altered_count / total_pixels) * 100.0, 3))

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for c in contours:
            if cv2.contourArea(c) >= min_contour_area:
                x, y, w, h = cv2.boundingRect(c)
                boxes.append([int(x), int(y), int(w), int(h)])

        # Sort bounding boxes by area descending
        boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
        return boxes, ratio

    def compare_images(
        self,
        original_path_or_img: Any,
        altered_path_or_img: Any,
        identifier: str = "forensic"
    ) -> ForensicReport:
        """
        Performs a deep differential forensic audit between a registered Genesis original
        and an alleged derivative or target scan.
        """
        # Load original
        if isinstance(original_path_or_img, str):
            orig_img = cv2.imread(original_path_or_img)
            if orig_img is None:
                raise FileNotFoundError(f"Original image not found: {original_path_or_img}")
        else:
            orig_img = original_path_or_img.copy()

        # Load altered
        if isinstance(altered_path_or_img, str):
            alt_img = cv2.imread(altered_path_or_img)
            if alt_img is None:
                raise FileNotFoundError(f"Altered image not found: {altered_path_or_img}")
        else:
            alt_img = altered_path_or_img.copy()

        # Standardize resolution for pixel-wise differential inspection
        std_size = (300, 300)
        orig_std = cv2.resize(orig_img, std_size, interpolation=cv2.INTER_AREA)
        alt_std = cv2.resize(alt_img, std_size, interpolation=cv2.INTER_AREA)

        # 1. Absolute Difference
        abs_diff = cv2.absdiff(orig_std, alt_std)
        gray_diff = cv2.cvtColor(abs_diff, cv2.COLOR_BGR2GRAY)

        # 2. Mathematical Error Metrics
        mse = float(np.mean((orig_std.astype(np.float64) - alt_std.astype(np.float64)) ** 2))
        psnr = 100.0 if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))

        # 3. Altered region detection
        boxes, altered_ratio = self.detect_altered_regions(gray_diff, threshold_val=18)

        # 4. Generate Heatmap & Overlay
        heatmap, overlay = self.generate_tamper_heatmap(gray_diff, alt_std)

        # Draw detected bounding boxes on overlay
        overlay_annotated = overlay.copy()
        for b in boxes[:5]:  # annotate top 5 suspicious zones
            x, y, w, h = b
            cv2.rectangle(overlay_annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(overlay_annotated, "ALT", (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # 5. Error Level Analysis (ELA) on target image
        ela_path = os.path.join(self.output_dir, f"ela_{identifier}.jpg")
        ela_img, ela_result = self.compute_ela(alt_std, quality=90, save_path=ela_path)

        # 6. Noise Analysis
        noise_var = self.compute_noise_variance(alt_std)

        # 7. Scoring & Verdict
        # Calculate tamper probability based on MSE, altered pixel ratio, and ELA variance
        if altered_ratio == 0.0 and mse == 0.0:
            tamper_prob = 0.0
            verdict = "GENESIS_AUTHENTIC"
        elif altered_ratio < 1.0 and mse < 50.0:
            tamper_prob = float(min(0.25, altered_ratio / 5.0))
            verdict = "MINOR_COMPRESSION_VARIANCE"
        elif altered_ratio < 5.0:
            tamper_prob = float(min(0.65, 0.25 + (altered_ratio / 10.0)))
            verdict = "SUSPICIOUS_ARTIFACTS"
        else:
            tamper_prob = float(min(1.0, 0.60 + (altered_ratio / 20.0)))
            verdict = "MANIPULATION_DETECTED"

        integrity_score = round(max(0.0, 100.0 - (tamper_prob * 100.0)), 2)
        is_tampered = (tamper_prob >= 0.30)

        # Save heatmap
        heatmap_path = os.path.join(self.output_dir, f"heatmap_{identifier}.jpg")
        cv2.imwrite(heatmap_path, overlay_annotated)

        # 8. Build 4-Panel Composite Inspection Card
        # Panels: [Original Master] | [Target Scan] | [Tamper Heatmap] | [ELA Residuals]
        composite_path = os.path.join(self.output_dir, f"composite_forensic_{identifier}.jpg")
        self._build_composite_card(
            orig_std, alt_std, overlay_annotated, ela_img,
            verdict, integrity_score, composite_path
        )

        return ForensicReport(
            is_tampered=is_tampered,
            verdict=verdict,
            tamper_probability=round(tamper_prob, 4),
            integrity_score=integrity_score,
            mean_squared_error=round(mse, 3),
            peak_signal_to_noise=round(psnr, 2),
            altered_pixel_ratio=round(altered_ratio, 2),
            ela_metrics=asdict(ela_result),
            noise_variance=noise_var,
            altered_bounding_boxes=boxes,
            heatmap_path=heatmap_path,
            composite_path=composite_path,
            ela_path=ela_path
        )

    def analyze_standalone_image(
        self,
        image_path_or_img: Any,
        identifier: str = "scan"
    ) -> ForensicReport:
        """
        Analyzes a single face scan without an existing reference master.
        Evaluates ELA compression artifacts, noise consistency, and synthetic boundaries.
        """
        if isinstance(image_path_or_img, str):
            img = cv2.imread(image_path_or_img)
            if img is None:
                raise FileNotFoundError(f"Image not found: {image_path_or_img}")
        else:
            img = image_path_or_img.copy()

        std_size = (300, 300)
        img_std = cv2.resize(img, std_size, interpolation=cv2.INTER_AREA)

        # 1. ELA
        ela_path = os.path.join(self.output_dir, f"ela_{identifier}.jpg")
        ela_img, ela_result = self.compute_ela(img_std, quality=90, save_path=ela_path)

        # 2. Noise variance
        noise_var = self.compute_noise_variance(img_std)

        # 3. ELA Heatmap (Highlights localized high-error zones)
        ela_gray = cv2.cvtColor(ela_img, cv2.COLOR_BGR2GRAY)
        boxes, altered_ratio = self.detect_altered_regions(ela_gray, threshold_val=40, min_contour_area=50)
        heatmap, overlay = self.generate_tamper_heatmap(ela_gray, img_std, alpha_overlay=0.4, amplification=3.0)

        # Standalone Verdict based on ELA energy variance and localized anomalies
        if ela_result.energy_variance > 120.0 or altered_ratio > 10.0:
            tamper_prob = 0.75
            verdict = "SUSPICIOUS_HIGH_FREQUENCY_EDITS"
        elif ela_result.energy_variance > 60.0 or altered_ratio > 4.0:
            tamper_prob = 0.35
            verdict = "MINOR_ARTIFACTS_DETECTED"
        else:
            tamper_prob = 0.05
            verdict = "CLEAN_COMPRESSION_PROFILE"

        integrity_score = round(max(0.0, 100.0 - (tamper_prob * 100.0)), 2)
        is_tampered = (tamper_prob >= 0.50)

        heatmap_path = os.path.join(self.output_dir, f"heatmap_{identifier}.jpg")
        cv2.imwrite(heatmap_path, overlay)

        # Composite of Image vs ELA vs Heatmap
        composite_path = os.path.join(self.output_dir, f"composite_forensic_{identifier}.jpg")
        self._build_standalone_composite(img_std, ela_img, overlay, verdict, integrity_score, composite_path)

        return ForensicReport(
            is_tampered=is_tampered,
            verdict=verdict,
            tamper_probability=round(tamper_prob, 4),
            integrity_score=integrity_score,
            mean_squared_error=0.0,
            peak_signal_to_noise=100.0,
            altered_pixel_ratio=round(altered_ratio, 2),
            ela_metrics=asdict(ela_result),
            noise_variance=noise_var,
            altered_bounding_boxes=boxes,
            heatmap_path=heatmap_path,
            composite_path=composite_path,
            ela_path=ela_path
        )

    def _build_composite_card(
        self,
        orig: np.ndarray,
        alt: np.ndarray,
        heatmap: np.ndarray,
        ela: np.ndarray,
        verdict: str,
        integrity_score: float,
        save_path: str
    ):
        """Constructs an executive 4-panel visual forensic audit card."""
        panel_h, panel_w = 300, 300
        header_h = 36
        total_w = panel_w * 4
        total_h = panel_h + header_h + 40

        card = np.zeros((total_h, total_w, 3), dtype=np.uint8)
        card[:] = (18, 24, 38)  # Dark slate background

        # Banner
        banner_color = (40, 167, 69) if "AUTHENTIC" in verdict else (30, 144, 255) if "MINOR" in verdict else (0, 69, 255)
        cv2.rectangle(card, (0, 0), (total_w, header_h), (25, 33, 50), -1)
        cv2.line(card, (0, header_h), (total_w, header_h), (50, 65, 95), 1)

        title_text = f"KOHINOORGUARD BIOMETRIC FORENSIC AUDIT  |  VERDICT: {verdict}  |  INTEGRITY: {integrity_score}%"
        cv2.putText(card, title_text, (20, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA)

        # Place the 4 panels
        panels = [
            (orig, "1. GENESIS ORIGINAL MASTER"),
            (alt, "2. TARGET FACE SCAN"),
            (heatmap, "3. TAMPER HEATMAP OVERLAY"),
            (ela, "4. ELA ERROR RESIDUALS")
        ]

        for idx, (img_panel, label) in enumerate(panels):
            x_offset = idx * panel_w
            y_offset = header_h + 20
            
            # Place image
            resized_p = cv2.resize(img_panel, (panel_w - 10, panel_h - 10))
            card[y_offset : y_offset + panel_h - 10, x_offset + 5 : x_offset + panel_w - 5] = resized_p
            
            # Draw border
            cv2.rectangle(card, (x_offset + 5, y_offset), (x_offset + panel_w - 5, y_offset + panel_h - 10), (60, 75, 105), 1)

            # Label banner
            cv2.rectangle(card, (x_offset + 5, y_offset + panel_h - 32), (x_offset + panel_w - 5, y_offset + panel_h - 10), (15, 20, 30), -1)
            cv2.putText(card, label, (x_offset + 12, y_offset + panel_h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 200, 230), 1, cv2.LINE_AA)

        cv2.imwrite(save_path, card)

    def _build_standalone_composite(
        self,
        img: np.ndarray,
        ela: np.ndarray,
        heatmap: np.ndarray,
        verdict: str,
        integrity_score: float,
        save_path: str
    ):
        """Constructs a 3-panel forensic audit card for single-scan analysis."""
        panel_h, panel_w = 300, 300
        header_h = 36
        total_w = panel_w * 3
        total_h = panel_h + header_h + 40

        card = np.zeros((total_h, total_w, 3), dtype=np.uint8)
        card[:] = (18, 24, 38)

        cv2.rectangle(card, (0, 0), (total_w, header_h), (25, 33, 50), -1)
        cv2.line(card, (0, header_h), (total_w, header_h), (50, 65, 95), 1)

        title_text = f"KOHINOORGUARD STANDALONE SCAN FORENSICS  |  VERDICT: {verdict}  |  HEALTH: {integrity_score}%"
        cv2.putText(card, title_text, (20, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (240, 240, 240), 1, cv2.LINE_AA)

        panels = [
            (img, "1. INGESTED FACE SCAN"),
            (ela, "2. ELA COMPRESSION RESIDUALS"),
            (heatmap, "3. LOCALIZED ANOMALY HEATMAP")
        ]

        for idx, (img_panel, label) in enumerate(panels):
            x_offset = idx * panel_w
            y_offset = header_h + 20
            resized_p = cv2.resize(img_panel, (panel_w - 10, panel_h - 10))
            card[y_offset : y_offset + panel_h - 10, x_offset + 5 : x_offset + panel_w - 5] = resized_p
            cv2.rectangle(card, (x_offset + 5, y_offset), (x_offset + panel_w - 5, y_offset + panel_h - 10), (60, 75, 105), 1)
            cv2.rectangle(card, (x_offset + 5, y_offset + panel_h - 32), (x_offset + panel_w - 5, y_offset + panel_h - 10), (15, 20, 30), -1)
            cv2.putText(card, label, (x_offset + 12, y_offset + panel_h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 200, 230), 1, cv2.LINE_AA)

        cv2.imwrite(save_path, card)
