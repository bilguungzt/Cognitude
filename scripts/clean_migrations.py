"""Sanitize Alembic migration files.

- Scans alembic/ and alembic/versions for files containing NUL bytes or non-UTF-8 encodings.
- Optionally fixes files by removing NUL bytes, removing BOM, and re-writing as UTF-8.
- Makes .bak copies before modifying.
- Runs a compile check after fixes.

Usage:
    python3 scripts/clean_migrations.py --check   # dry-run, report issues
    python3 scripts/clean_migrations.py --fix     # fix in-place (creates .bak backups)

This is safe and idempotent for plain-text migration files.
"""

from pathlib import Path
import argparse
import sys
import io
import py_compile

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_DIR = ROOT / 'alembic'


def detect_issues(path: Path):
    try:
        b = path.read_bytes()
    except Exception as e:
        return {'error': str(e)}
    issues = {}
    if b.find(b'\x00') != -1:
        issues['nul_byte'] = b.find(b'\x00')
    # detect BOMs
    if b.startswith(b"\xef\xbb\xbf"):
        issues['bom'] = 'utf-8-sig'
    # test utf-8 decode
    try:
        text = b.decode('utf-8')
    except UnicodeDecodeError as e:
        issues['decode_error'] = str(e)
    else:
        # if decode succeeded, ensure there are no surrogate escape markers etc
        pass
    return issues


def fix_file(path: Path):
    b = path.read_bytes()
    changed = False
    # remove NUL bytes
    if b.find(b'\x00') != -1:
        b = b.replace(b'\x00', b'')
        changed = True
    # remove BOM if present
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[len(b"\xef\xbb\xbf"):]
        changed = True
    # coerce to utf-8 text
    try:
        text = b.decode('utf-8')
    except UnicodeDecodeError:
        # try latin-1 fallback then encode utf-8
        try:
            text = b.decode('latin-1')
        except Exception:
            raise
        changed = True
    # write backup
    bak = path.with_suffix(path.suffix + '.bak')
    if not bak.exists():
        path.rename(bak)
        bak.write_text(text, encoding='utf-8')
        # write cleaned content to original path
        path.write_text(text, encoding='utf-8')
    else:
        # bak exists, just overwrite original with cleaned content
        path.write_text(text, encoding='utf-8')

    return changed


def compile_check(path: Path):
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fix', action='store_true', help='Fix files in-place (creates .bak)')
    p.add_argument('--check', action='store_true', help='Only check and report')
    args = p.parse_args()

    if not ALEMBIC_DIR.exists():
        print('ale mbic directory not found at', ALEMBIC_DIR)
        sys.exit(1)

    files = list(ALEMBIC_DIR.rglob('*.py'))
    if not files:
        print('No python files found under', ALEMBIC_DIR)
        return

    any_issues = False
    for f in files:
        issues = detect_issues(f)
        if issues:
            print(f'ISSUES: {f} -> {issues}')
            any_issues = True
            if args.fix:
                print('Fixing', f)
                try:
                    fix_file(f)
                    ok, err = compile_check(f)
                    if ok:
                        print('Compile ok for', f)
                    else:
                        print('Compile failed after fix for', f, 'error:', err)
                except Exception as e:
                    print('Error fixing', f, e)
        else:
            print('ok', f)
            # still run compile check to be safe
            ok, err = compile_check(f)
            if not ok:
                print('Compile problem in', f, err)
                any_issues = True

    if any_issues and not args.fix:
        print('\nFound issues. Re-run with --fix to attempt automatic repairs.')
        sys.exit(2)
    elif any_issues:
        print('\nFixes attempted. Please review .bak files.')
    else:
        print('\nNo issues found')

if __name__ == '__main__':
    main()
