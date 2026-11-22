#!/usr/bin/env bash
# Native Linux X11/Xwayland. No xhost + and no --privileged required.
set -euo pipefail
: "${DISPLAY:?No DISPLAY. Use a local X11/Xwayland desktop or the headless command in README.}"
command -v xauth || { printf '%s\n' 'Install xauth first.'; exit 1; }
XAUTH=$(mktemp /tmp/ros2-arm-xauth.XXXXXX)
chmod 600 "$XAUTH"
trap 'rm -f "$XAUTH"' EXIT
# Copy only this display's authorization into an ephemeral file.
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH" nmerge -
if ! xauth -f "$XAUTH" list | grep -q .; then
  printf '%s\n' 'No X11 authorization found for DISPLAY. Use the headless option or configure Xwayland/Xauthority.'
  exit 1
fi
sudo docker run --rm --init --name ros2-arm --network host \
  -e DISPLAY -e QT_X11_NO_MITSHM=1 -e LIBGL_ALWAYS_SOFTWARE=1 \
  -e XAUTHORITY=/tmp/.docker.xauth \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "$XAUTH":/tmp/.docker.xauth:ro \
  ros2-arm:jazzy ros2 launch arm_simulation simulation.launch.py "$@"
