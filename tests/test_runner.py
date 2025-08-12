#!/usr/bin/env python3
"""
Test runner for AIRefiner - runs all tests in organized sequence
"""

import os
import subprocess
import sys


# Unicode-safe print function for Windows console
def safe_print(*args, **kwargs):
    """Print function that handles Unicode characters safely on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Replace Unicode characters with ASCII equivalents for Windows console
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common Unicode symbols with ASCII equivalents
                unicode_replacements = {
                    '🧪': '[TEST]',
                    '✅': '[PASS]',
                    '❌': '[FAIL]',
                    '⚠️': '[WARN]',
                    '🔧': '[DEBUG]',
                    '📊': '[INFO]',
                    '🚀': '[RUN]',
                    '🎉': '[SUCCESS]',
                    '⭐': '[STAR]',
                    '📋': '[LIST]',
                    '💾': '[CACHE]',
                    '⚪': '[INFO]',
                    '🔍': '[SEARCH]',
                    '🌐': '[TRANSLATE]',
                    '🤖': '[AI]'
                }
                for unicode_char, ascii_equiv in unicode_replacements.items():
                    arg = arg.replace(unicode_char, ascii_equiv)
            safe_args.append(arg)
        print(*safe_args, **kwargs)


def safe_decode_output(output):
    """Safely decode subprocess output, replacing Unicode characters"""
    if not output:
        return ""

    unicode_replacements = {
        '🧪': '[TEST]',
        '✅': '[PASS]',
        '❌': '[FAIL]',
        '⚠️': '[WARN]',
        '🔧': '[DEBUG]',
        '📊': '[INFO]',
        '🚀': '[RUN]',
        '🎉': '[SUCCESS]',
        '⭐': '[STAR]',
        '📋': '[LIST]',
        '💾': '[CACHE]',
        '⚪': '[INFO]',
        '🔍': '[SEARCH]',
        '🌐': '[TRANSLATE]',
        '🤖': '[AI]'
    }

    safe_output = output
    for unicode_char, ascii_equiv in unicode_replacements.items():
        safe_output = safe_output.replace(unicode_char, ascii_equiv)

    return safe_output


# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_test(test_file, description):
    """Run a single test file"""
    safe_print(f"\n{'=' * 50}")
    safe_print(f"🧪 {description}")
    safe_print(f"{'=' * 50}")

    try:
        # Use PYTHONIOENCODING to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        result = subprocess.run([sys.executable, test_file],
                                capture_output=True, text=True, cwd=project_root,
                                env=env, encoding='utf-8', errors='replace')

        if result.returncode == 0:
            safe_output = safe_decode_output(result.stdout)
            safe_print(safe_output)
            safe_print(f"✅ {description} - PASSED")
            return True
        else:
            safe_stdout = safe_decode_output(result.stdout)
            safe_stderr = safe_decode_output(result.stderr)
            safe_print(safe_stdout)
            safe_print(safe_stderr)
            safe_print(f"❌ {description} - FAILED")
            return False

    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False


def main():
    """Run all tests in sequence"""
    safe_print("🚀 AIRefiner Test Suite")
    safe_print("Running all tests in organized sequence...\n")

    tests = [
        ("tests/test_installation.py", "Installation & Dependencies Test"),
        ("tests/test_auto_translation.py", "Auto-Translation Feature Test"),
        ("tests/test_providers.py", "AI Provider Integration Test"),
    ]

    passed = 0
    failed = 0

    for test_file, description in tests:
        test_path = os.path.join(project_root, test_file)
        if os.path.exists(test_path):
            if run_test(test_path, description):
                passed += 1
            else:
                failed += 1
        else:
            safe_print(f"⚠️  Test file not found: {test_file}")
            failed += 1

    safe_print(f"\n{'=' * 50}")
    safe_print(f"🏁 TEST SUITE COMPLETE")
    safe_print(f"{'=' * 50}")
    safe_print(f"✅ Passed: {passed}")
    safe_print(f"❌ Failed: {failed}")
    safe_print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    if failed == 0:
        safe_print(f"\n🎉 ALL TESTS PASSED! Your AIRefiner is ready to use.")
        safe_print(f"Run: python main.py")
    else:
        safe_print(f"\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
