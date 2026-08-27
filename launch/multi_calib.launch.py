import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

PKG = 'livox_camera_calib'


def generate_launch_description():
    share_dir = get_package_share_directory(PKG)
    default_params = os.path.join(share_dir, 'config', 'multi_calib.yaml')
    default_rviz = os.path.join(share_dir, 'rviz_cfg', 'calib.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=default_params,
                              description='Path to the calibration params file'),
        DeclareLaunchArgument('rviz_config', default_value=default_rviz),
        Node(
            package=PKG,
            executable='lidar_camera_multi_calib',
            name='lidar_camera_multi_calib',
            output='screen',
            emulate_tty=True,
            parameters=[LaunchConfiguration('params_file')],
        ),
        # RViz needs the "livox" fixed frame to exist in the TF tree.
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='livox_static_tf',
            arguments=['--frame-id', 'map', '--child-frame-id', 'livox'],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', LaunchConfiguration('rviz_config')],
        ),
    ])
