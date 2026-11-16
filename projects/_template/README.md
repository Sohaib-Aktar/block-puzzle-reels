# How to Add a New Project to this Studio

This content studio is designed to support any mobile game, SaaS product, ERP system, software tutorial, or brand without modifying the video engine.

## Step 1: Copy this template folder
Copy `projects/_template/` to `projects/<your-project-slug>/`:
```bash
# Example for an ERP software product
cp -r projects/_template projects/apex-erp

# Example for a new casual puzzle game
cp -r projects/_template projects/carom-clash
```

## Step 2: Fill out `PROJECT_PROFILE.md`
Edit `projects/<your-project-slug>/PROJECT_PROFILE.md`:
- Set your product name, category, developer/company, and website or download link.
- Define your brand voice, color palette, and target audience.
- Note where your raw assets are stored (e.g. `Raw_input_files/<your-project-slug>/`).

## Step 3: Create your campaign
Rename `campaigns/_template_campaign/` to your campaign name (e.g. `launch-campaign`, `features-walkthrough`):
- Edit `campaign_brief.md` with your campaign objectives and KPIs.
- Use `content_calendar.md` to map out your publishing schedule.
- Use `briefs/brief.template.md` to draft briefs for each reel or video.

## Step 4: Choose your rendering path
- **FFmpeg path (Ordinary edits, screen capture cuts, voiceovers):**
  Use `renderers/ffmpeg/trim_and_scale.bat` or Python scripts in `scripts/`.
- **Remotion path (Animated UI cards, motion graphics, badges, teasers):**
  Register a new composition in `my-video/src/Root.tsx` using the design tokens in `my-video/src/theme/tokens.ts`.

## Step 5: Deliver outputs
Outputs will automatically be organized into:
```
outputs/<project-slug>/<campaign-id>/<content-id>/
├── brief.md
├── captions/
│   ├── instagram.txt
│   ├── facebook.txt
│   └── youtube.txt
├── final/
│   └── instagram_reel.mp4
└── qc_report.md
```
Never overwrite an approved final file. Use `_v2`, `_v3` for revisions.
