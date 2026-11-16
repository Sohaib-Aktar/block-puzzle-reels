import os
import sys

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from audio_engine import generate_voiceover, mix_and_duck
from media_engine import inspect_media
from qc_verifier import verify_content
from creative_qc import evaluate_creative_quality
from campaign_manager import update_status, add_or_update_item

tut_dir = os.path.join(WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials", "ezisales-tut-01-order-booking")
final_dir = os.path.join(tut_dir, "final")
raw_vid = os.path.join(final_dir, "software_tutorial_vertical.mp4")

# Register in campaign tracker
add_or_update_item(
    content_id="ezisales-tut-01-order-booking",
    project="expand-ezisales",
    campaign="quick-start-tutorials",
    topic="Tutorial 01: Order Booking Workflow",
    platform="youtube_tutorial",
    status="PLANNED",
    output_location=final_dir
)

# 1. Synthesize offline voiceover narration
vo_script = "Step one. Select registered retailer. Step two. Enter order quantity and SKU items. Step three. Instant cloud synchronization with Expand ERP."
vo_path = os.path.join(tut_dir, "voiceover.wav")
generate_voiceover(vo_script, vo_path, rate=0)
print(f"Synthesized voiceover at: {vo_path}")

# 2. Mix voiceover into video with loudness normalization (-14 LUFS)
out_with_audio = os.path.join(final_dir, "software_tutorial_with_vo.mp4")
mix_and_duck(
    video_path=raw_vid,
    output_path=out_with_audio,
    voiceover_path=vo_path,
    normalize=True
)

# Overwrite main output with audio-enhanced version
os.replace(out_with_audio, raw_vid)
info = inspect_media(raw_vid)
print("Updated EziSales Video with VO:", raw_vid)
print(f"Duration: {info['duration_seconds']:.2f}s, Canvas: {info['width']}x{info['height']}, Audio: {info.get('audio_codec')}")

# 3. Technical QC
qc_report_path = os.path.join(tut_dir, "qc_report.md")
qc_tech = verify_content(raw_vid, "expand-ezisales", "youtube_tutorial", qc_report_path, "ezisales-tut-01-order-booking")

# 4. Creative QC
cqc_report_path = os.path.join(tut_dir, "creative_qc_report.md")
qc_creative = evaluate_creative_quality(tut_dir, "expand-ezisales", cqc_report_path)

# 5. Update status
update_status(
    "ezisales-tut-01-order-booking",
    "QC_APPROVED" if (qc_tech["passed"] and qc_creative["passed"]) else "RENDERED",
    technical_qc_passed=qc_tech["passed"],
    creative_qc_score=qc_creative["total_score"]
)

print("Technical QC Passed:", qc_tech["passed"])
print(f"Creative QC Score: {qc_creative['total_score']} / {qc_creative['max_score']} (Passed: {qc_creative['passed']})")
