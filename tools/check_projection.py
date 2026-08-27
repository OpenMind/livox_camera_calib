#!/usr/bin/env python3
"""Project a pcd into an image with a given extrinsic and report what happens.

When the calibration produces an empty overlay it is not obvious whether the
extrinsic is wrong, the depth gate rejected everything, or the intensities are
on a scale the projection does not expect. This answers that directly: it
prints how many points survive each stage and writes an overlay coloured by
depth.

Example:
    python3 tools/check_projection.py \
        --pcd ~/m20_calib/pcd/0.pcd --image ~/m20_calib/image/0.png \
        --scene-config config/config_m20_front.yaml \
        --params config/calib_m20_front.yaml \
        --output ~/m20_calib/check.png
"""

import argparse
import re
import sys

import numpy as np
import cv2


def read_pcd(path, stride):
    """Read an ASCII pcd, keeping every `stride`-th point. Returns (N,4)."""
    fields, count, data_type = [], 0, None
    with open(path, 'r', errors='replace') as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            key = parts[0].upper()
            if key == 'FIELDS':
                fields = parts[1:]
            elif key == 'POINTS':
                count = int(parts[1])
            elif key == 'DATA':
                data_type = parts[1]
                break
        if data_type != 'ascii':
            sys.exit('only ASCII pcd is supported (this one is %s). Convert '
                     'with: pcl_convert_pcd_ascii_binary in.pcd out.pcd 0'
                     % data_type)
        idx = {name: i for i, name in enumerate(fields)}
        for name in ('x', 'y', 'z'):
            if name not in idx:
                sys.exit('pcd has no %s field (fields: %s)' % (name, fields))
        ii = idx.get('intensity')
        pts = []
        for n, line in enumerate(f):
            if n % stride:
                continue
            v = line.split()
            if len(v) < 3:
                continue
            try:
                pts.append((float(v[idx['x']]), float(v[idx['y']]),
                            float(v[idx['z']]),
                            float(v[ii]) if ii is not None else 0.0))
            except ValueError:
                continue
    print('pcd header says %d points; loaded %d (stride %d)'
          % (count, len(pts), stride))
    return np.asarray(pts, dtype=np.float64)


def read_scene_config(path):
    """Pull the 4x4 ExtrinsicMat and the projection depth gates out of the
    OpenCV FileStorage config (PyYAML cannot parse its !!opencv-matrix tags)."""
    text = open(path).read()
    m = re.search(r'ExtrinsicMat:.*?data:\s*\[(.*?)\]', text, re.S)
    if not m:
        sys.exit('no ExtrinsicMat found in %s' % path)
    values = [float(v) for v in m.group(1).replace('\n', ' ').split(',')]
    if len(values) != 16:
        sys.exit('ExtrinsicMat has %d values, expected 16' % len(values))
    mat = np.asarray(values).reshape(4, 4)

    def scalar(key, default):
        m = re.search(re.escape(key) + r':\s*([-\d.eE+]+)', text)
        return float(m.group(1)) if m else default

    return mat[:3, :3], mat[:3, 3], scalar('Projection.min_depth', 2.5), \
        scalar('Projection.max_depth', 50.0), \
        scalar('Projection.min_camera_depth', 0.1)


def read_result_file(path):
    """Read the 4x4 comma-separated matrix the calibration writes out."""
    rows = [[float(v) for v in line.split(',')]
            for line in open(path).read().splitlines() if line.strip()]
    mat = np.asarray(rows)
    if mat.shape != (4, 4):
        sys.exit('%s is %s, expected a 4x4 matrix' % (path, mat.shape))
    return mat[:3, :3], mat[:3, 3]


def read_intrinsics(path):
    """Pull camera_matrix / dist_coeffs out of the ROS 2 params file."""
    text = open(path).read()
    m = re.search(r'camera_matrix:\s*\[(.*?)\]', text, re.S)
    if not m:
        sys.exit('no camera_matrix found in %s' % path)
    k = [float(v) for v in m.group(1).replace('\n', ' ').split(',')]
    m = re.search(r'dist_coeffs:\s*\[(.*?)\]', text, re.S)
    d = [float(v) for v in m.group(1).replace('\n', ' ').split(',')] if m \
        else [0.0] * 5
    return np.asarray(k).reshape(3, 3), np.asarray(d)


