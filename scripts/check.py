#!/usr/bin/env python3
"""Cross-platform check script (Python version of check.sh)."""
import sys
import os
import subprocess
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run command and return exit code."""
    print(f"\n== {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode

def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ['all', 'tests', 'lint']:
        print(f"usage: {sys.argv[0]} [all|tests|lint]", file=sys.stderr)
        return 2
    
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    # Change to repository root
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)
    
    python_bin = sys.executable
    
    exit_code = 0
    
    if target != 'lint':
        # Unit tests
        exit_code |= run_cmd(f"{python_bin} -m unittest discover -s tests")
        
        # Compile check
        exit_code |= run_cmd(f"{python_bin} -m compileall -q evals")
        
        # Check for invisible characters
        exit_code |= run_cmd(f"{python_bin} scripts/check_control_chars.py")
    
    if target != 'tests':
        # Clean samples check
        format_args = ""
        if os.environ.get('ANTI_SLOP_FORMAT'):
            format_args = f"--format {os.environ.get('ANTI_SLOP_FORMAT')}"
        
        exit_code |= run_cmd(f"{python_bin} en/ste-lint.py {format_args} --max 2 en/samples/ste.md")
        exit_code |= run_cmd(f"{python_bin} ru/ru-ste-lint.py {format_args} --max 2 ru/samples/utr.md")
        
        # Baseline scores
        exit_code |= run_cmd(f"{python_bin} en/ste-lint.py en/samples/baseline.md")
        exit_code |= run_cmd(f"{python_bin} ru/ru-ste-lint.py ru/samples/baseline.md")
    
    if exit_code == 0:
        print("\nAll checks passed.")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
