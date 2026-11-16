$base = 'c:\Users\Dell\Downloads\video gen'
$dirs = @(
  'projects\block-puzzle-burst\campaigns\30-day-challenge\briefs',
  'config\studio_settings',
  'config\platform_presets',
  'scripts',
  'renderers\ffmpeg',
  'renderers\remotion',
  'docs',
  'outputs\block-puzzle-burst\30-day-challenge\day-01-founder-intro\captions',
  'outputs\block-puzzle-burst\30-day-challenge\day-01-founder-intro\final',
  'outputs\block-puzzle-burst\30-day-challenge\day-02-satisfying-clear\captions',
  'outputs\block-puzzle-burst\30-day-challenge\day-02-satisfying-clear\final',
  'outputs\block-puzzle-burst\30-day-challenge\day-03-puzzle-challenge\captions',
  'outputs\block-puzzle-burst\30-day-challenge\day-03-puzzle-challenge\final',
  'outputs\block-puzzle-burst\30-day-challenge\solve-it-reel\captions',
  'outputs\block-puzzle-burst\30-day-challenge\solve-it-reel\final'
)
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Path (Join-Path $base $d) -Force | Out-Null
}
Write-Host 'All Phase 1 directories created successfully'
