"""Convert KISTAR Hand URDF to MuJoCo MJCF (kistar_son-style)."""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

MESHDIR = "01_kistar_hand_stl/"


def fvec(text: str) -> list[float]:
    return [float(x) for x in text.split()]


def fmt(v: float) -> str:
    if v == 0.0:
        return "0"
    s = f"{v:.8g}"
    return "0" if s == "-0" else s


def fmt_vec(v: list[float]) -> str:
    return " ".join(fmt(x) for x in v)


def mesh_basename(path: str) -> str:
    return Path(path.replace("\\", "/")).name


def mesh_asset_name(mesh_file: str) -> str:
    return Path(mesh_file).stem


def indent(level: int) -> str:
    return "  " * level


def parse_links(root: ET.Element) -> dict[str, dict]:
    links: dict[str, dict] = {}
    for link in root.findall("link"):
        name = link.get("name", "")
        visual = link.find("visual")
        rgba = "0.2 0.2 0.2 1"
        mesh_file = None
        if visual is not None:
            mesh_el = visual.find("geometry/mesh")
            if mesh_el is not None:
                mesh_file = mesh_basename(mesh_el.get("filename", ""))
            mat = visual.find("material/color")
            if mat is not None:
                rgba = mat.get("rgba", rgba)
        collision = link.find("collision/geometry/mesh")
        if mesh_file is None and collision is not None:
            mesh_file = mesh_basename(collision.get("filename", ""))

        inertial = link.find("inertial")
        mass = 0.0
        i_pos = [0.0, 0.0, 0.0]
        inertia = [0.0] * 6
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass = float(mass_el.get("value", "0"))
            origin = inertial.find("origin")
            if origin is not None:
                i_pos = fvec(origin.get("xyz", "0 0 0"))
            inertia_el = inertial.find("inertia")
            if inertia_el is not None:
                inertia = [
                    float(inertia_el.get("ixx", "0")),
                    float(inertia_el.get("iyy", "0")),
                    float(inertia_el.get("izz", "0")),
                    float(inertia_el.get("ixy", "0")),
                    float(inertia_el.get("ixz", "0")),
                    float(inertia_el.get("iyz", "0")),
                ]
        links[name] = {
            "mesh_file": mesh_file,
            "rgba": rgba,
            "mass": mass,
            "i_pos": i_pos,
            "inertia": inertia,
        }
    return links


def parse_joints(root: ET.Element) -> tuple[dict[str, list[dict]], str]:
    children: dict[str, list[dict]] = {}
    child_links: set[str] = set()
    for joint in root.findall("joint"):
        j = {
            "name": joint.get("name", ""),
            "type": joint.get("type", "fixed"),
            "parent": joint.find("parent").get("link", ""),
            "child": joint.find("child").get("link", ""),
            "xyz": fvec(joint.find("origin").get("xyz", "0 0 0")),
            "rpy": fvec(joint.find("origin").get("rpy", "0 0 0")),
            "axis": fvec(joint.find("axis").get("xyz", "0 0 1"))
            if joint.find("axis") is not None
            else None,
            "lower": float(joint.find("limit").get("lower", "0"))
            if joint.find("limit") is not None
            else None,
            "upper": float(joint.find("limit").get("upper", "0"))
            if joint.find("limit") is not None
            else None,
            "damping": float(joint.find("dynamics").get("damping", "0"))
            if joint.find("dynamics") is not None
            else 0.0,
            "friction": float(joint.find("dynamics").get("friction", "0"))
            if joint.find("dynamics") is not None
            else 0.0,
        }
        child_links.add(j["child"])
        children.setdefault(j["parent"], []).append(j)

    all_links = {link.get("name") for link in root.findall("link")}
    roots = sorted(all_links - child_links)
    if len(roots) != 1:
        raise RuntimeError(f"Expected one root link, found {roots}")
    return children, roots[0]


def emit_inertial(link: dict, level: int) -> list[str]:
    ixx, iyy, izz, ixy, ixz, iyz = link["inertia"]
    return [
        f'{indent(level)}<inertial pos="{fmt_vec(link["i_pos"])}" mass="{fmt(link["mass"])}" '
        f'fullinertia="{fmt(ixx)} {fmt(iyy)} {fmt(izz)} {fmt(ixy)} {fmt(ixz)} {fmt(iyz)}"/>'
    ]


