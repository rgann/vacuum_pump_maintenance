@echo off
echo Populating Supabase database with seed data...
python populate_supabase.py
if %ERRORLEVEL% EQU 0 (
    echo Database population completed successfully.
) else (
    echo Database population failed. Check the logs for details.
)
pause
