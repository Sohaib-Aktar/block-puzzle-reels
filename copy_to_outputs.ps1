$base = 'c:\Users\Dell\Downloads\video gen'
Copy-Item "$base\generated_outputs\videos\Day_02_MyDayTwoReel.mp4" "$base\outputs\block-puzzle-burst\30-day-challenge\day-02-satisfying-clear\final\instagram_reel.mp4" -Force
Copy-Item "$base\generated_outputs\videos\Day_03_Puzzle_Challenge.mp4" "$base\outputs\block-puzzle-burst\30-day-challenge\day-03-puzzle-challenge\final\instagram_reel.mp4" -Force
Write-Host 'Videos copied to outputs/'
