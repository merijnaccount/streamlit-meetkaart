import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from pathlib import Path
import random

# --- Pagina instellingen ---
st.set_page_config(page_title="Interactieve Meetkaart", layout="wide")
st.title("📍 Python cursus okt 2025 - Interactieve Meetdata Kaart 2014–2024")

# --- Pad naar Excelbestand ---
bestandspad = Path("Dummy_bestand_volledig_random_2014_2024.xlsx")

# ==============================================================
# 📂 1️⃣ Data inladen (alleen één keer via caching)
# ==============================================================

@st.cache_data(ttl=None)
def load_data(pad: Path) -> pd.DataFrame:
    """Lees het Excel-bestand één keer in en parse de datums."""
    df = pd.read_excel(str(pad))
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df["Jaar"] = df["Datum"].dt.year
    return df

with st.spinner("📂 Gegevens worden ingeladen... even geduld..."):
    df = load_data(bestandspad)

# ==============================================================
# 🗺️ 2️⃣ Hulpfuncties
# ==============================================================

# Bekende woonplaatsen + coördinaten
TOWN_COORDS = {
    "Utrecht": (52.0907, 5.1214), "Amersfoort": (52.1561, 5.3878), "Veenendaal": (52.0286, 5.5589),
    "Lelystad": (52.5185, 5.4714), "Almere": (52.3508, 5.2647), "Dronten": (52.5250, 5.7181),
    "Arnhem": (51.9851, 5.8987), "Nijmegen": (51.8126, 5.8372), "Apeldoorn": (52.2112, 5.9699),
    "Zwolle": (52.5168, 6.0830), "Enschede": (52.2215, 6.8937), "Deventer": (52.2550, 6.1639),
    "Leeuwarden": (53.2012, 5.7999), "Sneek": (53.0323, 5.6589), "Drachten": (53.1123, 6.0989),
}

def kleur_op_basis_van_meetwaarde(waarde: float) -> str:
    """Bepaal kleur op basis van Ruw.Res.-waarde."""
    if waarde < 1:
        return "green"
    elif waarde < 10:
        return "yellow"
    elif waarde < 50:
        return "orange"
    else:
        return "red"

# ==============================================================
# 📊 3️⃣ Voorbereiding van data per jaar (ook gecached)
# ==============================================================

@st.cache_data
def prepare_data(df: pd.DataFrame, jaar: int):
    """Filter de data per jaar en bereken jitter-coördinaten."""
    df_jaar = df[df["Jaar"] == jaar].copy()
    df_jaar = df_jaar[df_jaar["Woonplaats"].isin(TOWN_COORDS.keys())]

    rng = np.random.default_rng(42)
    lat_lon = []
    for _, row in df_jaar.iterrows():
        base_lat, base_lon = TOWN_COORDS[row["Woonplaats"]]
        lat = base_lat + rng.normal(0, 0.004)
        lon = base_lon + rng.normal(0, 0.006)
        lat_lon.append((lat, lon))
    df_jaar["lat"], df_jaar["lon"] = zip(*lat_lon)

    return df_jaar

# ==============================================================
# 🎛️ 4️⃣ Gebruikersinterface
# ==============================================================

# Dropdown-menu voor jaarselectie
jaren = sorted(df["Jaar"].dropna().unique())
gekozen_jaar = st.selectbox("Kies een kalenderjaar:", jaren, index=len(jaren)-1)

# Data voor gekozen jaar ophalen
df_jaar = prepare_data(df, gekozen_jaar)

st.write(f"📊 Aantal meetpunten in {gekozen_jaar}: **{len(df_jaar):,}**")

# ==============================================================
# 🗺️ 5️⃣ Kaart genereren
# ==============================================================

m = folium.Map(location=[52.2, 5.3], zoom_start=7, tiles="cartodbpositron")
cluster = MarkerCluster(name="Meetpunten").add_to(m)

sample_size = min(2000, len(df_jaar))
sample_df = df_jaar.sample(n=sample_size, random_state=42)

for _, row in sample_df.iterrows():
    kleur = kleur_op_basis_van_meetwaarde(row["Ruw.Res."])
    popup_html = f"""
    <b>{row.get('Straat', '')}</b> {row.get('Huisnummer', '')}<br>
    {row.get('Postcode', '')} {row.get('Woonplaats', '')}<br>
    Datum: {pd.to_datetime(row.get('Datum')).date()}<br>
    Ruw.Res.: <b>{row.get('Ruw.Res.', 0)}</b>
    """
    folium.CircleMarker(
        location=(row["lat"], row["lon"]),
        radius=6,
        color=kleur,
        fill=True,
        fill_color=kleur,
        fill_opacity=0.8,
        popup=popup_html,
    ).add_to(cluster)

folium.LayerControl().add_to(m)

# ==============================================================
# 🌍 6️⃣ Kaart tonen
# ==============================================================

st_folium(m, width=1000, height=650)

# ==============================================================
# 🔵 7️⃣ Legenda
# ==============================================================

st.markdown("""
### 🔵 Legenda
| Kleur | Waarde (Ruw.Res.) |
|-------|--------------------|
| 🟢 Groen | < 1 |
| 🟡 Geel | 1 – 10 |
| 🟠 Oranje | 10 – 50 |
| 🔴 Rood | > 50 |
""")


