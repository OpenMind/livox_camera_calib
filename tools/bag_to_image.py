#!/usr/bin/env python3
"""Extract image frames from a ROS 2 bag to PNG files.

The calibration node wants a single still image next to the accumulated pcd,
and `image_view` is not always installed, so this pulls the frames straight
out of the bag with rosbag2_py. Supports sensor_msgs/Image and
sensor_msgs/CompressedImage.

Example:
    python3 tools/bag_to_image.py ~/m20_calib/bag \
        --topic /camera/camera/color/image_raw \
        --output ~/m20_calib/image/0.png
"""

import argparse
import os
import sys

import numpy as np
import cv2
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

# Image encodings we can turn into a BGR image without cv_bridge.
_CHANNELS = {'mono8': 1, 'mono16': 1, '8UC1': 1, '16UC1': 1,
             'bgr8': 3, 'rgb8': 3, '8UC3': 3,
             'bgra8': 4, 'rgba8': 4, '8UC4': 4}


def image_to_bgr(msg):
    channels = _CHANNELS.get(msg.encoding)
    if channels is None:
        raise RuntimeError('unsupported image encoding: %s' % msg.encoding)
    dtype = np.uint16 if '16' in msg.encoding else np.uint8
    buf = np.frombuffer(msg.data, dtype=dtype)
    img = buf.reshape(msg.height, msg.step // np.dtype(dtype).itemsize)
    img = img[:, :msg.width * channels].reshape(msg.height, msg.width, channels)
    if msg.encoding in ('rgb8', 'rgba8'):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if channels == 3
                           else cv2.COLOR_RGBA2BGR)
    elif channels == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def open_bag(path):
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=path),
                rosbag2_py.ConverterOptions('', ''))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    return reader, types


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bag', help='path to the bag directory')
    parser.add_argument('--topic', required=True, help='image topic')
    parser.add_argument('--output', required=True,
                        help='output png (or output directory with --all)')
    parser.add_argument('--index', type=int, default=None,
                        help='frame index to save; default is the middle one')
    parser.add_argument('--all', action='store_true',
                        help='save every frame as <output>/%%04d.png')
    args = parser.parse_args()

    reader, types = open_bag(args.bag)
    if args.topic not in types:
        sys.exit('topic %s not in bag. Available:\n  %s'
                 % (args.topic, '\n  '.join(sorted(types))))
    msg_type = get_message(types[args.topic])
    compressed = types[args.topic].endswith('CompressedImage')

    frames = []
    while reader.has_next():
        topic, data, _ = reader.read_next()
        if topic == args.topic:
            frames.append(deserialize_message(data, msg_type))
    if not frames:
        sys.exit('no messages found on %s' % args.topic)

    def decode(msg):
        if compressed:
            return cv2.imdecode(np.frombuffer(msg.data, np.uint8),
                                cv2.IMREAD_COLOR)
        return image_to_bgr(msg)

    if args.all:
        os.makedirs(args.output, exist_ok=True)
        for i, msg in enumerate(frames):
            path = os.path.join(args.output, '%04d.png' % i)
            cv2.imwrite(path, decode(msg))
        print('saved %d frames to %s' % (len(frames), args.output))
        return

    index = args.index if args.index is not None else len(frames) // 2
    if not 0 <= index < len(frames):
        sys.exit('index %d out of range (bag has %d frames)'
                 % (index, len(frames)))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    cv2.imwrite(args.output, decode(frames[index]))
    print('saved frame %d of %d to %s' % (index, len(frames), args.output))


if __name__ == '__main__':
    main()
