# Security Audit

## Findings and Patches
1. Command injection via YouTube playlist URL (shell command).
   - File: `VivaanXmusic/platforms/Youtube.py` lines 75-105, 272-296.
   - Patch: replaced shell execution with `asyncio.create_subprocess_exec` arg list and added `_has_unsafe_url_chars` to block `; & | $ \n \r \`` in playlist URLs.
   - File: `VivaanXmusic/platforms/Youtube.backup` lines 71-101, 253-272.
   - Patch: same replacement and URL validation for the backup implementation.
2. Shell execution for ffmpeg speedup stream.
   - File: `VivaanXmusic/core/call.py` lines 168-179.
   - Patch: replaced `asyncio.create_subprocess_shell` with `asyncio.create_subprocess_exec` and explicit argument list.
3. Shell command execution in update/restart flow.
   - File: `VivaanXmusic/plugins/sudo/restart.py` lines 30-150 and 153-178.
   - Patch: replaced `os.system` calls with `subprocess.run`/`subprocess.Popen` using list arguments; added restart helpers to preserve behavior without shell usage.
4. Path traversal via YouTube title-derived filenames.
   - File: `VivaanXmusic/platforms/Youtube.py` lines 84-90 and 426-670.
   - Patch: added `_safe_filename` to strip path separators and collapse `..` before building download paths.
   - File: `VivaanXmusic/platforms/Youtube.backup` lines 80-86 and 380-480.
   - Patch: same filename sanitization for the backup implementation.
5. Secrets safety (.env not ignored).
   - File: `.gitignore` line 14.
   - Patch: added `.env` to ignore list to prevent accidental commits.