def pct(name, values):
    if len(values) == 0:
        print('  %-22s (empty)' % name)
        return
    q = np.percentile(values, [0, 1, 50, 99, 100])
    print('  %-22s min %.3f  p1 %.3f  median %.3f  p99 %.3f  max %.3f'
          % (name, *q))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pcd', required=True)
    p.add_argument('--image', required=True)
    p.add_argument('--scene-config', required=True,
                   help='config_*.yaml holding ExtrinsicMat')
    p.add_argument('--params', required=True,
                   help='calib_*.yaml holding camera_matrix')
    p.add_argument('--extrinsic',
                   help='result file (extrinsic.txt) to use instead of the '
                        'ExtrinsicMat in the scene config, so a finished '
                        'calibration can be inspected without re-running it')
    p.add_argument('--output', default='check.png')
    p.add_argument('--stride', type=int, default=20,
                   help='keep every Nth point (default 20)')
    p.add_argument('--min-depth', type=float, default=None,
                   help='override Projection.min_depth')
    p.add_argument('--max-depth', type=float, default=None,
                   help='override Projection.max_depth')
    args = p.parse_args()

    image = cv2.imread(args.image)
    if image is None:
        sys.exit('could not read %s' % args.image)
    h, w = image.shape[:2]
    K, dist = read_intrinsics(args.params)
    R, t, min_depth, max_depth, min_cam_depth = read_scene_config(
        args.scene_config)
    if args.extrinsic:
        R, t = read_result_file(args.extrinsic)
        print('using extrinsic from %s' % args.extrinsic)
    if args.min_depth is not None:
        min_depth = args.min_depth
    if args.max_depth is not None:
        max_depth = args.max_depth

    print('image %dx%d, fx %.1f fy %.1f cx %.1f cy %.1f'
          % (w, h, K[0, 0], K[1, 1], K[0, 2], K[1, 2]))
    print('depth gate: %.2f .. %.2f m, min camera depth %.2f m'
          % (min_depth, max_depth, min_cam_depth))

    pts = read_pcd(args.pcd, args.stride)
    xyz, intensity = pts[:, :3], pts[:, 3]
    rng = np.linalg.norm(xyz, axis=1)
    print('\nLiDAR cloud, in its own frame:')
    pct('range (m)', rng)
    pct('intensity', intensity)
    for axis, name in enumerate('xyz'):
        pct('%s (m)' % name, xyz[:, axis])

    cam = xyz @ R.T + t          # points in the camera frame
    in_range = (rng > min_depth) & (rng < max_depth)
    in_front = cam[:, 2] > min_cam_depth
    print('\nStage by stage:')
    print('  %8d points loaded' % len(xyz))
    print('  %8d pass the range gate (%.1f%%)'
          % (in_range.sum(), 100.0 * in_range.sum() / max(len(xyz), 1)))
    print('  %8d are in front of the camera (%.1f%%)'
          % (in_front.sum(), 100.0 * in_front.sum() / max(len(xyz), 1)))

    keep = in_range & in_front
    if not keep.any():
        print('\nNothing survives; the overlay would be empty.')
        if in_front.sum() == 0:
            print('The whole cloud is BEHIND the camera -> the extrinsic '
                  'rotation or translation sign is wrong.')
        else:
            print('Points exist in front of the camera but the range gate '
                  'rejects them. Try --min-depth 0.3.')
        sys.exit(1)

    uv, _ = cv2.projectPoints(xyz[keep], cv2.Rodrigues(R)[0], t, K, dist)
    uv = uv.reshape(-1, 2)
    inside = (uv[:, 0] > 0) & (uv[:, 0] < w) & (uv[:, 1] > 0) & (uv[:, 1] < h)
    print('  %8d land inside the image (%.1f%% of the survivors)'
          % (inside.sum(), 100.0 * inside.sum() / max(keep.sum(), 1)))

    if not inside.any():
        print('\nEverything projects outside the image bounds -> the '
              'extrinsic is pointing the camera the wrong way.')
        sys.exit(1)

    depth = cam[keep][inside][:, 2]
    lo, hi = np.percentile(depth, [2, 98])
    shade = np.clip((depth - lo) / max(hi - lo, 1e-6), 0, 1)
    colors = cv2.applyColorMap((shade * 255).astype(np.uint8),
                               cv2.COLORMAP_JET).reshape(-1, 3)
    overlay = image.copy()
    for (u, v), c in zip(uv[inside].astype(int), colors):
        cv2.circle(overlay, (u, v), 1, tuple(int(x) for x in c), -1)
    cv2.imwrite(args.output, overlay)
    print('\nwrote %s' % args.output)


if __name__ == '__main__':
    main()
