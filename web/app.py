import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# CONFIG
# -----------------------------
DATA_PATH = "njuskalo_osijek_regija_auti_5000_2_fixed.csv"

# Stavi svoj URL slike ovdje (može i Pinterest kao što si slala)
HERO_IMAGE_URL = "https://i.pinimg.com/736x/62/97/b5/6297b51b69b4f0be703ee06da9fe7817.jpg"

st.set_page_config(
    page_title="Procjena cijene rabljenih auta",
    page_icon=None,          # makne emoji auta
    layout="centered",
)

# -----------------------------
# STYLE (bež tema + kontrast + animacija gumba + sakrij Streamlit chrome)
# -----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

html, body, [class*="css"] {
  font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.stApp {
  background: radial-gradient(1200px 600px at 30% 20%, #fff7ea 0%, #f0dfc6 45%, #e8d3b6 100%);
}

/* Makni Streamlit header/menu/footer */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="stDecoration"] {visibility: hidden;}

/* Malo ljepši padding */
.block-container {
  padding-top: 1.6rem;
  padding-bottom: 2.5rem;
}

/* Hero slika */
.hero {
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 18px 50px rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.08);
}

/* Card */
.card {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0,0,0,0.10);
  box-shadow: 0 18px 60px rgba(0,0,0,0.10);
  border-radius: 22px;
  padding: 22px 22px 18px 22px;
  backdrop-filter: blur(10px);
}

/* Naslov i podnaslov */
h1.title {
  margin: 0.2rem 0 0.2rem 0;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #2b231c;
  font-size: 3.0rem;
}
p.subtitle {
  margin-top: 0;
  margin-bottom: 1.2rem;
  color: rgba(43,35,28,0.78);
  font-size: 1.05rem;
  line-height: 1.55;
}

/* Labeli */
label, .stMarkdown, .stTextLabelWrapper p {
  color: #2b231c !important;
  font-weight: 600;
}

/* Inputi/selectovi */
[data-baseweb="select"] > div,
.stNumberInput input,
.stTextInput input {
  border-radius: 14px !important;
}

/* Slider boje */
[data-testid="stSlider"] [role="slider"] {
  background: #8a6a4a !important;
  border: 2px solid #8a6a4a !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] {
  color: rgba(43,35,28,0.35);
}

/* Gumb - animacija */
.stButton>button {
  background: linear-gradient(135deg, #8a6a4a 0%, #6e5237 100%);
  color: #fff;
  border: none;
  border-radius: 18px;
  padding: 0.9rem 1.25rem;
  font-weight: 800;
  font-size: 1.05rem;
  box-shadow: 0 16px 40px rgba(110,82,55,0.28);
  transform: translateY(0px) scale(1);
  transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}
.stButton>button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 22px 55px rgba(110,82,55,0.35);
  filter: brightness(1.03);
}
.stButton>button:active {
  transform: translateY(0px) scale(0.99);
  box-shadow: 0 12px 32px rgba(110,82,55,0.22);
}

