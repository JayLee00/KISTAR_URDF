"""Render animated GIF + still PNG previews for every MJCF model.

Drives every actuated joint through 60% of its range on a cosine schedule while
orbiting the camera slowly, then writes

    doc/<model>.gif   # looping animation for README
    doc/<model>.png   # single-frame still (quarter-cycle pose)

Run from the repo root:

    python tools/render_previews.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "doc"

# A wrapper MJCF that includes the target model and adds a gradient skybox so
# we don't have to touch the canonical model files.
_WRAPPER_TEMPLATE = """<mujoco model="preview_{name}">
  <include file="{mjcf}"/>
  <asset>
    <texture type="skybox" builtin="gradient"
             rgb1="0.95 0.96 0.98" rgb2="0.65 0.70 0.80"
             width="512" height="512"/>
  </asset>
  <visual>
    <headlight ambient="0.55 0.55 0.55" diffuse="0.70 0.70 0.70" specular="0.10 0.10 0.10"/>
    <quality shadowsize="4096" offsamples="8"/>
    <global elevation="-20" azimuth="90"/>
  </visual>
</mujoco>
"""

MODELS: list[tuple[str, Path]] = [
    ("kistar_hand",      ROOT / "robots/hands/kistar_hand/kistar_hand.xml"),
    ("kistar_son_right", ROOT / "robots/hands/kistar_son/kistar_son_right.xml"),
    ("kistar_son_left",  ROOT / "robots/hands/kistar_son/kistar_son_left.xml"),
]


def _enforce_equality(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    """Directly propagate `<equality joint>` constraints in qpos space.

    For kinematic preview we bypass the solver and evaluate the polynomial
    `slave = c0 + c1*master + c2*master^2 + ...` on every frame.
    """
    for eq_id in range(model.neq):
        if model.eq_type[eq_id] != mujoco.mjtEq.mjEQ_JOINT:
            continue
        j1 = model.eq_obj1id[eq_id]
        j2 = model.eq_obj2id[eq_id]
        adr1 = model.jnt_qposadr[j1]
        adr2 = model.jnt_qposadr[j2]
        c = model.eq_data[eq_id][:5]
        x = data.qpos[adr2]
        data.qpos[adr1] = c[0] + c[1] * x + c[2] * x**2 + c[3] * x**3 + c[4] * x**4


def render_one(
    name: str,
    mjcf_path: Path,
    width: int = 640,
    height: int = 480,
    n_frames: int = 120,
    fps: int = 30,
    sweep_fraction: float = 0.6,
    front_azimuth: float = 90.0,
    neutral: bool = False,
) -> None:
    if not mjcf_path.exists():
        print(f"[{name}] SKIP: {mjcf_path} not found")
        return

    print(f"[{name}] loading {mjcf_path.relative_to(ROOT)}")

    # Write a tiny wrapper next to the original MJCF so that the `<include>`'s
    # relative mesh paths still resolve correctly.
    wrapper_path = mjcf_path.with_name(f"_preview_wrapper_{name}.xml")
    wrapper_path.write_text(
        _WRAPPER_TEMPLATE.format(name=name, mjcf=mjcf_path.name), encoding="utf-8"
    )
    try:
        model = mujoco.MjModel.from_xml_path(str(wrapper_path))
    finally:
        wrapper_path.unlink(missing_ok=True)

    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=height, width=width)

    # Camera looks at the centre of the finger chain, slightly above the palm,
    # with a gentle elevation so both sensors and tips stay in frame.
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.lookat[:] = [-0.012, 0.0, 0.09]
    cam.distance = 0.28
    cam.elevation = -15.0
    cam.azimuth = front_azimuth

    scene_opt = mujoco.MjvOption()
    mujoco.mjv_defaultOption(scene_opt)
    # hide collision-only (group 0) geoms, show visual (group 1) only
    scene_opt.geomgroup[0] = 1

    def _drive_joints(phase: float) -> None:
        """Set every actuator master joint to center + sweep*phase, enforce mimic."""
        signed = 2 * phase - 1  # [-1, 1]
        for aid in range(model.nu):
            jid = model.actuator(aid).trnid[0]
            lo, hi = model.actuator_ctrlrange[aid]
            center = 0.5 * (lo + hi)
            half = 0.5 * sweep_fraction * (hi - lo)
            adr = model.jnt_qposadr[jid]
            data.qpos[adr] = center + half * signed
        _enforce_equality(model, data)
        mujoco.mj_forward(model, data)

    def _reset_joints() -> None:
        """All joint positions = 0 (control = 0 / fully extended pose)."""
        data.qpos[:] = 0.0
        mujoco.mj_forward(model, data)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUT_DIR / f"{name}.png"

    if neutral:
        # Neutral-pose PNG only, at the requested front azimuth.
        _reset_joints()
        cam.azimuth = front_azimuth
        renderer.update_scene(data, camera=cam, scene_option=scene_opt)
        imageio.imwrite(png_path, renderer.render())
        print(f"  -> {png_path.relative_to(ROOT)}  (neutral pose, az={front_azimuth:.0f})")
        return

    # -------- GIF: azimuth oscillates front ± 90 deg (z-axis pan), joints flex --
    # Camera follows a smooth sine wave so it loops perfectly: front -> +90 ->
    # front -> -90 -> front per period. Joints also cycle once per period.
    # If you want the GIF to cover the *opposite* hemisphere from the PNG, pass
    # --front-azimuth 180 (relative to the PNG front).
    frames = []
    for k in range(n_frames):
        phase = 0.5 - 0.5 * np.cos(2 * np.pi * k / n_frames)  # [0, 1]
        _drive_joints(phase)
        cam.azimuth = front_azimuth + 90.0 * np.sin(2 * np.pi * k / n_frames)
        renderer.update_scene(data, camera=cam, scene_option=scene_opt)
        frames.append(renderer.render())

    # -------- PNG: fixed front view, neutral pose (all joints at zero) -------
    # Using the canonical reference pose so the still is reproducible and
    # matches the convention used by dex-urdf / yourdfpy.
    _reset_joints()
    cam.azimuth = front_azimuth
    renderer.update_scene(data, camera=cam, scene_option=scene_opt)
    still_frame = renderer.render()

    gif_path = OUT_DIR / f"{name}.gif"
    imageio.mimsave(gif_path, frames, fps=fps, loop=0)
    imageio.imwrite(png_path, still_frame)

    size_mb = gif_path.stat().st_size / (1024 * 1024)
    print(f"  -> {gif_path.relative_to(ROOT)}  ({len(frames)} frames, {size_mb:.2f} MB)")
    print(f"  -> {png_path.relative_to(ROOT)}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--width",  type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--frames", type=int, default=180,
                   help="number of animation frames (higher = slower + longer GIF)")
    p.add_argument("--fps",    type=int, default=24,
                   help="GIF playback frame rate")
    p.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="subset of model names to render (e.g. --only kistar_hand)",
    )
    p.add_argument(
        "--front-azimuth",
        type=float,
        default=90.0,
        help="camera azimuth (deg) treated as 'front'; PNG still is taken here "
             "and the GIF orbit starts from this angle (default: 90)",
    )
    p.add_argument(
        "--neutral",
        action="store_true",
        help="PNG only, with every joint at qpos=0 (ctrl=0, fully extended pose). "
             "Skips the GIF entirely - useful for quick multi-angle comparison.",
    )
    args = p.parse_args()

    targets = MODELS if args.only is None else [m for m in MODELS if m[0] in args.only]
    for name, path in targets:
        render_one(
            name,
            path,
            width=args.width,
            height=args.height,
            n_frames=args.frames,
            fps=args.fps,
            front_azimuth=args.front_azimuth,
            neutral=args.neutral,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