def emit_geoms(mesh_name: str, rgba: str, level: int) -> list[str]:
    return [
        f'{indent(level)}<geom type="mesh" mesh="{mesh_name}"/>',
        f'{indent(level)}<geom type="mesh" contype="0" conaffinity="0" group="1" '
        f'density="0" rgba="{rgba}" mesh="{mesh_name}"/>',
    ]


def emit_link_content(link: dict, level: int) -> list[str]:
    lines: list[str] = []
    if link["mesh_file"]:
        mname = mesh_asset_name(link["mesh_file"])
        if link["mass"] > 0:
            lines.extend(emit_inertial(link, level))
        lines.extend(emit_geoms(mname, link["rgba"], level))
    elif link["mass"] > 0:
        lines.extend(emit_inertial(link, level))
    return lines


def emit_children(parent: str, links: dict, children: dict, level: int) -> list[str]:
    lines: list[str] = []
    for joint in children.get(parent, []):
        child_name = joint["child"]
        child = links[child_name]
        pos = fmt_vec(joint["xyz"])
        rpy = fmt_vec(joint["rpy"])
        lines.append(f'{indent(level)}<body name="{child_name}" pos="{pos}" euler="{rpy}">')
        if joint["type"] == "revolute":
            axis = fmt_vec(joint["axis"])
            lines.append(
                f'{indent(level + 1)}<joint name="{joint["name"]}" pos="0 0 0" axis="{axis}" '
                f'range="{fmt(joint["lower"])} {fmt(joint["upper"])}" '
                f'actuatorfrcrange="-0.2 0.2" damping="{fmt(joint["damping"])}" '
                f'frictionloss="{fmt(joint["friction"])}"/>'
            )
        elif joint["type"] != "fixed":
            raise ValueError(f"Unsupported joint type {joint['type']}")
        lines.extend(emit_link_content(child, level + 1))
        lines.extend(emit_children(child_name, links, children, level + 1))
        lines.append(f"{indent(level)}</body>")
    return lines


def convert(urdf_path: Path, out_path: Path) -> None:
    root = ET.parse(urdf_path).getroot()
    model_name = root.get("name", "kistar_hand").upper()
    links = parse_links(root)
    children, root_link = parse_joints(root)

    mesh_files = sorted({link["mesh_file"] for link in links.values() if link["mesh_file"]})

    lines = [
        f"<mujoco model=\"{model_name}\">",
        f'  <compiler angle="radian" meshdir="{MESHDIR}" boundmass="0.0001" boundinertia="1e-09"/>',
        "",
        '  <option timestep="0.0005" integrator="implicitfast" solver="Newton" iterations="100" tolerance="1e-10">',
        "    <flag contact=\"disable\"/>",
        "  </option>",
        "",
        "  <asset>",
    ]
    for mf in mesh_files:
        lines.append(
            f'    <mesh name="{mesh_asset_name(mf)}" content_type="model/stl" file="{mf}"/>'
        )
    lines += ["  </asset>", "", "  <worldbody>", f'    <body name="{root_link}">']
    lines.extend(emit_link_content(links[root_link], 3))
    lines.extend(emit_children(root_link, links, children, 3))
    lines += ["    </body>", "  </worldbody>", "", "  <default>", '    <position kp="30" kv="0.7" forcerange="-100 100"/>', "  </default>", "", "  <actuator>"]

    for joint in root.findall("joint"):
        if joint.get("type") != "revolute":
            continue
        jname = joint.get("name", "")
        lo = joint.find("limit").get("lower")
        hi = joint.find("limit").get("upper")
        lines.append(
            f'    <position name="{jname.replace("_joint", "_act")}" joint="{jname}" ctrlrange="{lo} {hi}"/>'
        )

    lines += ["  </actuator>", "</mujoco>", ""]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("urdf")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    convert(Path(args.urdf), Path(args.output))


if __name__ == "__main__":
    main()
