import os

import plotly.graph_objects as go
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
# BACKEND_URL debe ser SOLO el dominio. Si en Railway se puso la ruta completa,
# aquí se le quita para evitar que se duplique (/api/v1/.../api/v1/...).
BACKEND_URL = (
    os.getenv("BACKEND_URL", "https://esoplanet01-production-c23ba379.up.railway.app")
    .rstrip("/")
    .removesuffix("/api/v1/exoplanets/classify")
)
CLASSIFY_URL = f"{BACKEND_URL}/api/v1/exoplanets/classify"

st.set_page_config(page_title="Clasificador de Exoplanetas", layout="wide")

# Claves de los widgets (se usan para limpiar el formulario)
KEYS_FLAGS = ["flag_nt", "flag_ss", "flag_co", "flag_ec"]
KEYS_NUM = [
    "input_period", "input_ruido", "input_time0bk", "input_duration",
    "input_time01", "input_time02", "input_duration01", "input_duration02",
    "input_prad", "input_teq", "input_depth", "input_insol", "input_impact",
    "input_plnt_num", "input_steff", "input_slogg",
    "input_impact01", "input_impact02", "input_depth01", "input_depth02",
    "input_prad02", "input_insol02", "input_steff01", "input_slogg02",
    "input_srad01", "input_ra", "input_dec", "input_kepmag",
]

# Estado de sesión
if "probabilidad_exoplaneta" not in st.session_state:
    st.session_state.probabilidad_exoplaneta = 0.0
if "veredicto_ia" not in st.session_state:
    st.session_state.veredicto_ia = "PENDIENTE DE ANÁLISIS"
if "aviso" not in st.session_state:
    st.session_state.aviso = ""


def limpiar_interfaz():
    """Callback del botón: reinicia resultado y todos los campos."""
    st.session_state.probabilidad_exoplaneta = 0.0
    st.session_state.veredicto_ia = "PENDIENTE DE ANÁLISIS"
    st.session_state.aviso = ""
    for k in KEYS_NUM:
        st.session_state[k] = None
    for k in KEYS_FLAGS:
        st.session_state[k] = False


def num(col, label, key, placeholder, fmt=None, step=None):
    """number_input vacío por defecto (value=None)."""
    kwargs = {"value": None, "placeholder": placeholder, "key": key}
    if fmt:
        kwargs["format"] = fmt
    if step:
        kwargs["step"] = step
    return col.number_input(label, **kwargs)


