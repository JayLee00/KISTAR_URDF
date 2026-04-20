# KISTAR-SON

5-finger anthropomorphic hand (left + right) developed at
[Korea Institute of Science and Technology](https://www.kist.re.kr).

| Field            | Value                                                       |
| ---------------- | ----------------------------------------------------------- |
| Author           | Jaesung Lee                                                 |
| Affiliation      | Korea Institute of Science and Technology                   |
| License          | BSD-3-Clause                                                |
| Last update      | 2026-04-19                                                  |
| Right URDF       | [`kistar_son_right_mockup.urdf`](kistar_son_right_mockup.urdf) |
| Left URDF        | [`kistar_son_left_mockup.urdf`](kistar_son_left_mockup.urdf)   |
| Right MJCF       | [`kistar_son_right.xml`](kistar_son_right.xml)              |
| Left MJCF        | [`kistar_son_left.xml`](kistar_son_left.xml)                |
| Mesh format      | binary STL (`01_kistar_son_STL/`)                           |

---

## Files

```
kistar_son/
├── kistar_son_right_mockup.urdf   # right URDF (Gazebo / RViz / Isaac Sim / SAPIEN)
├── kistar_son_left_mockup.urdf    # left URDF
├── kistar_son_right.xml           # MuJoCo MJCF, recommended for sim
├── kistar_son_left.xml
├── README.md
└── 01_kistar_son_STL/             # all binary STL meshes (left + right)
```

---

## Model Spec

| Item              | Value                                                                |
| ----------------- | -------------------------------------------------------------------- |
| Fingers           | 5 (thumb, index, middle, ring, little)                               |
| Joints / hand     | 20 hinge                                                             |
| Actuators / hand  | 15 position actuators                                                |
| Mimic / Coupling  | `*_3_joint` ↔ `*_2_joint` (index, middle, ring), `thumb_4` ↔ `thumb_3`, `little_2` ↔ `little_1` (5 equality constraints) |
| PD gains (MJCF)   | `kp=30`, `kv=0.7`, force range ± 100 N·m                             |
| Contact           | disabled (kinematic preview by default)                              |

---

## How to run

```bash
pip install mujoco
python -m mujoco.viewer --mjcf=robots/hands/kistar_son/kistar_son_right.xml
# or
python -m mujoco.viewer --mjcf=robots/hands/kistar_son/kistar_son_left.xml
```

In the viewer:

- **Control** sliders — 15 master joints
- **Mouse left-drag** — orbit
- **Mouse right-drag** — pan
- **Mouse wheel** — zoom
- **Space** — pause / resume
- **Backspace** — reset all joints to 0

---

## Portability

All paths in the URDF/XML files are **relative to this folder**. Keep
`01_kistar_son_STL/`, the URDFs, and the XMLs in the same directory.

Do **not** rename any STL or `01_kistar_son_STL/` folder.

---

## License

BSD-3-Clause © 2026 Korea Institute of Science and Technology.
Author: **Jaesung Lee** &lt;jay.lee@kist.re.kr&gt;.
