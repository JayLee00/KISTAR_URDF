"""Extract link inertial tables from KISTAR Hand / SON URDF files."""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HAND_URDF = ROOT / "robots/hands/kistar_hand/kistar_hand_right.urdf"
SON_URDF = ROOT / "robots/hands/kistar_son/kistar_son_right_mockup.urdf"

HAND_CANONICAL_ALIAS = {
    "right_hand_base_link": "Palm",
    "right_hand_thumb_base_link": "Thumb_Basemotor",
    "right_hand_thumb_0_link": "Thumb_Link_0",
    "right_hand_thumb_1_link": "Thumb_Link_1",
    "right_hand_thumb_2_link": "Thumb_Link_2",
    "right_hand_thumb_3_link": "Thumb_Tip_Bracket",
    "right_hand_thumb_3_tip_link": "Tip",
    "right_hand_finger_base_link": "Basemotor",
    "right_hand_finger_0_link": "Link_0",
    "right_hand_finger_1_link": "Link_1",
    "right_hand_finger_2_link": "Link_2",
    "right_hand_finger_2_motor_link": "Finger_Motor",
    "right_hand_finger_3_link": "Tip_Bracket",
    "right_hand_finger_3_tip_link": "Tip_Silicone",
}

HAND_ROW_ORDER = list(HAND_CANONICAL_ALIAS.values())


def fvec(text: str) -> list[float]:
    return [float(x) for x in text.split()]


def canonical_hand_link(link_name: str) -> str:
    name = link_name
    for finger in ("index", "middle", "ring"):
        name = name.replace(f"right_hand_{finger}_", "right_hand_finger_")
    return name


def hand_alias(link_name: str) -> str:
    if "pad" in link_name.lower():
        return "Pad (sensor)"
    return HAND_CANONICAL_ALIAS.get(canonical_hand_link(link_name), link_name)


SON_FINGER_PREFIXES = ("index", "middle", "ring")


def canonical_son_link(link_name: str) -> str:
    name = link_name.replace("right_hand_", "")
    for finger in SON_FINGER_PREFIXES:
        if name.startswith(f"{finger}_"):
            return "finger_" + name[len(finger) + 1 :]
    return name


def son_alias(link_name: str) -> str:
    return canonical_son_link(link_name)


def parse_inertial(link: ET.Element) -> dict | None:
    inertial = link.find("inertial")
    if inertial is None:
        return None
    mass_el = inertial.find("mass")
    mass_kg = float(mass_el.get("value", "0")) if mass_el is not None else 0.0
    origin = inertial.find("origin")
    com_m = fvec(origin.get("xyz", "0 0 0")) if origin is not None else [0.0, 0.0, 0.0]
    inertia_el = inertial.find("inertia")
    if inertia_el is None:
        return None
    tensor_kgm2 = {
        "ixx": float(inertia_el.get("ixx", "0")),
        "iyy": float(inertia_el.get("iyy", "0")),
        "izz": float(inertia_el.get("izz", "0")),
        "ixy": float(inertia_el.get("ixy", "0")),
        "ixz": float(inertia_el.get("ixz", "0")),
        "iyz": float(inertia_el.get("iyz", "0")),
    }
    return {"mass_kg": mass_kg, "com_m": com_m, "tensor_kgm2": tensor_kgm2}


def kg_to_g(kg: float) -> float:
    return kg * 1000.0


def kgm2_to_gmm2(v: float) -> float:
    return v * 1e9


def fmt(v: float, decimals: int = 2) -> str:
    if abs(v) < 1e-12:
        return "0"
    return f"{v:.{decimals}f}".rstrip("0").rstrip(".")


def row_from_link(name: str, data: dict, alias_fn) -> dict:
    mass_g = kg_to_g(data["mass_kg"])
    t = data["tensor_kgm2"]
    com_mm = [x * 1000 for x in data["com_m"]]
    return {
        "link": name,
        "alias": alias_fn(name),
        "mass_g": mass_g,
        "com_x_mm": com_mm[0],
        "com_y_mm": com_mm[1],
        "com_z_mm": com_mm[2],
        "ixx": kgm2_to_gmm2(t["ixx"]),
        "iyy": kgm2_to_gmm2(t["iyy"]),
        "izz": kgm2_to_gmm2(t["izz"]),
        "ixy": kgm2_to_gmm2(t["ixy"]),
        "ixz": kgm2_to_gmm2(t["ixz"]),
        "iyz": kgm2_to_gmm2(t["iyz"]),
    }