# ---------------------------------------------------------------------------
# ESTILO
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3, span, label, p { color: white !important; }
    .stButton>button {
        background-color: #00acee;
        color: white;
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3em;
    }
    .stButton>button:hover { background-color: #0084b4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🪐 Clasificador de Exoplanetas Kepler")

col1, col2 = st.columns([1, 1.4], gap="large")

# ---------------------------------------------------------------------------
# COLUMNA 1: MEDIDOR
# ---------------------------------------------------------------------------
with col1:
    st.subheader("Resultado de Clasificación")

    prob_porcentaje = st.session_state.probabilidad_exoplaneta
    veredicto = st.session_state.veredicto_ia

    if veredicto == "CONFIRMADO":
        color_estado = "#22c55e"
    elif veredicto == "CANDIDATO":
        color_estado = "#00acee"
    elif veredicto == "FALSO POSITIVO":
        color_estado = "#ef4444"
    else:
        color_estado = "#94a3b8"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob_porcentaje,
        number={"suffix": "%", "font": {"color": "white"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "white"},
            "bar": {"color": "#B19CD9"},
            "bgcolor": "#1e293b",
            "steps": [
                {"range": [0, 50], "color": "#f08282"},
                {"range": [50, 75], "color": "#59bde5"},
                {"range": [75, 100], "color": "#8ad4a5"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )

    st.plotly_chart(fig, width="stretch")
    st.markdown(
        f"<center><h3>Estado: <span style='color:{color_estado};'>{veredicto}</span></h3></center>",
        unsafe_allow_html=True,
    )
    st.info("Nota: Este valor representa la probabilidad de que el objeto sea un Exoplaneta.")
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Volver a Clasificar 💫", use_container_width=True, on_click=limpiar_interfaz)

# ---------------------------------------------------------------------------
# COLUMNA 2: FORMULARIO
# ---------------------------------------------------------------------------
with col2:
    st.subheader("Datos Técnicos")
    st.write("Completa los parámetros requeridos para la clasificación")

    with st.form("entity_inputs"):
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Banderas (Flags)", "Datos de Tránsito", "Datos Estelares", "Coordenadas"]
        )

        # ---------------- TAB 1: FLAGS ----------------
        with tab1:
            st.caption("Falsos Positivos Potenciales")
            c1, c2 = st.columns(2)
            koi_fpflag_nt = c1.toggle("Flag No Transit-Like (nt)", value=False, key="flag_nt")
            koi_fpflag_ss = c2.toggle("Flag Stellar Co-Passenger (ss)", value=False, key="flag_ss")

            c3, c4 = st.columns(2)
            koi_fpflag_co = c3.toggle("Flag Centroid Offset (co)", value=False, key="flag_co")
            koi_fpflag_ec = c4.toggle("Flag Ephemeris Match (ec)", value=False, key="flag_ec")

        # ---------------- TAB 2: TRÁNSITO ----------------
        with tab2:
            st.caption("Parámetros de la curva de luz y tránsitos")
            t_c1, t_c2 = st.columns(2)
            koi_period = num(t_c1, "Período Orbital (koi_period)", "input_period", "Ej: 51.07926", "%.6f")
            koi_model_snr = num(t_c2, "Relación Señal/Ruido (koi_model_snr)", "input_ruido", "Ej: 126.8", "%.2f")

            t_c3, t_c4 = st.columns(2)
            koi_time0bk = num(t_c3, "Época de Tránsito (koi_time0bk)", "input_time0bk", "Ej: 185.18087", "%.6f")
            koi_duration = num(t_c4, "Duración Tránsito (koi_duration)", "input_duration", "Ej: 6.3729", "%.5f")

            with st.expander("Ver Errores de Medición de Tránsito"):
                e1, e2 = st.columns(2)
                koi_time0bk_err1 = num(e1, "koi_time0bk_err1", "input_time01", "Ej: 0.000981", "%.7f")
                koi_time0bk_err2 = num(e2, "koi_time0bk_err2", "input_time02", "Ej: -0.000981", "%.7f")

                e3, e4 = st.columns(2)
                koi_duration_err1 = num(e3, "koi_duration_err1", "input_duration01", "Ej: 0.0312", "%.5f")
                koi_duration_err2 = num(e4, "koi_duration_err2", "input_duration02", "Ej: -0.0312", "%.5f")

        # ---------------- TAB 3: FÍSICA ----------------
        with tab3:
            st.caption("Física del Planeta Candidato y su Estrella")
            p_c1, p_c2 = st.columns(2)
            koi_prad = num(p_c1, "Radio Planetario (koi_prad)", "input_prad", "Ej: 2.75", "%.2f")
            koi_teq = num(p_c2, "Temp. Equilibrio (koi_teq)", "input_teq", "Ej: 503", step=1)

            p_c3, p_c4 = st.columns(2)
            koi_depth = num(p_c3, "Profundidad de Tránsito (koi_depth)", "input_depth", "Ej: 736.8", "%.1f")
            koi_insol = num(p_c4, "Insolación (koi_insol)", "input_insol", "Ej: 15.17", "%.2f")

            p_c5, p_c6 = st.columns(2)
            koi_impact = num(p_c5, "Parámetro de Impacto (koi_impact)", "input_impact", "Ej: 0.017", "%.3f")
            koi_tce_plnt_num = num(p_c6, "Número TCE Planet (koi_tce_plnt_num)", "input_plnt_num", "Ej: 1", step=1)

            p_c7, p_c8 = st.columns(2)
            koi_steff = num(p_c7, "Temp. Efectiva Estelar (koi_steff)", "input_steff", "Ej: 5833", step=1)
            koi_slogg = num(p_c8, "Gravedad Estelar (koi_slogg)", "input_slogg", "Ej: 4.407", "%.3f")

            with st.expander("Ver Errores de Medición Física"):
                ex1, ex2 = st.columns(2)
                koi_impact_err1 = num(ex1, "koi_impact_err1", "input_impact01", "Ej: 0.267", "%.3f")
                koi_impact_err2 = num(ex2, "koi_impact_err2", "input_impact02", "Ej: -0.017", "%.3f")

                ex3, ex4 = st.columns(2)
                koi_depth_err1 = num(ex3, "koi_depth_err1", "input_depth01", "Ej: 6", "%.1f")
                koi_depth_err2 = num(ex4, "koi_depth_err2", "input_depth02", "Ej: -6", "%.1f")

                ex5, ex6 = st.columns(2)
                koi_prad_err2 = num(ex5, "koi_prad_err2", "input_prad02", "Ej: -0.28", "%.2f")
                koi_insol_err2 = num(ex6, "koi_insol_err2", "input_insol02", "Ej: -3.96", "%.2f")

                ex7, ex8 = st.columns(2)
                koi_steff_err1 = num(ex7, "koi_steff_err1", "input_steff01", "Ej: 105", step=1)
                koi_slogg_err2 = num(ex8, "koi_slogg_err2", "input_slogg02", "Ej: -0.114", "%.3f")

                koi_srad_err1 = num(st.columns(1)[0], "koi_srad_err1", "input_srad01", "Ej: 0.143", "%.3f")

        # ---------------- TAB 4: COORDENADAS ----------------
        with tab4:
            st.caption("Identificación de Localización Estelar")
            g_c1, g_c2 = st.columns(2)
            ra = num(g_c1, "Ascensión Recta (ra)", "input_ra", "Ej: 295.64871", "%.5f")
            dec_val = num(g_c2, "Declinación (dec)", "input_dec", "Ej: 48.49556", "%.6f")
            koi_kepmag = num(st.columns(1)[0], "Magnitud Kepler (koi_kepmag)", "input_kepmag", "Ej: 12.772", "%.4f")

        submit_btn = st.form_submit_button("Ejecutar Clasificación")

    # Aviso persistente de campos enviados como 0.0
    if st.session_state.aviso:
        st.warning(st.session_state.aviso)

    # -----------------------------------------------------------------------
    # ENVÍO
    # -----------------------------------------------------------------------
    if submit_btn:
        flags = {
            "koi_fpflag_nt": koi_fpflag_nt,
            "koi_fpflag_ss": koi_fpflag_ss,
            "koi_fpflag_co": koi_fpflag_co,
            "koi_fpflag_ec": koi_fpflag_ec,
        }

        valores = {
            "koi_period": koi_period,
            "koi_time0bk": koi_time0bk,
            "koi_time0bk_err1": koi_time0bk_err1,
            "koi_time0bk_err2": koi_time0bk_err2,
            "koi_impact": koi_impact,
            "koi_impact_err1": koi_impact_err1,
            "koi_impact_err2": koi_impact_err2,
            "koi_duration": koi_duration,
            "koi_duration_err1": koi_duration_err1,
            "koi_duration_err2": koi_duration_err2,
            "koi_depth": koi_depth,
            "koi_depth_err1": koi_depth_err1,
            "koi_depth_err2": koi_depth_err2,
            "koi_prad": koi_prad,
            "koi_prad_err2": koi_prad_err2,
            "koi_teq": koi_teq,
            "koi_insol": koi_insol,
            "koi_insol_err2": koi_insol_err2,
            "koi_model_snr": koi_model_snr,
            "koi_tce_plnt_num": koi_tce_plnt_num,
            "koi_steff": koi_steff,
            "koi_steff_err1": koi_steff_err1,
            "koi_slogg": koi_slogg,
            "koi_slogg_err2": koi_slogg_err2,
            "koi_srad_err1": koi_srad_err1,
            "ra": ra,
            "dec": dec_val,
            "koi_kepmag": koi_kepmag,
        }

        campos_esenciales = [koi_period, koi_model_snr, koi_time0bk, koi_duration]

        if all(v is None for v in campos_esenciales):
            st.error("❌ No puedes clasificar un exoplaneta sin introducir datos. Por favor, completa los campos.")
        else:
            vacios = [k for k, v in valores.items() if v is None]
            st.session_state.aviso = (
                f"⚠️ {len(vacios)} campo(s) vacío(s) se enviaron como 0: " + ", ".join(vacios)
                if vacios else ""
            )

            payload = {k: int(v) for k, v in flags.items()}
            for k, v in valores.items():
                payload[k] = float(v) if v is not None else 0.0
            payload["koi_tce_plnt_num"] = int(valores["koi_tce_plnt_num"] or 0)

            with st.spinner("Enviando datos (si la IA estaba dormida puede tardar un poco)..."):
                try:
                    response = requests.post(CLASSIFY_URL, json=payload, timeout=90)

                    if response.status_code == 200:
                        resultado = response.json()

                        st.session_state.probabilidad_exoplaneta = float(
                            resultado.get("probability", 0.0)
                        )

                        clase = resultado.get("prediction")
                        etiquetas = {0: "CANDIDATO", 1: "CONFIRMADO", 2: "FALSO POSITIVO"}
                        st.session_state.veredicto_ia = etiquetas.get(int(clase), "DESCONOCIDO")

                        st.toast("¡Predicción procesada con éxito!", icon="🚀")
                        st.rerun()
                    else:
                        st.error(f"Error del backend ({response.status_code}): {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"No se pudo establecer contacto con la API en Java: {e}")
                except (TypeError, ValueError) as e:
                    st.error(f"Respuesta inesperada de la IA: {e}. Respuesta: {response.text}")
