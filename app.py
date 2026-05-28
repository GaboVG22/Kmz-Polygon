
from pathlib import Path

import pandas as pd
import streamlit as st

from core import (
    LayerInput,
    build_3d_preview_png,
    build_computed_layers,
    build_consolidated_kml,
    build_cota_area_png,
    build_cota_volumen_curve,
    build_cota_volumen_png,
    build_geojson,
    build_kmz,
    compute_interval_volumes,
    consistency_table,
    interpolate_layers,
    parse_kmz,
    polygon_from_coords,
    summarize_layers,
    to_csv_bytes,
)

st.set_page_config(page_title="KMZ 3D Volúmenes V5", page_icon="🗺️", layout="wide")

st.title("🗺️ KMZ 3D, cotas y cálculo de volúmenes")
st.markdown(
    """
Carga **2 o más KMZ**, asigna una **cota** a cada capa, genera una **vista 3D**,
calcula **volúmenes entre capas** y exporta resultados.
"""
)

with st.sidebar:
    st.header("1. Archivos")
    usar_ejemplos = st.checkbox("Usar KMZ de ejemplo incluidos", value=False)
    uploaded_files = st.file_uploader("Cargue 2 o más KMZ", type=["kmz"], accept_multiple_files=True)

    st.header("2. Volumen")
    volume_method = st.selectbox("Método de volumen", ["Prismoidal", "Promedio de áreas"])

    st.header("3. Interpolación opcional")
    interp_mode = st.selectbox("Modo", ["Sin interpolación", "n capas por intervalo", "delta de cota"])
    n_between = 0
    delta_cota = None
    if interp_mode == "n capas por intervalo":
        n_between = st.number_input("Capas intermedias por intervalo", min_value=1, max_value=25, value=2, step=1)
    if interp_mode == "delta de cota":
        delta_cota = st.number_input("Delta de cota (m)", min_value=0.01, value=5.0, step=1.0, format="%.2f")

    interp_samples = st.slider("Puntos de interpolación", min_value=40, max_value=240, value=120, step=20)

    st.header("4. Vista 3D")
    vertical_exaggeration = st.slider("Exageración vertical", min_value=0.2, max_value=8.0, value=1.0, step=0.2)

    st.header("5. Salida")
    out_basename = st.text_input("Nombre base", value="modelo_kmz_volumenes")

class LocalUpload:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name

    def getvalue(self):
        return self.path.read_bytes()

if usar_ejemplos:
    sample_dir = Path(__file__).parent / "sample_data"
    uploaded_files = [
        LocalUpload(sample_dir / "capa_100m.kmz"),
        LocalUpload(sample_dir / "capa_110m.kmz"),
        LocalUpload(sample_dir / "capa_125m.kmz"),
    ]

if not uploaded_files or len(uploaded_files) < 2:
    st.info("Cargue al menos 2 archivos KMZ o active 'Usar KMZ de ejemplo incluidos'.")
    st.stop()

parsed = []
for f in uploaded_files:
    try:
        parsed.append((f.name, parse_kmz(f)))
    except Exception as e:
        st.error(f"Error leyendo {getattr(f, 'name', 'archivo')}: {e}")
        st.stop()

st.subheader("Configuración de capas")
st.caption("Seleccione un polígono por archivo e ingrese su cota.")

layer_inputs = []
cols = st.columns(2)
for idx, (file_name, items) in enumerate(parsed):
    with cols[idx % 2]:
        with st.expander(f"{idx + 1}. {file_name}", expanded=True):
            selected_idx = st.selectbox(
                f"Polígono de {file_name}",
                options=list(range(len(items))),
                format_func=lambda i, items=items: items[i].name,
                key=f"poly_{idx}",
            )
            cota = st.number_input(
                f"Cota de {file_name} (m)",
                value=float(100 + idx * 10),
                step=1.0,
                format="%.2f",
                key=f"cota_{idx}",
            )
            item = items[selected_idx]
            layer_inputs.append(
                LayerInput(
                    source_file=file_name,
                    name=item.name,
                    cota=float(cota),
                    polygon_lonlat=polygon_from_coords(item.coords_lonlat),
                )
            )

