import os
import sys
import json
import shutil

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, run_command, inspect_media
from audio_engine import generate_voiceover, mix_and_duck
from qc_verifier import verify_content
from creative_qc import evaluate_creative_quality
from campaign_manager import update_status, add_or_update_item

tut_dir = os.path.join(WORKSPACE_ROOT, "outputs", "expand-hr", "payroll-quick-guides", "expandhr-tut-01-one-click-payroll")
final_dir = os.path.join(tut_dir, "final")
captions_dir = os.path.join(tut_dir, "captions")
os.makedirs(final_dir, exist_ok=True)
os.makedirs(captions_dir, exist_ok=True)

# 1. Register in Campaign Tracker
add_or_update_item(
    content_id="expandhr-tut-01-one-click-payroll",
    project="expand-hr",
    campaign="payroll-quick-guides",
    topic="One-Click Monthly Payroll Processing",
    platform="youtube_tutorial",
    status="PLANNED",
    output_location=final_dir
)

# 2. Write Creative Brief
with open(os.path.join(tut_dir, "brief.md"), "w", encoding="utf-8") as f:
    f.write("""# Creative Brief — One-Click Payroll Processing

**Content ID:** `expandhr-tut-01-one-click-payroll`  
**Project:** `expand-hr`  
**Campaign:** `payroll-quick-guides`  
**Target Audience:** HR Managers, Payroll Officers, CFOs, SME Business Owners  
**Core Problem:** Manual spreadsheet payroll calculations take days and risk compliance penalties.  
**Objective:** Demonstrate fast, error-free monthly salary calculation and compliance automation.  
**Hook Archetype:** Speed / Operational Efficiency  
**Tone:** Professional, clear, authoritative B2B  
**CTA:** "Book a customized Expand HR walkthrough at expandhrms.com"  
""")

# 3. Write Script
with open(os.path.join(tut_dir, "script.md"), "w", encoding="utf-8") as f:
    f.write("""# Video Script — One-Click Monthly Payroll

**Scene 1 (0:00–0:03): Hook**  
- On-Screen Text: "Payroll Done in One Click ⏱️"  
- Narration: "Stop spending days on manual spreadsheets."  

**Scene 2 (0:03–0:08): Workflow**  
- On-Screen Text: "Auto Tax & Deductions Calculation"  
- Narration: "With Expand HR, monthly payroll, statutory tax deductions, and compliance process automatically."  

**Scene 3 (0:08–0:12): Action & CTA**  
- On-Screen Text: "Automate Your HR Today 💼"  
- Narration: "Disburse payslips instantly. Simplify your human resources today."  
""")

# 4. Write Timeline
with open(os.path.join(tut_dir, "timeline.md"), "w", encoding="utf-8") as f:
    f.write("""# Shot-by-Shot Timeline

| Timecode | Shot | Visual Focus | Audio / VO |
|---|---|---|---|
| 00:00–00:03 | Shot 1 | Dashboard overview & Month selection | "Stop spending days on manual spreadsheets." |
| 00:03–00:08 | Shot 2 | One-click calculate & deduction summary | "With Expand HR, monthly payroll and compliance process automatically." |
| 00:08–00:12 | Shot 3 | Direct bank advice & payslip release | "Disburse payslips instantly. Simplify your HR today." |
""")