def extract_hand_rows(urdf_path: Path) -> list[dict]:
    root = ET.parse(urdf_path).getroot()
    by_canonical: dict[str, dict] = {}
    for link in root.findall("link"):
        name = link.get("name", "")
        data = parse_inertial(link)
        if data is None:
            continue
        canon = canonical_hand_link(name)
        if canon not in by_canonical:
            by_canonical[canon] = row_from_link(name, data, hand_alias)
    rows = [by_canonical[k] for k in HAND_CANONICAL_ALIAS if k in by_canonical]
    return [r for r in rows if r["mass_g"] > 0]


def extract_son_rows(urdf_path: Path) -> list[dict]:
    root = ET.parse(urdf_path).getroot()
    by_canonical: dict[str, dict] = {}
    order: list[str] = []
    for link in root.findall("link"):
        name = link.get("name", "")
        data = parse_inertial(link)
        if data is None:
            continue
        row = row_from_link(name, data, son_alias)
        if row["mass_g"] <= 0:
            continue
        canon = canonical_son_link(name)
        if canon not in by_canonical:
            by_canonical[canon] = row
            order.append(canon)
    return [by_canonical[k] for k in order]


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "alias",
        "link",
        "mass_g",
        "com_x_mm",
        "com_y_mm",
        "com_z_mm",
        "ixx_gmm2",
        "iyy_gmm2",
        "izz_gmm2",
        "ixy_gmm2",
        "ixz_gmm2",
        "iyz_gmm2",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for r in rows:
            w.writerow(
                [
                    r["alias"],
                    r["link"],
                    fmt(r["mass_g"], 2),
                    fmt(r["com_x_mm"], 3),
                    fmt(r["com_y_mm"], 3),
                    fmt(r["com_z_mm"], 3),
                    fmt(r["ixx"], 2),
                    fmt(r["iyy"], 2),
                    fmt(r["izz"], 2),
                    fmt(r["ixy"], 2),
                    fmt(r["ixz"], 2),
                    fmt(r["iyz"], 2),
                ]
            )


def write_md(path: Path, title: str, urdf_rel: str, rows: list[dict], note: str) -> None:
    lines = [
        f"# {title}",
        "",
        f"Source: `{urdf_rel}` (link frame, URDF `<inertial>`)",
        "",
        "Units: mass **g**, inertia **g·mm²**, COM **mm**.",
        "",
        note,
        "",
        "| 파트명 | URDF link | mass (g) | COM x | COM y | COM z | ixx | iyy | izz | ixy | ixz | iyz |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['alias']} | `{r['link']}` | {fmt(r['mass_g'], 2)} | "
            f"{fmt(r['com_x_mm'], 3)} | {fmt(r['com_y_mm'], 3)} | {fmt(r['com_z_mm'], 3)} | "
            f"{fmt(r['ixx'], 2)} | {fmt(r['iyy'], 2)} | {fmt(r['izz'], 2)} | "
            f"{fmt(r['ixy'], 2)} | {fmt(r['ixz'], 2)} | {fmt(r['iyz'], 2)} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    hand_rows = extract_hand_rows(HAND_URDF)
    son_rows = extract_son_rows(SON_URDF)

    hand_doc = ROOT / "doc/kistar_hand_inertia.md"
    son_doc = ROOT / "doc/kistar_son_inertia.md"
    hand_csv = ROOT / "doc/kistar_hand_inertia.csv"
    son_csv = ROOT / "doc/kistar_son_inertia.csv"

    write_md(
        hand_doc,
        "KISTAR Hand — Link Inertia",
        "robots/hands/kistar_hand/kistar_hand_right.urdf",
        hand_rows,
        "Index / Middle / Ring finger links share the same mesh & inertia; one row per unique part. "
        "Pad links (mass 0) omitted.",
    )
    write_md(
        son_doc,
        "KISTAR-SON — Link Inertia",
        "robots/hands/kistar_son/kistar_son_right_mockup.urdf",
        son_rows,
        "Only links with **mass > 0** are listed. Index/Middle/Ring duplicates removed; split visual meshes with zero mass omitted.",
    )
    write_csv(hand_csv, hand_rows)
    write_csv(son_csv, son_rows)

    (ROOT / "robots/hands/kistar_hand/INERTIA.md").write_text(
        hand_doc.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (ROOT / "robots/hands/kistar_son/INERTIA.md").write_text(
        son_doc.read_text(encoding="utf-8"), encoding="utf-8"
    )

    print(f"Wrote {hand_doc}")
    print(f"Wrote {son_doc}")
    print(f"Hand parts: {len(hand_rows)}, SON parts: {len(son_rows)}")


if __name__ == "__main__":
    main()
