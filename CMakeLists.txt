cmake_minimum_required(VERSION 3.8)
project(livox_camera_calib)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(rosbag2_cpp REQUIRED)

find_package(PCL REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Threads REQUIRED)
find_package(Ceres REQUIRED)

# Livox CustomMsg is generated inside this package so that no external
# livox driver package is required to read bags containing it.
rosidl_generate_interfaces(${PROJECT_NAME}
  msg/CustomPoint.msg
  msg/CustomMsg.msg
  DEPENDENCIES std_msgs
)
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} rosidl_typesupport_cpp)

set(dependencies
  rclcpp
  std_msgs
  sensor_msgs
  cv_bridge
  pcl_conversions
  rosbag2_cpp
)

include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${PCL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
  ${EIGEN3_INCLUDE_DIRS}
)
link_directories(${PCL_LIBRARY_DIRS})
add_definitions(${PCL_DEFINITIONS})

foreach(target lidar_camera_calib lidar_camera_multi_calib bag_to_pcd)
  add_executable(${target} src/${target}.cpp)
  ament_target_dependencies(${target} ${dependencies})
  target_link_libraries(${target}
    ${cpp_typesupport_target}
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    ${CERES_LIBRARIES}
    Threads::Threads
  )
endforeach()

install(TARGETS
  lidar_camera_calib
  lidar_camera_multi_calib
  bag_to_pcd
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch config rviz_cfg
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
