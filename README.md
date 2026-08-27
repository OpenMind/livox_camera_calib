# lidar_camera_calib
**lidar_camera_calib** is a robust, high accuracy extrinsic calibration tool between high resolution LiDAR (e.g. Livox) and camera in targetless environment. Our algorithm can run in both indoor and outdoor scenes, and only requires edge information in the scene. If the scene is suitable, we can achieve pixel-level accuracy similar to or even beyond the target based method.
<div align="center">
    <img src="pics/color_cloud.png" width = 100% >
    <font color=#a0a0a0 size=2>An example of a outdoor calibration scenario. We color the point cloud with the calibrated extrinsic and compare with actual image. A and C are locally enlarged
views of the point cloud. B and D are parts of the camera image
corresponding to point cloud in A and C.</font>
</div>

## Info
New features:
1. Support muti-scenes calibration (more accurate and robust)

## Related paper
Related paper available on arxiv:  
[Pixel-level Extrinsic Self Calibration of High Resolution LiDAR and Camera in Targetless Environments](http://arxiv.org/abs/2103.01627)
## Related video
Related video: https://youtu.be/e6Vkkasc4JI

## 1. Prerequisites
### 1.1 **Ubuntu** and **ROS 2**
Ubuntu 64-bit 22.04 or 24.04.
ROS 2 Humble, Iron or Jazzy. [ROS 2 Installation](https://docs.ros.org/en/rolling/Installation.html) and its additional ROS 2 packages:

```
    sudo apt-get install ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-pcl-conversions ros-$ROS_DISTRO-rosbag2 ros-$ROS_DISTRO-rviz2
```

> This is the ROS 2 branch. The `livox_ros_driver` `CustomMsg` is regenerated
> inside this package (`msg/CustomMsg.msg`), so no external Livox driver package
> is needed to read bags that contain it.

### 1.2 **Eigen**
Follow [Eigen Installation](http://eigen.tuxfamily.org/index.php?title=Main_Page)

### 1.3 **Ceres Solver**
Follow [Ceres Installation](http://ceres-solver.org/installation.html).

### 1.4 **PCL**
Follow [PCL Installation](http://www.pointclouds.org/downloads/linux.html). (Our code is tested with PCL1.7)

## 2. Build
Clone the repository and build with colcon:

```
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/hku-mars/livox_camera_calib.git
cd ~/ros2_ws
colcon build --packages-select livox_camera_calib --cmake-args -DCMAKE_BUILD_TYPE=Release
source ~/ros2_ws/install/setup.bash
```

## 3. Run our example
The exmaple dataset can be download from [**OneDrive**](https://connecthkuhk-my.sharepoint.com/:f:/g/personal/ycj1_connect_hku_hk/EuZs1x2RHbxFikjsvt9qf80BD8Wjj05ZhVGRgzfzLCQUCQ?e=un8r1y) and [**BaiduNetDisk(百度网盘)**](https://pan.baidu.com/s/1oz3unqsmDnFvBExY5fiBJQ?pwd=i964)
### 3.1 Single scene calibration
Download [Our pcd and iamge file](https://connecthkuhk-my.sharepoint.com/:f:/g/personal/ycj1_connect_hku_hk/EsPKJ-If659EkzSgApVmGToBLQdxo61p6SG8EEruR6C9Hw?e=beoUXX) to your local path, and then change the file path in **calib.yaml** to your data path. Then directly run
```
ros2 launch livox_camera_calib calib.launch.py
```

To use a params file outside the install space:
```
ros2 launch livox_camera_calib calib.launch.py params_file:=/path/to/calib.yaml
```
You will get the following result. (Sensor suite: Livox Avia + Realsense-D435i)
<div align="center">
    <img src="pics/single_calib_case.png" width = 100% >
    <font color=#a0a0a0 size=2>An example of single scene calibration.</font>
</div>

### 3.2 Multi scenes calibration
Download [Our pcd and iamge file](https://connecthkuhk-my.sharepoint.com/:f:/g/personal/ycj1_connect_hku_hk/Ej5-eYv9pJdLj4cOe-qhvO8BaSxFJ0HZU-2savbqHkzvKQ?e=PMjqY6) to your local path, and then change the file path in **multi_calib.yaml** to your data path. Then directly run
```
ros2 launch livox_camera_calib multi_calib.launch.py
```
The projected images obtained by initial extrinsic parameters. (Sensor Suite: Livox Horizon + MVS camera)
<div align="center">
    <img src="pics/initial_extrinsic.png" width = 100% >
    <font color=#a0a0a0 size=2>An example of multi scenes calibration. The projected image obtained by theinitial extrinsic parameters</font>
</div>
Rough calibration is used to deal with the bad extrinsic.
<div align="center">
    <img src="pics/after_rough_calib.png" width = 100% >
    <font color=#a0a0a0 size=2>The projected image obtained by the extrinsic parameters after rough calibration</font>
</div>
Then we finally get a fine extrinsic after final optimization.
<div align="center">
    <img src="pics/fine_extrinsic.png" width = 100% >
    <font color=#a0a0a0 size=2>The projected image obtained by the extrinsic parameters after fine calibration</font>
</div>

## 4. Run on your own sensor set
### 4.1 Record data
Record the point cloud to pcd files and record image files.

To turn a ROS 2 bag into a pcd file:
```
ros2 launch livox_camera_calib bag_to_pcd.launch.py \
    bag_file:=/path/to/bag_dir lidar_topic:=/livox/lidar \
    pcd_file:=/path/to/0.pcd is_custom_msg:=false
```
Set `is_custom_msg:=true` if the topic carries `livox_ros_driver2/msg/CustomMsg`.
### 4.2 Modify the **calib.yaml**
Change the data path to your local data path.
Provide the instrinsic matrix and distor coeffs for your camera.

Note that **calib.yaml** / **multi_calib.yaml** are ROS 2 parameter files: the
keys live under `<node_name>` -> `ros__parameters`, and the node names are
`lidar_camera_calib` and `lidar_camera_multi_calib`. The scene configs
(**config_outdoor.yaml**, **config_indoor.yaml**) are OpenCV `FileStorage`
files and keep their original format.

### 4.3 Use multi scenes calibration
Change the params in **multi_calib.yaml**, name the image file and pcd file from 0 to (data_num-1).
