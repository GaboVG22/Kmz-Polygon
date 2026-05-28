
import io
import os
import tempfile
import json
import math
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, mapping
from shapely.geometry.polygon import orient
from shapely.ops import transform


@dataclass
class PolygonItem:
    source_file: str
    name: str
    coords_lonlat: List[Tuple[float, float]]
    description: str = ""


@dataclass
class LayerInput:
    source_file: str
    name: str
    cota: float
    polygon_lonlat: Polygon


@dataclass
class LayerComputed:
    source_file: str
    name: str
    cota: float
    polygon_lonlat: Polygon
    polygon_proj: Polygon
    area_m2: float
    area_ha: float
    perimeter_m: float
    centroid_x: float
    centroid_y: float
    kind: str = "base"
    interval_parent: str = ""


def extract_kml_text_from_kmz_bytes(data: bytes) -> str:
    if not data:
        raise ValueError("El archivo está vacío.")
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            kml_names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
            if not kml_names:
                raise ValueError("El KMZ no contiene un archivo KML interno.")
            preferred = [n for n in kml_names if n.lower().endswith("doc.kml")]
            kml_name = preferred[0] if preferred else kml_names[0]
            text = zf.read(kml_name).decode("utf-8", errors="ignore")
            if not text.strip():
                raise ValueError("El KML interno está vacío.")
            return text
    except zipfile.BadZipFile:
        raise ValueError("El archivo no parece ser un KMZ válido.")


def parse_coord_text(coord_text: str) -> List[Tuple[float, float]]:
    coords = []
    for token in str(coord_text).strip().replace("\n", " ").replace("\t", " ").split():
        parts = token.split(",")
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                coords.append((lon, lat))
            except ValueError:
                pass
    return coords


def parse_kmz(uploaded_or_bytes: Union[bytes, object], file_name: str = "archivo.kmz") -> List[PolygonItem]:
    if isinstance(uploaded_or_bytes, bytes):
        data = uploaded_or_bytes
    else:
        data = uploaded_or_bytes.getvalue()
        file_name = getattr(uploaded_or_bytes, "name", file_name)

    kml_text = extract_kml_text_from_kmz_bytes(data)
    root = ET.fromstring(kml_text)
    items: List[PolygonItem] = []

    for pm in root.findall(".//{*}Placemark"):
        name_el = pm.find("{*}name")
        desc_el = pm.find("{*}description")
        base_name = name_el.text.strip() if name_el is not None and name_el.text else "Poligono"
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

        coord_els = pm.findall(".//{*}Polygon/{*}outerBoundaryIs/{*}LinearRing/{*}coordinates")
        for idx, coord_el in enumerate(coord_els, start=1):
            coords = parse_coord_text(coord_el.text or "")
            if len(coords) >= 3:
                label = base_name if len(coord_els) == 1 else f"{base_name}_{idx}"
                items.append(PolygonItem(source_file=file_name, name=label, coords_lonlat=coords, description=desc))

    if not items:
        raise ValueError(f"No se encontraron polígonos válidos en {file_name}. Debe ser un KMZ con Polygon.")
    return items


