#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Configure the pinned, experimentally verified macOS SYCL build profile."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'install', 'adaptivecpp', 'dependencies', 'eigen', 'ceres'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--homebrew', type=Path, default=Path('/opt/homebrew'))
    parser.add_argument('--llvm', type=Path)
    parser.add_argument('--sdk', type=Path)
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--metal', action='store_true', help='Enable the float profile and require a Metal GPU')
    parser.add_argument('--print-only', action='store_true')
    args = parser.parse_args()
    values = {name: str(getattr(args, name).absolute()) for name in
              ('build', 'install', 'adaptivecpp', 'dependencies', 'eigen', 'ceres', 'homebrew')}
    values['source'] = str(Path(__file__).absolute().parents[2])
    values['llvm'] = str((args.llvm or args.homebrew / 'opt/llvm@20').absolute())
    values['sdk'] = str(args.sdk.absolute()) if args.sdk else subprocess.check_output(
        ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
    template = json.loads(Path(__file__).with_name('cmake-arguments.json').read_text())
    command = [args.cmake] + [value.format(**values) for value in template]
    if args.metal:
        command.append('-DCMAKE_CXX_FLAGS=-DAV_SYCL_METAL_FLOAT=1')
    if args.print_only:
        print(json.dumps(command, indent=2))
    else:
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
