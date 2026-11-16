@echo off
REM trim_and_scale.bat
REM FFmpeg trim + scale to Instagram Reel spec (1080x1920)
REM
REM Usage:
REM   trim_and_scale.bat <input_file> <start_time> <duration> <output_file>
REM
REM Example:
REM   renderers\ffmpeg\trim_and_scale.bat Raw_input_files\recording_3.mp4 00:00:10 00:00:05 output.mp4

IF "%~4"=="" (
  echo Usage: trim_and_scale.bat ^<input^> ^<start_time^> ^<duration^> ^<output^>
  echo Example: trim_and_scale.bat recording.mp4 00:00:10 00:00:05 out.mp4
  exit /b 1
)

SET INPUT=%~1
SET START=%~2
SET DUR=%~3
SET OUTPUT=%~4
SET SCRIPT_DIR=%~dp0
SET MY_VIDEO_DIR=%SCRIPT_DIR%..\..\my-video

echo.
echo Trimming and scaling to 1080x1920 ...
echo Input    : %INPUT%
echo Start    : %START%
echo Duration : %DUR%
echo Output   : %OUTPUT%
echo.

REM Check if system ffmpeg exists
where ffmpeg >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
  echo Using system FFmpeg...
  ffmpeg -ss %START% -i "%INPUT%" -t %DUR% -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" -c:v libx264 -profile:v high -crf 23 -preset fast -c:a aac -b:a 128k -pix_fmt yuv420p -movflags +faststart -y "%OUTPUT%"
) ELSE (
  echo System FFmpeg not found on PATH. Using Remotion bundled FFmpeg...
  call npx --prefix "%MY_VIDEO_DIR%" remotion ffmpeg -ss %START% -i "%INPUT%" -t %DUR% -vf "scale=1080:1920" -c:v libx264 -profile:v high -crf 23 -preset fast -c:a aac -b:a 128k -pix_fmt yuv420p -movflags +faststart -y "%OUTPUT%"
)

IF ERRORLEVEL 1 (
  echo.
  echo ERROR: Video processing failed.
  exit /b 1
)

echo.
echo Done: %OUTPUT%