/* Alert box */
[data-testid="stAlert"] {
  border-radius: 18px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# DATA
# -----------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normaliziraj nazive stupaca ako imaju razmake
    df.columns = [c.strip() for c in df.columns]

    # Očekivani stupci (prema tvom projektu)
    # Price_market, Brand, Model, Transmission, Age, Mileage, Power_kW
    # Ako neki nedostaje, probaj s varijantama
    rename_map = {}
    if "Power_kW" not in df.columns and "Power (kW)" in df.columns:
        rename_map["Power (kW)"] = "Power_kW"
    if "Price_market" not in df.columns and "Price" in df.columns:
        rename_map["Price"] = "Price_market"
    if rename_map:
        df = df.rename(columns=rename_map)

    # Trim stringova
    for c in ["Brand", "Model", "Transmission"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # Numerički
    for c in ["Price_market", "Age", "Mileage", "Power_kW"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop rows bez ključnih polja
    needed = [c for c in ["Price_market", "Brand", "Model", "Age", "Mileage", "Power_kW"] if c in df.columns]
    df = df.dropna(subset=needed)

    return df


df = load_data(DATA_PATH)

# -----------------------------
# HERO IMAGE
# -----------------------------
if HERO_IMAGE_URL:
    st.markdown(f"""
<div class="hero">
  <img src="{HERO_IMAGE_URL}" style="width:100%; height:280px; object-fit:cover; display:block;" />
</div>
""", unsafe_allow_html=True)
    st.write("")

# -----------------------------
# TITLE
# -----------------------------
st.markdown('<h1 class="title">Odabir specifikacija</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Unesi podatke o vozilu i dobit ćeš procjenu cijene na temelju sličnih oglasa iz dataseta.</p>',
    unsafe_allow_html=True
)

# -----------------------------
# UI CARD
# -----------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Brand / Model / Transmission iz dataseta (da se vrijednosti poklapaju i da ne bude "nema vozila")
brands = sorted(df["Brand"].dropna().unique()) if "Brand" in df.columns else []
default_brand = brands[0] if brands else ""

with col1:
    brand = st.selectbox("Brand", brands, index=0 if brands else 0)

    models = sorted(df[df["Brand"] == brand]["Model"].dropna().unique()) if "Model" in df.columns else []
    model = st.selectbox("Model", models, index=0 if models else 0)

    # Transmission opcije iz dataseta; ako nema stupca, daj "N/A"
    if "Transmission" in df.columns:
        trans_vals = sorted(df[(df["Brand"] == brand) & (df["Model"] == model)]["Transmission"].dropna().unique())
        if not trans_vals:
            trans_vals = sorted(df["Transmission"].dropna().unique())
        transmission = st.selectbox("Mjenjač", trans_vals, index=0 if trans_vals else 0)
    else:
        transmission = "N/A"
        st.selectbox("Mjenjač", ["N/A"], index=0)

with col2:
    # Sigurni min/max za slidere
    age_min = int(df["Age"].min()) if "Age" in df.columns else 0
    age_max = int(df["Age"].max()) if "Age" in df.columns else 30
    age_default = int(np.clip(np.median(df["Age"]), age_min, age_max)) if "Age" in df.columns else 5
    age = st.slider("Starost (godina)", age_min, age_max, age_default)

    km_min = int(df["Mileage"].min()) if "Mileage" in df.columns else 0
    km_max = int(df["Mileage"].max()) if "Mileage" in df.columns else 400_000
    km_default = int(np.clip(np.median(df["Mileage"]), km_min, km_max)) if "Mileage" in df.columns else 150_000
    km = st.slider("Kilometraža (km)", km_min, km_max, km_default)

    kw_min = int(df["Power_kW"].min()) if "Power_kW" in df.columns else 40
    kw_max = int(df["Power_kW"].max()) if "Power_kW" in df.columns else 250
    kw_default = int(np.clip(np.median(df["Power_kW"]), kw_min, kw_max)) if "Power_kW" in df.columns else 90
    power = st.slider("Snaga (kW)", kw_min, kw_max, kw_default)

st.write("")

# -----------------------------
# ESTIMATION (robust fallback)
# -----------------------------
def estimate_price(data: pd.DataFrame, brand: str, model: str, transmission: str, age: int, km: int, power: int):
    # 1) Pokušaj strogo: Brand+Model (+Transmission ako postoji)
    base = data[(data["Brand"] == brand) & (data["Model"] == model)].copy()

    if "Transmission" in data.columns and transmission != "N/A":
        base_t = base[base["Transmission"] == transmission].copy()
        if not base_t.empty:
            base = base_t  # koristi ako ima pogodaka

    # 2) Ako je i dalje premalo, uzmi najbližih K po numeričkoj udaljenosti (KNN-like)
    # Normalizacija po rasponima da sve ima smisla
    if base.empty:
        base = data[data["Brand"] == brand].copy()  # barem isti brand kao fallback

    if base.empty:
        base = data.copy()

    # Ako nema numeričkih stupaca, nema procjene
    for c in ["Age", "Mileage", "Power_kW", "Price_market"]:
        if c not in base.columns:
            return None, None, 0

    # Udaljenost
    eps = 1e-9
    age_range = (data["Age"].max() - data["Age"].min()) + eps
    km_range = (data["Mileage"].max() - data["Mileage"].min()) + eps
    kw_range = (data["Power_kW"].max() - data["Power_kW"].min()) + eps

    d = (
        ((base["Age"] - age).abs() / age_range)
        + ((base["Mileage"] - km).abs() / km_range)
        + ((base["Power_kW"] - power).abs() / kw_range)
    )

    base = base.assign(_dist=d).sort_values("_dist")

    K = 50
    top = base.head(K).copy()
    n = int(len(top))

    if n == 0:
        return None, None, 0

    median_price = float(top["Price_market"].median())

    # raspon: manji ako ima dosta podataka, veći ako ih je malo
    spread = 1000 if n >= 20 else 2500
    lo, hi = median_price - spread, median_price + spread
    return median_price, (lo, hi), n


if st.button("Procijeni", type="primary"):
    price, rng, n = estimate_price(df, brand, model, transmission, age, km, power)

    if price is None:
        st.error("Ne mogu izračunati procjenu (provjeri da dataset ima potrebne stupce).")
    else:
        st.success("Procjena izračunata.")
        st.write("")

        st.metric("Procijenjena cijena", f"{int(round(price)):,} €".replace(",", "."))

        if rng:
            lo, hi = rng
            st.caption(f"Raspon procjene: {int(round(lo)):,} € – {int(round(hi)):,} €".replace(",", "."))

        st.caption(f"Procjena temeljena na ~{n} najsličnijih zapisa iz dataseta.")

st.markdown("</div>", unsafe_allow_html=True)

