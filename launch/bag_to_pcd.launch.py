import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

PKG = 'livox_camera_calib'


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('bag_file', default_value='',
                              description='Path to the ROS 2 bag directory'),
        DeclareLaunchArgument('lidar_topic', default_value='/livox/lidar'),
        DeclareLaunchArgument('pcd_file',
                              default_value=os.path.join(os.getcwd(), '0.pcd')),
        DeclareLaunchArgument('is_custom_msg', default_value='false'),
        Node(
            package=PKG,
            executable='bag_to_pcd',
            name='bag_to_pcd',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'bag_file': LaunchConfiguration('bag_file'),
                'lidar_topic': LaunchConfiguration('lidar_topic'),
                'pcd_file': LaunchConfiguration('pcd_file'),
                'is_custom_msg': LaunchConfiguration('is_custom_msg'),
            }],
        ),
    ])
