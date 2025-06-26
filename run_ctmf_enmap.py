#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys

def load_image(tarball):
    print(f"▶️ Loading Docker image from {tarball} …")
    subprocess.run(['docker', 'load', '-i', tarball], check=True)

def ensure_dir(path):
    """If path is a file parent, return its dirname; if it's a directory, ensure it exists and return it."""
    abs_path = os.path.abspath(path)
    if os.path.isdir(abs_path):
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    else:
        parent = os.path.dirname(abs_path)
        if not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        return parent

def collect_mounts(paths):
    """Given a list of file/dir paths, return a dict {host_dir:host_dir} for mounting."""
    mounts = {}
    for p in paths:
        d = ensure_dir(p)
        mounts[d] = d
    return mounts

def build_docker_run_cmd(image, mounts, script_args):
    cmd = ['docker', 'run', '--rm']
    for host_dir, cont_dir in mounts.items():
        cmd += ['-v', f'{host_dir}:{cont_dir}']
    cmd += [image] + script_args
    return cmd

def main():
    parser = argparse.ArgumentParser(
        description="Load an EnMAP Docker image from tarball and run single-image processing mode"
    )
    parser.add_argument(
        '-t','--tarball',
        required=True,
        help="Path to your saved image tarball (e.g. enmap-ch4-mapper.tar)"
    )
    parser.add_argument(
        '--image',
        default='enmap-ch4-mapper:latest',
        help="Name:tag of the image inside the tarball (default: enmap-ch4-mapper:latest)"
    )
    # single-mode arguments
    parser.add_argument('vnir', help='VNIR spectral image (GeoTIFF)')
    parser.add_argument('swir', help='SWIR spectral image (GeoTIFF)')
    parser.add_argument('meta', help='Metadata XML file')
    parser.add_argument('lut', help='LUT HDF5 (.hdf5)')
    parser.add_argument('output', help='Output directory')
    parser.add_argument('-k', type=int, default=1, help='Cluster count')

    args = parser.parse_args()

    # 1) load the image
    load_image(args.tarball)

    # 2) determine mounts and script arguments
    mounts = [args.vnir, args.swir, args.meta, args.lut, args.output]
    script_args = [
        args.vnir, args.swir, args.meta, args.lut, args.output,
        '-k', str(args.k)
    ]

    mount_map = collect_mounts(mounts)

    # 3) build & print the docker run command
    cmd = build_docker_run_cmd(args.image, mount_map, script_args)
    print("▶️ Running container:\n   " + " ".join(cmd))

    # 4) execute
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()