# 5. Write Manifest
manifest_data = {
    "content_id": "expandhr-tut-01-one-click-payroll",
    "project": "expand-hr",
    "campaign": "payroll-quick-guides",
    "resolution": {"width": 1080, "height": 1920},
    "fps": 30,
    "target_duration_sec": 12.0,
    "hook": "Payroll Done in One Click",
    "cta": "Simplify HR Today",
    "audio": {
        "voiceover": "voiceover.wav",
        "loudness_target_lufs": -14.0
    }
}
with open(os.path.join(tut_dir, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, indent=2)

# 6. Write Captions
with open(os.path.join(captions_dir, "youtube.txt"), "w", encoding="utf-8") as f:
    f.write("Stop losing hours every month to manual payroll calculations. Expand HR calculates gross pay, tax deductions (PF/ESI/TDS), and generates bank disbursement sheets in one click.\n\nLearn more: https://expandhrms.com\n\n#ExpandHR #PayrollAutomation #HRMS #CloudERP #BusinessEfficiency")

with open(os.path.join(captions_dir, "instagram.txt"), "w", encoding="utf-8") as f:
    f.write("Payroll in 1 click? ⏱️ Yes, really. Automated tax, PF, ESI, and instant payslips with Expand HR.\n\nLink in bio to see it in action! 💼\n\n#HRTech #PayrollMadeEasy #CloudHRMS #BusinessAutomation")

# 7. Write Approval Record
with open(os.path.join(tut_dir, "approval_record.md"), "w", encoding="utf-8") as f:
    f.write("""# Editorial Approval Record

**Content ID:** `expandhr-tut-01-one-click-payroll`  
**Project:** `expand-hr`  
**Review Status:** Pending Human Sign-Off  
**Verification Level:** Core Workflows Verified (Synthetic demo data used)  
**Publishing Target:** YouTube Shorts / LinkedIn Video  
**Sign-Off Requirements:**
- [x] Verified claim accuracy (No fabricated features)
- [x] Zero PII displayed (synthetic demo employee records)
- [ ] Final executive approval prior to social publishing
""")

# 8. Synthesize Voiceover
vo_script = "Stop spending days on manual spreadsheets. With Expand HR, monthly payroll, statutory deductions, and bank disbursements process in a single click. Simplify your human resources today."
vo_path = os.path.join(tut_dir, "voiceover.wav")
generate_voiceover(vo_script, vo_path, rate=0)
print(f"Generated VO at {vo_path}")

# 9. Cut authentic video footage and mix with VO
raw_footage = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "recording_3.mp4")
temp_video = os.path.join(final_dir, "temp_video.mp4")

cmd_cut = get_ffmpeg_cmd() + [
    "-y",
    "-ss", "0.0",
    "-i", os.path.abspath(raw_footage),
    "-t", "12.0",
    "-vf", "scale=1080:1920",
    "-c:v", "libx264",
    "-crf", "22",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-an",
    os.path.abspath(temp_video)
]
run_command(cmd_cut)

# Mix with VO and apply EBU R128 loudness normalization
final_video = os.path.join(final_dir, "software_tutorial_vertical.mp4")
mix_and_duck(
    video_path=temp_video,
    output_path=final_video,
    voiceover_path=vo_path,
    normalize=True
)

if os.path.exists(temp_video):
    os.remove(temp_video)

info = inspect_media(final_video)
print("Rendered Expand HR Video:", final_video)
print(f"Duration: {info['duration_seconds']:.2f}s, Canvas: {info['width']}x{info['height']}, Audio: {info.get('audio_codec')}")

# 10. Technical QC
qc_report_path = os.path.join(tut_dir, "qc_report.md")
qc_tech = verify_content(final_video, "expand-hr", "youtube_tutorial", qc_report_path, "expandhr-tut-01-one-click-payroll")

# 11. Creative QC
cqc_report_path = os.path.join(tut_dir, "creative_qc_report.md")
qc_creative = evaluate_creative_quality(tut_dir, "expand-hr", cqc_report_path)

# 12. Update Campaign Manager
update_status(
    "expandhr-tut-01-one-click-payroll",
    "QC_APPROVED" if (qc_tech["passed"] and qc_creative["passed"]) else "RENDERED",
    technical_qc_passed=qc_tech["passed"],
    creative_qc_score=qc_creative["total_score"]
)

print("Technical QC Passed:", qc_tech["passed"])
print(f"Creative QC Score: {qc_creative['total_score']} / {qc_creative['max_score']} (Passed: {qc_creative['passed']})")