if st.button("Generar modelo", type="primary", use_container_width=True):
    try:
        base_layers, proj_crs = build_computed_layers(layer_inputs)

        interpolated = interpolate_layers(
            base_layers=base_layers,
            proj_crs=proj_crs,
            mode=interp_mode,
            n_between=int(n_between),
            delta_cota=delta_cota,
            n_samples=int(interp_samples),
        )

        if len(interpolated) > 250:
            st.error("La interpolación genera demasiadas capas. Reduzca n o aumente delta de cota.")
            st.stop()

        all_layers = sorted(base_layers + interpolated, key=lambda x: (x.cota, x.kind, x.name))
        df_layers = summarize_layers(all_layers)
        df_vol = compute_interval_volumes(all_layers, volume_method)
        df_curve = build_cota_volumen_curve(df_vol, min(l.cota for l in all_layers))

        metadata = {
            "projected_crs": proj_crs.to_string(),
            "volume_method": volume_method,
            "interpolation_mode": interp_mode,
        }

        png_3d = build_3d_preview_png(all_layers, vertical_exaggeration=float(vertical_exaggeration))
        png_area = build_cota_area_png(df_layers)
        png_volume = build_cota_volumen_png(df_curve)
        kml = build_consolidated_kml(all_layers, df_vol, metadata)
        kmz = build_kmz(kml)
        geojson = build_geojson(all_layers, metadata)

        total_volume = float(df_vol["volumen_intervalo_m3"].sum()) if not df_vol.empty else 0.0

        st.subheader("Control de consistencia")
        st.dataframe(consistency_table(base_layers, all_layers), hide_index=True, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Capas base", len(base_layers))
        c2.metric("Capas interpoladas", len(interpolated))
        c3.metric("Volumen total", f"{total_volume:,.2f} m³")
        c4.metric("CRS", proj_crs.to_string())

        st.subheader("Vista 3D")
        st.image(png_3d, caption="Vista 3D referencial.", use_container_width=True)

        tab1, tab2, tab3, tab4 = st.tabs(["Capas", "Volúmenes", "Cota-área", "Cota-volumen"])

        with tab1:
            st.dataframe(df_layers, hide_index=True, use_container_width=True)
        with tab2:
            st.dataframe(df_vol, hide_index=True, use_container_width=True)
        with tab3:
            st.image(png_area, use_container_width=True)
        with tab4:
            st.image(png_volume, use_container_width=True)
            st.dataframe(df_curve, hide_index=True, use_container_width=True)

        st.subheader("Descargas")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("KMZ consolidado", kmz, f"{out_basename}.kmz", "application/vnd.google-earth.kmz", use_container_width=True)
            st.download_button("KML consolidado", kml, f"{out_basename}.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)
        with d2:
            st.download_button("GeoJSON", geojson, f"{out_basename}.geojson", "application/geo+json", use_container_width=True)
            st.download_button("CSV capas", to_csv_bytes(df_layers), f"{out_basename}_capas.csv", "text/csv", use_container_width=True)
        with d3:
            st.download_button("CSV volúmenes", to_csv_bytes(df_vol), f"{out_basename}_volumenes.csv", "text/csv", use_container_width=True)
            st.download_button("CSV cota-volumen", to_csv_bytes(df_curve), f"{out_basename}_cota_volumen.csv", "text/csv", use_container_width=True)
        with d4:
            st.download_button("PNG 3D", png_3d, f"{out_basename}_3d.png", "image/png", use_container_width=True)
            st.download_button("PNG cota-volumen", png_volume, f"{out_basename}_cota_volumen.png", "image/png", use_container_width=True)

    except Exception as e:
        st.error(f"Error al generar el modelo: {e}")
