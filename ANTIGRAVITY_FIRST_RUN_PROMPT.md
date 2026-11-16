# First-run prompt for Antigravity

Read and follow `MASTER_SOCIAL_VIDEO_STUDIO_PROMPT.md`, `MASTER_REEL_RULES.md`, `prompt.md`, and the existing `README.md` and architecture/plan documents before making changes.

I want this workspace to become a reusable **multi-project Social Video Studio**, managed with the mindset of a social media manager, marketing strategist, creative director, and technical video producer. It must support all my games, apps, ERP/software products, tutorials, product demonstrations, release announcements, and other projects—not only Block Puzzle Burst.

It must prepare and produce content for Instagram Reels, Facebook Reels/videos, YouTube Shorts, and standard horizontal YouTube videos/tutorials. Create platform-specific versions and publishing copy where required. Keep English as the default and only on-screen language unless I explicitly approve a project-specific exception. Captions/descriptions may be supplied separately in Bengali or Hindi when requested.

## Your first task: audit only

Do not code, delete, rename, move, or overwrite anything yet.

1. Inspect the complete existing workspace and report the real folder structure.
2. Read the existing prompt, rulebook, README, plans, package manifests, lockfiles, and Remotion configuration.
3. Explain the purpose of the root Node project versus `my-video` and identify which commands must run from which folder.
4. Confirm whether `my-video` is a working Remotion renderer and what it currently renders. Do not assume based only on its folder name.
5. Separate global studio rules from Block Puzzle Burst-specific rules and campaign documents.
6. Identify missing project profiles, project/campaign folders, raw asset organisation, platform export profiles, FFmpeg tooling, edit manifests, preview/final output separation, and QC checks.
7. Provide a proposed target structure and a safe, phased migration plan that preserves all existing files and working behaviour.
8. List anything you could not verify because the relevant file or asset was unavailable.

## Architecture direction

- Use a **project profile** for each game, app, software product, or brand. Store verified product facts, audience, brand identity, approved claims, CTA, language settings, source assets, and footage-integrity rules separately per project.
- Use **campaign briefs** for each campaign and individual video brief. Do not place all projects' facts or campaign plans in one generic rules file.
- Use **FFmpeg first** for normal footage editing: inspect, trim, concatenate, crop/reframe, scale, mix audio, add subtitles, apply appropriate speed changes, and render.
- Keep **Remotion as an optional renderer** for reusable animated titles, motion graphics, branded layouts, and more complex compositions. Do not force all editing through Remotion, and do not remove the existing Remotion project without a verified reason.
- Preserve authentic gameplay for projects that require it. For software tutorials, use real screen recordings/screenshots and never invent screens or functionality. Protect private information in all source material.
- Do not require paid video-generation APIs for ordinary edits. Only integrate paid services after I approve their cost and provide the required access.
- Do not auto-publish. Produce files and publishing copy for my review unless I separately authorize publishing and the account connection is available.

## Build only after the audit

After presenting the audit and plan, implement incrementally. First establish the multi-project structure and profiles while preserving Block Puzzle Burst as the first configured project. Then make one complete test video from real source footage, review it, and verify the final rendered file. Only after that should you add batch production, more project profiles, or a larger UI.

Be honest about what was inspected, what was implemented, what actually rendered, and any remaining blockers. Do not report a successful render unless you have checked the output file.
