#ifndef LIDAR_CAMERA_CV_BRIDGE_COMPAT_H
#define LIDAR_CAMERA_CV_BRIDGE_COMPAT_H
// cv_bridge shipped a C++ header rename: <cv_bridge/cv_bridge.h> was replaced
// by <cv_bridge/cv_bridge.hpp> (Iron onwards; the old header is gone in Jazzy).
#if __has_include(<cv_bridge/cv_bridge.hpp>)
#include <cv_bridge/cv_bridge.hpp>
#else
#include <cv_bridge/cv_bridge.h>
#endif
#endif // LIDAR_CAMERA_CV_BRIDGE_COMPAT_H
