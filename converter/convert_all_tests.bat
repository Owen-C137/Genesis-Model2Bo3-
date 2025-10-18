@echo off
echo ========================================
echo Converting all ROTATION_TEST files to XMODEL_BIN
echo ========================================
echo.

REM Set the path to export2bin
set EXPORT2BIN="D:\SteamLibrary\steamapps\common\Call of Duty Black Ops III\bin\export2bin.exe"

REM Check if export2bin exists
if not exist %EXPORT2BIN% (
    echo ERROR: export2bin.exe not found at %EXPORT2BIN%
    echo Please verify the path is correct
    pause
    exit /b 1
)

echo Converting test files...
echo.

cd output

for %%f in (ROTATION_TEST_*.XMODEL_EXPORT) do (
    echo Converting %%f...
    %EXPORT2BIN% "%%f"
)

echo.
echo ========================================
echo Conversion complete!
echo ========================================
echo.
echo BIN files created in converter\output\
echo Now import them in BO3 APE to find the correct rotation
echo.
pause
