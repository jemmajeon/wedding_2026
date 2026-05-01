@echo off
chcp 65001 > nul
setlocal

set GIT="C:\Users\JEON\AppData\Local\GitHubDesktop\app-3.5.2\resources\app\git\cmd\git.exe"
set SRC="C:\Users\JEON\projects\personal-dashboard.html"
set DST="C:\Users\JEON\projects\wedding_2026\hawaii.html"
set REPO="C:\Users\JEON\projects\wedding_2026"

echo === Sync personal-dashboard.html -^> hawaii.html ===
copy /Y %SRC% %DST%
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
%GIT% commit -m "Update dashboard"

echo === Push ===
%GIT% push
if errorlevel 1 goto :error

echo.
echo ====================================================
echo  Done! Live in 1-2 min:
echo  https://jemmajeon.github.io/wedding_2026/hawaii.html
echo ====================================================
goto :end

:error
echo.
echo *** ERROR - see messages above ***

:end
echo.
pause