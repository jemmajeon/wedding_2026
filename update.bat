@echo off
chcp 65001 > nul
setlocal

set GIT="C:\Users\JEON\AppData\Local\GitHubDesktop\app-3.5.2\resources\app\git\cmd\git.exe"
set REPO="C:\Users\JEON\projects\wedding_2026"

set SRC1="C:\Users\JEON\projects\personal-dashboard.html"
set DST1="C:\Users\JEON\projects\wedding_2026\hawaii.html"

set SRC2="C:\Users\JEON\projects\hawaii-trip-dashboard.html"
set DST2="C:\Users\JEON\projects\wedding_2026\hawaii-trip-dashboard.html"

echo === Sync personal-dashboard.html -^> hawaii.html ===
copy /Y %SRC1% %DST1%
if errorlevel 1 goto :error

echo === Sync hawaii-trip-dashboard.html ===
copy /Y %SRC2% %DST2%
if errorlevel 1 goto :error

cd /d %REPO%

echo === Add ===
%GIT% add -A

%GIT% diff --cached --quiet
if not errorlevel 1 (
  echo No changes to commit.
  goto :end
)

echo === Commit ===
%GIT% commit -m "Update dashboards"

echo === Push ===
%GIT% push
if errorlevel 1 goto :error

echo.
echo ====================================================
echo  Done! Live in 1-2 min:
echo  https://jemmajeon.github.io/wedding_2026/hawaii.html
echo  https://jemmajeon.github.io/wedding_2026/hawaii-trip-dashboard.html
echo ====================================================
goto :end

:error
echo.
echo *** ERROR - see messages above ***

:end
echo.
pause