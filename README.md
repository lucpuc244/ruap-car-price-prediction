# 🚗 RUAP – Car Price Prediction System

Sustav za procjenu tržišne cijene rabljenih automobila temeljen na strojnom učenju i stvarnim podacima prikupljenima s portala Njuškalo.

---

## 📌 O projektu

Ovaj projekt razvijen je u sklopu kolegija RUAP s ciljem demonstracije cjelovitog procesa:
- prikupljanja podataka  
- obrade i analize podataka  
- treniranja modela strojnog učenja  
- deploya modela u oblaku  
- razvoja web aplikacije  

Sustav korisniku omogućuje unos specifikacija vozila i dobivanje procijenjene tržišne cijene.

---

## 🌐 Online aplikacija 

Web aplikacija dostupna je na sljedećoj poveznici:  
https://car-price-app-wuyibyihgfyht5tzy7dood.streamlit.app/

--

## 🧠 Korištene značajke

- Marka vozila  
- Model vozila  
- Starost (godine)  
- Kilometraža  
- Snaga motora (kW)  
- Tip mjenjača  

---

## 🛠 Tehnologije

- Python  
- Pandas  
- NumPy  
- Scikit-learn  
- Flask  
- Azure Machine Learning  
- GitHub  

---

## 📂 Struktura projekta

ruap-car-price-prediction/  
├── scraping/   → prikupljanje podataka  
├── ml/         → treniranje i evaluacija modela  
├── web/        → web aplikacija  
└── .gitignore  

---

## ⚙️ Pokretanje lokalno

1. Kloniranje repozitorija

git clone https://github.com/lucpuc244/ruap-car-price-prediction.git  

2. Instalacija potrebnih paketa

pip install -r requirements.txt  

3. Pokretanje web aplikacije

python web/app.py  

---

## ☁️ Deploy modela

Model je deployan u oblaku korištenjem Azure Machine Learning servisa kao online endpoint, čime je omogućena komunikacija između web aplikacije i modela putem web usluge.

---

## 📊 Skup podataka

Skup podataka nije uključen u repozitorij zbog veličine i načina prikupljanja.  
Podaci se generiraju web scrapingom ili koriste lokalno.

---

## 🎯 Cilj projekta

- Demonstrirati primjenu strojnog učenja u realnom problemu  
- Razviti funkcionalnu web aplikaciju  
- Povezati lokalni razvoj s cloud rješenjem  

---

## 👨‍🎓 Autor 

Projekt izrađen u edukativne svrhe u sklopu kolegija RUAP. :3
