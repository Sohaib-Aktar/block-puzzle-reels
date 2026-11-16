@echo off
REM trim_and_scale.bat
REM FFmpeg trim + scale to Instagram Reel spec (1080x1920)
REM
REM Usage:
REM   trim_and_scale.bat <input_file> <start_time> <duration> <output_file>
REM
REM Example:
REM   trim_and_scale.bat ..\..\Raw_input_files\recording_1.mp4 00:01:30 00:00:15 out_test.mp4
REM
REM Requires FFmpeg on PATH, or set FFMPEG_PATH below.

SET FFMPEG_PATH=ffmpeg

IF "%~4"=="" (
  echo Usage: trim_and_scale.bat ^<input^> ^<start_time^> ^<duration^> ^<output^>
  echo Example: trim_and_scale.bat recording.mp4 00:01:30 00:00:15 out.mp4
  exit /b 1
)

SET INPUT=%~1
SET START=%~2
SET DUR=%~3
SET OUTPUT=%~4

echo.
echo Trimming and scaling to 1080x1920 ...
echo Input  : %INPUT%
echo Start  : %START%
echo Duration: %DUR%
echo Output : %OUTPUT%
echo.

%FFMPEG_PATH% ^
  -ss %START% ^
  -i "%INPUT%" ^
  -t %DUR% ^
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" ^
  -c:v libx264 -profile:v high -crf 23 -preset fast ^
  -c:a aac -b:a 128k ^
  -pix_fmt yuv420p ^
  -movflags +faststart ^
  "%OUTPUT%"

IF ERRORLEVEL 1 (
  echo ERROR: FFmpeg failed. Check that FFmpeg is installed and on PATH.
  exit /b 1
)

echo.
echo Done: %OUTPUT%