def close_ring(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if coords and coords[0] != coords[-1]:
        return coords + [coords[0]]
    return coords


def polygon_from_coords(coords_lonlat: List[Tuple[float, float]]) -> Polygon:
    coords = close_ring(coords_lonlat)
    if len(coords) < 4:
        raise ValueError("Un polígono necesita al menos 3 vértices y cierre.")
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        raise ValueError("No fue posible construir un polígono válido.")
    return poly


def utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    zone = int(math.floor((lon + 180.0) / 6.0) + 1)
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def reproject_geom(geom, src_crs: CRS, dst_crs: CRS):
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    return transform(transformer.transform, geom)


def projected_crs_for_inputs(inputs: List[LayerInput]) -> CRS:
    xs, ys = [], []
    for item in inputs:
        c = item.polygon_lonlat.centroid
        xs.append(c.x)
        ys.append(c.y)
    return utm_crs_from_lonlat(sum(xs) / len(xs), sum(ys) / len(ys))


def polygon_proj_to_lonlat(poly_proj: Polygon, proj_crs: CRS) -> Polygon:
    return reproject_geom(poly_proj, proj_crs, CRS.from_epsg(4326))


def build_computed_layers(inputs: List[LayerInput]) -> Tuple[List[LayerComputed], CRS]:
    if len(inputs) < 2:
        raise ValueError("Debe ingresar al menos 2 capas.")
    proj_crs = projected_crs_for_inputs(inputs)
    wgs84 = CRS.from_epsg(4326)
    layers = []
    for item in inputs:
        poly_proj = reproject_geom(item.polygon_lonlat, wgs84, proj_crs)
        if not poly_proj.is_valid:
            poly_proj = poly_proj.buffer(0)
        poly_proj = orient(poly_proj, sign=1.0)
        if poly_proj.area <= 0:
            raise ValueError(f"La capa {item.name} tiene área cero.")
        layers.append(
            LayerComputed(
                source_file=item.source_file,
                name=item.name,
                cota=float(item.cota),
                polygon_lonlat=item.polygon_lonlat,
                polygon_proj=poly_proj,
                area_m2=float(poly_proj.area),
                area_ha=float(poly_proj.area / 10000.0),
                perimeter_m=float(poly_proj.length),
                centroid_x=float(poly_proj.centroid.x),
                centroid_y=float(poly_proj.centroid.y),
                kind="base",
            )
        )
    layers.sort(key=lambda x: (x.cota, x.name))
    return layers, proj_crs


def resample_ring(coords: np.ndarray, n_samples: int) -> np.ndarray:
    coords = np.asarray(coords, dtype=float)
    if np.allclose(coords[0], coords[-1]):
        coords = coords[:-1]
    closed = np.vstack([coords, coords[0]])
    segs = np.diff(closed, axis=0)
    lengths = np.sqrt((segs ** 2).sum(axis=1))
    total = float(lengths.sum())
    if total <= 0:
        raise ValueError("Perímetro inválido.")
    cum = np.insert(np.cumsum(lengths), 0, 0.0)
    stations = np.linspace(0, total, n_samples, endpoint=False)
    out = []
    for s in stations:
        idx = np.searchsorted(cum, s, side="right") - 1
        idx = min(idx, len(lengths) - 1)
        t = 0 if lengths[idx] == 0 else (s - cum[idx]) / lengths[idx]
        out.append(closed[idx] + t * (closed[idx + 1] - closed[idx]))
    return np.asarray(out)


def best_alignment(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    best_score = None
    best = None
    for candidate in (b, b[::-1]):
        for shift in range(len(candidate)):
            shifted = np.roll(candidate, shift, axis=0)
            score = float(np.mean(np.sum((a - shifted) ** 2, axis=1)))
            if best_score is None or score < best_score:
                best_score = score
                best = shifted
    return best


def interpolate_layers(base_layers: List[LayerComputed], proj_crs: CRS, mode: str, n_between: int, delta_cota: Optional[float], n_samples: int) -> List[LayerComputed]:
    result = []
    n_samples = int(max(40, min(n_samples, 240)))

    if mode == "Sin interpolación":
        return result

    for i in range(len(base_layers) - 1):
        lower = base_layers[i]
        upper = base_layers[i + 1]
        h = upper.cota - lower.cota
        if h <= 0:
            continue

        if mode == "n capas por intervalo":
            z_values = [lower.cota + h * j / (n_between + 1) for j in range(1, n_between + 1)]
        elif mode == "delta de cota":
            if not delta_cota or delta_cota <= 0:
                raise ValueError("Debe indicar un delta de cota mayor que cero.")
            z_values = []
            z = lower.cota + delta_cota
            while z < upper.cota:
                z_values.append(z)
                z += delta_cota
        else:
            raise ValueError("Modo de interpolación no reconocido.")

        a = resample_ring(np.array(lower.polygon_proj.exterior.coords), n_samples)
        b = resample_ring(np.array(upper.polygon_proj.exterior.coords), n_samples)
        b = best_alignment(a, b)

        for z in z_values:
            alpha = (z - lower.cota) / h
            pts = (1 - alpha) * a + alpha * b
            pts_closed = np.vstack([pts, pts[0]])
            poly_proj = Polygon(pts_closed)
            if not poly_proj.is_valid:
                poly_proj = poly_proj.buffer(0)
            if poly_proj.is_empty or poly_proj.area <= 0:
                continue
            poly_lonlat = polygon_proj_to_lonlat(poly_proj, proj_crs)
            name = f"Interp_{i+1}_{z:.2f}m"
            result.append(
                LayerComputed(
                    source_file="interpolado",
                    name=name,
                    cota=float(z),
                    polygon_lonlat=poly_lonlat,
                    polygon_proj=poly_proj,
                    area_m2=float(poly_proj.area),
                    area_ha=float(poly_proj.area / 10000.0),
                    perimeter_m=float(poly_proj.length),
                    centroid_x=float(poly_proj.centroid.x),
                    centroid_y=float(poly_proj.centroid.y),
                    kind="interpolada",
                    interval_parent=f"{lower.name} -> {upper.name}",
                )
            )

    result.sort(key=lambda x: (x.cota, x.name))
    return result


def compute_interval_volumes(layers: List[LayerComputed], method: str) -> pd.DataFrame:
    ordered = sorted(layers, key=lambda x: (x.cota, x.kind, x.name))
    rows = []
    cumulative = 0.0
    for i in range(len(ordered) - 1):
        a = ordered[i]
        b = ordered[i + 1]
        h = float(b.cota - a.cota)
        A1 = float(a.area_m2)
        A2 = float(b.area_m2)
        if h < 0:
            raise ValueError("Cotas desordenadas.")
        if method == "Promedio de áreas":
            V = h * (A1 + A2) / 2
        else:
            V = h / 3 * (A1 + A2 + math.sqrt(max(A1, 0) * max(A2, 0)))
        cumulative += V
        rows.append(
            {
                "tramo": i + 1,
                "capa_inferior": a.name,
                "tipo_inferior": a.kind,
                "capa_superior": b.name,
                "tipo_superior": b.kind,
                "cota_inferior_m": a.cota,
                "cota_superior_m": b.cota,
                "delta_h_m": h,
                "area_inferior_m2": A1,
                "area_superior_m2": A2,
                "volumen_intervalo_m3": V,
                "volumen_acumulado_m3": cumulative,
                "metodo": method,
            }
        )
    return pd.DataFrame(rows)


def summarize_layers(layers: List[LayerComputed]) -> pd.DataFrame:
    ordered = sorted(layers, key=lambda x: (x.cota, x.kind, x.name))
    return pd.DataFrame(
        [
            {
                "orden": i + 1,
                "archivo": l.source_file,
                "capa": l.name,
                "tipo": l.kind,
                "cota_m": l.cota,
                "area_m2": l.area_m2,
                "area_ha": l.area_ha,
                "perimetro_m": l.perimeter_m,
                "origen_interpolacion": l.interval_parent,
            }
            for i, l in enumerate(ordered)
        ]
    )


def build_cota_volumen_curve(df_vol: pd.DataFrame, min_cota: float) -> pd.DataFrame:
    rows = [{"cota_m": min_cota, "volumen_acumulado_m3": 0.0}]
    for _, r in df_vol.iterrows():
        rows.append({"cota_m": r["cota_superior_m"], "volumen_acumulado_m3": r["volumen_acumulado_m3"]})
    return pd.DataFrame(rows)


def plot_xy_png(x, y, title, xlabel, ylabel) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, marker="o")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_cota_area_png(df_layers: pd.DataFrame) -> bytes:
    df = df_layers.sort_values("cota_m")
    return plot_xy_png(df["cota_m"], df["area_m2"], "Curva cota-área", "Cota (m)", "Área (m²)")


def build_cota_volumen_png(df_curve: pd.DataFrame) -> bytes:
    return plot_xy_png(df_curve["cota_m"], df_curve["volumen_acumulado_m3"], "Curva cota-volumen", "Cota (m)", "Volumen acumulado (m³)")


def build_3d_preview_png(layers: List[LayerComputed], n_samples: int = 80, vertical_exaggeration: float = 1.0) -> bytes:
    ordered = sorted(layers, key=lambda x: (x.cota, x.kind, x.name))
    if len(ordered) > 80:
        step = max(1, len(ordered) // 80)
        ordered = ordered[::step]
    n_samples = int(max(20, min(n_samples, 100)))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    min_cota = min(l.cota for l in ordered)

    def zplot(z):
        return min_cota + (z - min_cota) * vertical_exaggeration

    for l in ordered:
        xy = np.array(l.polygon_proj.exterior.coords)
        z = zplot(l.cota)
        face = Poly3DCollection([[(x, y, z) for x, y in xy]], alpha=0.20 if l.kind == "base" else 0.09, linewidths=1.0)
        ax.add_collection3d(face)
        ax.plot(xy[:, 0], xy[:, 1], zs=z, linewidth=1.5 if l.kind == "base" else 0.7)
        if l.kind == "base":
            ax.text(l.centroid_x, l.centroid_y, z, f"{l.name}\n{l.cota:.2f} m", fontsize=8)

    for i in range(len(ordered) - 1):
        a_layer = ordered[i]
        b_layer = ordered[i + 1]
        a = resample_ring(np.array(a_layer.polygon_proj.exterior.coords), n_samples)
        b = resample_ring(np.array(b_layer.polygon_proj.exterior.coords), n_samples)
        b = best_alignment(a, b)
        z1 = zplot(a_layer.cota)
        z2 = zplot(b_layer.cota)
        quads = []
        for j in range(n_samples):
            j2 = (j + 1) % n_samples
            quads.append([(a[j, 0], a[j, 1], z1), (a[j2, 0], a[j2, 1], z1), (b[j2, 0], b[j2, 1], z2), (b[j, 0], b[j, 1], z2)])
        ax.add_collection3d(Poly3DCollection(quads, alpha=0.04, linewidths=0.1))

    minx = min(l.polygon_proj.bounds[0] for l in ordered)
    miny = min(l.polygon_proj.bounds[1] for l in ordered)
    maxx = max(l.polygon_proj.bounds[2] for l in ordered)
    maxy = max(l.polygon_proj.bounds[3] for l in ordered)
    minz = min(zplot(l.cota) for l in ordered)
    maxz = max(zplot(l.cota) for l in ordered)
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_zlim(minz, maxz if maxz > minz else minz + 1)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Cota (m)")
    ax.set_title("Vista 3D referencial")
    ax.view_init(elev=24, azim=-55)
    ax.set_box_aspect((max(maxx-minx,1), max(maxy-miny,1), max(maxz-minz,1)))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def kml_escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def coords_to_kml(poly_lonlat: Polygon, cota: float) -> str:
    return " ".join([f"{lon:.10f},{lat:.10f},{cota:.3f}" for lon, lat in poly_lonlat.exterior.coords])


def build_consolidated_kml(layers: List[LayerComputed], df_vol: pd.DataFrame, metadata: Dict) -> bytes:
    placemarks = []
    for l in sorted(layers, key=lambda x: (x.cota, x.kind, x.name)):
        style = "#baseStyle" if l.kind == "base" else "#interpStyle"
        desc = f"Tipo: {l.kind}<br>Cota: {l.cota:.3f} m<br>Área: {l.area_m2:.3f} m²<br>Perímetro: {l.perimeter_m:.3f} m"
        placemarks.append(f"""
<Placemark>
<name>{kml_escape(l.name)}</name>
<description>{desc}</description>
<styleUrl>{style}</styleUrl>
<Polygon>
<altitudeMode>absolute</altitudeMode>
<outerBoundaryIs><LinearRing><coordinates>{coords_to_kml(l.polygon_lonlat, l.cota)}</coordinates></LinearRing></outerBoundaryIs>
</Polygon>
</Placemark>
""")
    total = float(df_vol["volumen_intervalo_m3"].sum()) if not df_vol.empty else 0.0
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Modelo KMZ 3D Volúmenes</name>
<description>Volumen total: {total:.3f} m3 | CRS: {metadata.get('projected_crs','')}</description>
<Style id="baseStyle"><LineStyle><color>ff1f77b4</color><width>3</width></LineStyle><PolyStyle><color>551f77b4</color></PolyStyle></Style>
<Style id="interpStyle"><LineStyle><color>ff0e7fff</color><width>1</width></LineStyle><PolyStyle><color>330e7fff</color></PolyStyle></Style>
{''.join(placemarks)}
</Document>
</kml>
"""
    return kml.encode("utf-8")


def build_kmz(kml_bytes: bytes) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_bytes)
    out.seek(0)
    return out.getvalue()


def build_geojson(layers: List[LayerComputed], metadata: Dict) -> bytes:
    features = []
    for l in layers:
        features.append({
            "type": "Feature",
            "properties": {
                "name": l.name,
                "kind": l.kind,
                "source_file": l.source_file,
                "cota_m": l.cota,
                "area_m2": l.area_m2,
                "area_ha": l.area_ha,
                "perimeter_m": l.perimeter_m,
            },
            "geometry": mapping(l.polygon_lonlat),
        })
    return json.dumps({"type": "FeatureCollection", "metadata": metadata, "features": features}, ensure_ascii=False, indent=2).encode("utf-8")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def consistency_table(base_layers: List[LayerComputed], all_layers: List[LayerComputed]) -> pd.DataFrame:
    rows = []
    rows.append(("OK", f"Capas base cargadas: {len(base_layers)}"))
    rows.append(("OK", f"Capas totales consideradas: {len(all_layers)}"))
    cotas = [l.cota for l in base_layers]
    if len(set(cotas)) < len(cotas):
        rows.append(("ADVERTENCIA", "Existen cotas repetidas; el volumen de esos intervalos será cero."))
    else:
        rows.append(("OK", "Todas las cotas base son únicas."))
    rows.append(("OK", f"Rango de cotas: {min(cotas):.2f} m a {max(cotas):.2f} m"))
    return pd.DataFrame(rows, columns=["Estado", "Resultado"])
