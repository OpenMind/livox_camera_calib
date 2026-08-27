#include "livox_camera_calib/msg/custom_msg.hpp"
#include <Eigen/Core>
#include <pcl/io/pcd_io.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl_conversions/pcl_conversions.h>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/serialization.hpp>
#include <rosbag2_cpp/reader.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>

using namespace std;

string bag_file;
string lidar_topic;
string pcd_file;
bool is_custom_msg;

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("bag_to_pcd");
  const auto logger = node->get_logger();

  bag_file = node->declare_parameter<string>("bag_file", "");
  pcd_file = node->declare_parameter<string>("pcd_file", "");
  lidar_topic = node->declare_parameter<string>("lidar_topic", "/livox/lidar");
  is_custom_msg = node->declare_parameter<bool>("is_custom_msg", false);

  if (bag_file.empty() || pcd_file.empty()) {
    RCLCPP_ERROR(logger, "Both 'bag_file' and 'pcd_file' must be set.");
    rclcpp::shutdown();
    return -1;
  }

  pcl::PointCloud<pcl::PointXYZI> output_cloud;

  RCLCPP_INFO(logger, "Loading the rosbag %s", bag_file.c_str());
  rosbag2_cpp::Reader reader;
  try {
    reader.open(bag_file);
  } catch (const std::exception &e) {
    RCLCPP_ERROR_STREAM(logger, "LOADING BAG FAILED: " << e.what());
    rclcpp::shutdown();
    return -1;
  }

  rclcpp::Serialization<livox_camera_calib::msg::CustomMsg> custom_serializer;
  rclcpp::Serialization<sensor_msgs::msg::PointCloud2> cloud_serializer;

  while (reader.has_next()) {
    auto bag_msg = reader.read_next();
    if (bag_msg->topic_name != lidar_topic) {
      continue;
    }
    rclcpp::SerializedMessage serialized(*bag_msg->serialized_data);
    if (is_custom_msg) {
      livox_camera_calib::msg::CustomMsg livox_cloud_msg;
      custom_serializer.deserialize_message(&serialized, &livox_cloud_msg);
      for (uint i = 0; i < livox_cloud_msg.point_num; ++i) {
        pcl::PointXYZI p;
        p.x = livox_cloud_msg.points[i].x;
        p.y = livox_cloud_msg.points[i].y;
        p.z = livox_cloud_msg.points[i].z;
        p.intensity = livox_cloud_msg.points[i].reflectivity;
        output_cloud.points.push_back(p);
      }
    } else {
      sensor_msgs::msg::PointCloud2 livox_cloud;
      cloud_serializer.deserialize_message(&serialized, &livox_cloud);
      pcl::PointCloud<pcl::PointXYZI> cloud;
      pcl::PCLPointCloud2 pcl_pc;
      pcl_conversions::toPCL(livox_cloud, pcl_pc);
      pcl::fromPCLPointCloud2(pcl_pc, cloud);
      for (uint i = 0; i < cloud.size(); ++i) {
        output_cloud.points.push_back(cloud.points[i]);
      }
    }
  }

  if (output_cloud.points.empty()) {
    RCLCPP_ERROR(logger, "No point cloud message found on topic %s",
                 lidar_topic.c_str());
    rclcpp::shutdown();
    return -1;
  }

  output_cloud.is_dense = false;
  output_cloud.width = output_cloud.points.size();
  output_cloud.height = 1;
  pcl::io::savePCDFileASCII(pcd_file, output_cloud);
  RCLCPP_INFO_STREAM(logger,
                     "Sucessfully save point cloud to pcd file: " << pcd_file);
  rclcpp::shutdown();
  return 0;
}
