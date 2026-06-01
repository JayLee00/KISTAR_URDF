# KISTAR Hand (Ver2)

4-finger anthropomorphic hand (left + right) developed at
[Korea Institute of Science and Technology](https://www.kist.re.kr).

| Field            | Value                                                       |
| ---------------- | ----------------------------------------------------------- |
| Author           | Jaesung Lee                                                 |
| Affiliation      | Korea Institute of Science and Technology                   |
| License          | BSD-3-Clause                                                |
| Last update      | 2026-06-01                                                  |
| Right URDF       | [`kistar_hand_right.urdf`](kistar_hand_right.urdf)          |
| Left URDF        | [`kistar_hand_left.urdf`](kistar_hand_left.urdf)            |
| Right MJCF       | [`kistar_hand_right.xml`](kistar_hand_right.xml)            |
| Left MJCF        | [`kistar_hand_left.xml`](kistar_hand_left.xml)              |
| Mesh format      | binary STL (`01_kistar_hand_stl/`)                          |

---

## Files

```
kistar_hand/
├── kistar_hand_right.urdf         # right URDF (Gazebo / RViz / Isaac Sim / SAPIEN)
├── kistar_hand_left.urdf          # left URDF
├── kistar_hand_right.xml          # MuJoCo MJCF, recommended for sim
├── kistar_hand_left.xml
├── README.md
└── 01_kistar_hand_stl/            # all binary STL meshes (left + right + shared)
```

---

## Model Spec

| Item              | Value                                                                |
| ----------------- | -------------------------------------------------------------------- |
| Fingers           | 4 (thumb, index, middle, ring)                                     |
| Joints / hand     | 16 hinge                                                             |
| Actuators / hand  | 16 position actuators (all revolute joints independent)            |
| Mimic / Coupling  | none                                                                 |
| PD gains (MJCF)   | `kp=30`, `kv=0.7`, force range ± 100 N·m                             |
| Contact           | disabled (kinematic preview by default)                              |

---

## How to run in MuJoCo

```bash
pip install mujoco
python -m mujoco.viewer --mjcf=robots/hands/kistar_hand/kistar_hand_right.xml
python -m mujoco.viewer --mjcf=robots/hands/kistar_hand/kistar_hand_left.xml
```

Drive joints by moving the **Control** sliders in the left panel.

---

## How to run in any URDF parser

```python
import yourdfpy
robot = yourdfpy.URDF.load("robots/hands/kistar_hand/kistar_hand_right.urdf")
robot.show()
```

Compatible with: yourdfpy, RViz, Gazebo, IsaacGym, IsaacSim, SAPIEN, PyBullet.

---

## License

BSD-3-Clause © 2026 Korea Institute of Science and Technology.
Author: **Jaesung Lee** &lt;jay.lee@kist.re.kr&gt;.
