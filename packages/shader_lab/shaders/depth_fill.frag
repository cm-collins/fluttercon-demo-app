#version 460 core

#include <flutter/runtime_effect.glsl>

// Uniform order must match DepthChart: size (2 floats), then 1 for bids and 0 for asks.
uniform vec2 uSize;
uniform float uBid;

out vec4 fragColor;

void main() {
  vec2 uv = FlutterFragCoord().xy / uSize;
  float along = mix(uv.x, 1.0 - uv.x, uBid);
  vec3 bid = vec3(0.239, 0.863, 0.592);
  vec3 ask = vec3(1.000, 0.302, 0.427);
  vec3 color = mix(ask, bid, clamp(uBid, 0.0, 1.0));
  fragColor = vec4(color * (0.35 + 0.65 * along), 1.0);
}
