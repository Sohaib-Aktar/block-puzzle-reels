import os
import sys

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, run_command, concat_clips, inspect_media
from qc_verifier import verify_content
from creative_qc import evaluate_creative_quality
from campaign_manager import update_status, add_or_update_item

out_dir = os.path.join(WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-offline-proof")
final_dir = os.path.join(out_dir, "final")
captions_dir = os.path.join(out_dir, "captions")
os.makedirs(final_dir, exist_ok=True)
os.makedirs(captions_dir, exist_ok=True)

# Register content in tracker
add_or_update_item(
    content_id="day-04-offline-proof",
    project="block-puzzle-burst",
    campaign="30-day-challenge",
    topic="Day 04: Offline & Airplane Mode Proof",
    platform="instagram_reel",
    status="PLANNED",
    output_location=final_dir
)

# 1. Generate 3.0s video from sample_airplane.jpg with matched silent audio
airplane_img = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "sample_airplane.jpg")
shot1_temp = os.path.join(final_dir, "shot1_airplane.mp4")

cmd_shot1 = get_ffmpeg_cmd() + [
    "-y",
    "-loop", "1",
    "-i", os.path.abspath(airplane_img),
    "-f", "lavfi",
    "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
    "-t", "3.0",
    "-vf", "scale=1080:1920",
    "-c:v", "libx264",
    "-crf", "22",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-c:a", "aac",
    "-b:a", "128k",
    os.path.abspath(shot1_temp)
]
run_command(cmd_shot1)

# 2. Trim 9.0s of authentic gameplay from recording_3.mp4
raw_gameplay = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "recording_3.mp4")
shot2_temp = os.path.join(final_dir, "shot2_gameplay.mp4")

cmd_shot2 = get_ffmpeg_cmd() + [
    "-y",
    "-ss", "5.0",
    "-i", os.path.abspath(raw_gameplay),
    "-t", "9.0",
    "-vf", "scale=1080:1920",
    "-c:v", "libx264",
    "-crf", "22",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-c:a", "aac",
    "-b:a", "128k",
    "-ac", "1",
    "-ar", "48000",
    os.path.abspath(shot2_temp)
]
run_command(cmd_shot2)

# 3. Concatenate shot 1 and shot 2 -> final 12s reel
final_output = os.path.join(final_dir, "instagram_reel.mp4")
concat_clips([shot1_temp, shot2_temp], final_output)

# Clean up temp shots
if os.path.exists(shot1_temp):
    os.remove(shot1_temp)
if os.path.exists(shot2_temp):
    os.remove(shot2_temp)

info = inspect_media(final_output)
print("Rendered Day 4 Reel:", final_output)
print(f"Duration: {info['duration_seconds']:.2f}s, Canvas: {info['width']}x{info['height']}, Size: {info['file_size_bytes'] / (1024 * 1024):.2f} MB")

# Write Captions
with open(os.path.join(captions_dir, "instagram.txt"), "w", encoding="utf-8") as f:
    f.write("Airplane mode on, game still on. ✈️ Perfect for flights, local trains, and zero-signal days. Free to play! 🧩\n\nLink in bio ⬇️\n\n#BlockPuzzle #OfflineGames #PyapirasGames #NoWifiGames")

# Copy brief from projects if present
proj_brief = os.path.join(WORKSPACE_ROOT, "projects", "block-puzzle-burst", "campaigns", "30-day-challenge", "briefs", "day-04.md")
if os.path.exists(proj_brief):
    import shutil
    shutil.copy2(proj_brief, os.path.join(out_dir, "brief.md"))

# Run Technical QC
qc_report_path = os.path.join(out_dir, "qc_report.md")
qc_tech = verify_content(final_output, "block-puzzle-burst", "instagram_reel", qc_report_path, "day-04-offline-proof")

# Run Creative QC
cqc_report_path = os.path.join(out_dir, "creative_qc_report.md")
qc_creative = evaluate_creative_quality(out_dir, "block-puzzle-burst", cqc_report_path)

# Update Campaign Manager
update_status(
    "day-04-offline-proof",
    "QC_APPROVED" if (qc_tech["passed"] and qc_creative["passed"]) else "RENDERED",
    technical_qc_passed=qc_tech["passed"],
    creative_qc_score=qc_creative["total_score"]
)

print("Technical QC Passed:", qc_tech["passed"])
print(f"Creative QC Score: {qc_creative['total_score']} / {qc_creative['max_score']} (Passed: {qc_creative['passed']})")
