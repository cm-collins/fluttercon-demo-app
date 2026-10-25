#version 460 core

#include <flutter/runtime_effect.glsl>

// Uniform order must match SpeedRampPainter: size (2 floats), then time.
uniform vec2 uSize;
uniform float uTime;

out vec4 fragColor;

vec3 ramp(float t) {
  vec3 slow = vec3(1.0, 0.302, 0.427);
  vec3 mid = vec3(1.0, 0.710, 0.278);
  vec3 fast = vec3(0.310, 0.820, 1.0);
  if (t < 0.45) {
    return mix(slow, mid, t / 0.45);
  }
  return mix(mid, fast, (t - 0.45) / 0.55);
}

void main() {
  vec2 uv = FlutterFragCoord().xy / uSize;
  float shimmer = 0.04 * sin(uTime * 2.0 + uv.x * 12.0);
  float t = clamp(uv.x + shimmer, 0.0, 1.0);
  float glow = 0.35 * exp(-pow((uv.y - 0.5) * 6.0, 2.0));
  fragColor = vec4(ramp(t) + glow, 1.0);
}
