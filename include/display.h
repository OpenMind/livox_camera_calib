#ifndef LIDAR_CAMERA_DISPLAY_H
#define LIDAR_CAMERA_DISPLAY_H

#include <cstdlib>
#include <opencv2/highgui/highgui.hpp>
#include <string>
#include <unistd.h>

// OpenCV highgui throws when it cannot reach a display server, which kills the
// calibration on a headless robot or over a plain SSH session. Every window
// call goes through these helpers instead: they are no-ops unless a display is
// actually reachable. The `common.enable_gui` parameter can force either way.
namespace display {

inline bool &enabledRef() {
  static bool enabled = std::getenv("DISPLAY") != nullptr ||
                        std::getenv("WAYLAND_DISPLAY") != nullptr;
  return enabled;
}

inline bool enabled() { return enabledRef(); }

inline void setEnabled(bool enable) { enabledRef() = enable; }

inline void imshow(const std::string &name, const cv::Mat &image) {
  if (enabled()) {
    cv::imshow(name, image);
  }
}

inline void waitKey(int delay) {
  if (enabled()) {
    cv::waitKey(delay);
  }
}

// True when a human can actually press enter, i.e. stdin is a terminal.
inline bool interactive() { return isatty(STDIN_FILENO) != 0; }

} // namespace display

#endif // LIDAR_CAMERA_DISPLAY_H
