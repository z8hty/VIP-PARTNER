import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os
import datetime
from fpdf import FPDF

st.set_page_config(page_title="VIP PARTNER | Outils CGP", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(181, 162, 123, 0.1);
        border-left: 5px solid #B5A27B;
        padding: 10px 20px;
        border-radius: 5px;
    }
    h1, h2, h3 { color: #B5A27B !important; font-family: 'Arial', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSE PDF GLOBALE ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(10, 26, 63)
        self.cell(0, 10, "Bilan d'Expertise Patrimoniale", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 10, f"Edite le {datetime.date.today().strftime('%d/%m/%Y')} - VIP PARTNER", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} - Document strictement confidentiel", align="C")

def generer_bouton_pdf(titre, lignes_texte, nom_fichier):
    """Fonction pour générer et télécharger un PDF rapidement"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, titre, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    for ligne in lignes_texte:
        # Encodage latin-1 pour éviter les bugs avec les symboles euro
        texte_propre = ligne.replace("€", "euros").encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, texte_propre)
    
    pdf.output("temp.pdf")
    with open("temp.pdf", "rb") as f:
        st.download_button(label=f"📥 Télécharger le Bilan ({nom_fichier})", data=f, file_name=f"{nom_fichier}.pdf", mime="application/pdf")

# --- FONCTIONS MARCHÉS ---
@st.cache_data(ttl=3600)
def isin_to_ticker(user_input):
    val = user_input.strip().upper()
    if len(val) == 12 and val[:2].isalpha():
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={val}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            res = requests.get(url, headers=headers)
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                return data['quotes'][0]['symbol']
        except:
            return None
    return val

@st.cache_data(ttl=3600)
def fetch_market_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="5y")

def determiner_devise(ticker):
    if "-USD" in ticker.upper() or ticker.upper() in ["AAPL", "MSFT", "TSLA", "SPY", "URTH"]: return "$"
    elif ".L" in ticker.upper(): return "£"
    elif ".CHF" in ticker.upper(): return "CHF"
    return "€"

# --- SIDEBAR & LOGO ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Expertise Patrimoniale", [
    "1. Marchés Financiers (Expert)", 
    "2. Capitalisation & Fiscalité", 
    "3. Impôt sur la Fortune (IFI)", 
    "4. Transmission & Démembrement"
])

# ==========================================
# MODULE 1 : MARCHÉS FINANCIERS
# ==========================================
if menu == "1. Marchés Financiers (Expert)":
    st.title("📈 Analyse des Supports")
    st.markdown("Recherchez vos actifs (ISIN ou Ticker). Ex: `CW8.PA, AI.PA, BTC-USD`.")
    
    col_input, col_period = st.columns([3, 1])
    recherche_utilisateur = col_input.text_input("Saisir un actif :", "AI.PA")
    periode_affichage = col_period.selectbox("Période d'affichage", ["1 an", "3 ans", "5 ans"])
    
    ticker_final = isin_to_ticker(recherche_utilisateur)
    
    if ticker_final:
        try:
            data = fetch_market_data(ticker_final)
            if not data.empty:
                if periode_affichage == "1 an": df_display = data.last('365D')
                elif periode_affichage == "3 ans": df_display = data.last('1095D')
                else: df_display = data
                
                devise = determiner_devise(ticker_final)
                prix_actuel = df_display['Close'].iloc[-1]
                prix_debut = df_display['Close'].iloc[0]
                perf_periode = ((prix_actuel / prix_debut) - 1) * 100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Dernier Cours", f"{prix_actuel:,.2f} {devise}")
                c2.metric(f"Performance ({periode_affichage})", f"{perf_periode:.2f} %")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_display.index, y=df_display['Close'], line=dict(color='#B5A27B', width=2)))
                fig.update_layout(title=f"Evolution de {ticker_final}", yaxis_title="Prix", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                
                # EXPORT PDF
                st.markdown("---")
                lignes_pdf = [
                    f"- Actif analyse : {ticker_final}",
                    f"- Periode observee : {periode_affichage}",
                    f"- Cours actuel : {prix_actuel:,.2f} {devise}",
                    f"- Performance sur la periode : {perf_periode:.2f} %"
                ]
                generer_bouton_pdf(f"Analyse de Marche : {ticker_final}", lignes_pdf, "Bilan_Marche")

            else:
                st.warning("Données introuvables. Vérifiez le code de l'actif.")
        except Exception as e:
            # GESTION PROPRE DU RATE LIMIT
            st.error("⚠️ Les serveurs de données financières (Yahoo) bloquent temporairement l'accès en raison d'un trop grand nombre de requêtes. Veuillez patienter quelques minutes et réessayer.")
            st.write(f"*(Détail technique : {e})*")

# ==========================================
# MODULE 2 : CAPITALISATION
# ==========================================
elif menu == "2. Capitalisation & Fiscalité":
    st.title("💰 Croissance & Fiscalité")
    
    c1, c2, c3, c4 = st.columns(4)
    capital_init = c1.number_input("Capital initial (€)", value=50000, step=5000)
    versement = c2.number_input("Versement mensuel (€)", value=500, step=100)
    taux_brut = c3.number_input("Rendement cible brut (%)", value=6.0, step=0.5)
    annees = c4.slider("Horizon (Années)", 5, 40, 15)
    
    taux_mensuel = (taux_brut / 100) / 12
    cap = capital_init
    total_versements = capital_init
    for _ in range(annees * 12):
        cap = cap * (1 + taux_mensuel) + versement
        total_versements += versement
        
    plus_values = cap - total_versements
    pfu = plus_values * 0.30
    capital_net = cap - pfu
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Brut", f"{cap:,.0f} €".replace(',', ' '))
    r2.metric("Plus-values", f"{plus_values:,.0f} €".replace(',', ' '))
    r3.metric("Impôts (PFU 30%)", f"- {pfu:,.0f} €".replace(',', ' '))
    st.info(f"💶 Valeur Nette dans la poche : {capital_net:,.0f} €")
    
    # EXPORT PDF
    st.markdown("---")
    lignes_pdf = [
        f"- Capital de depart : {capital_init:,.0f} euros",
        f"- Versement mensuel : {versement:,.0f} euros",
        f"- Rendement estime : {taux_brut} % sur {annees} ans",
        "",
        f"- Capital brut obtenu : {cap:,.0f} euros",
        f"- Dont plus-values : {plus_values:,.0f} euros",
        f"- PFU (30%) : - {pfu:,.0f} euros",
        f"-> CAPITAL NET : {capital_net:,.0f} euros"
    ]
    generer_bouton_pdf("Projection de Capitalisation", lignes_pdf, "Bilan_Capitalisation")

# ==========================================
# MODULE 3 : IFI
# ==========================================
elif menu == "3. Impôt sur la Fortune (IFI)":
    st.title("🏛️ Simulateur IFI")
    c1, c2, c3 = st.columns(3)
    rp = c1.number_input("Valeur Résidence Principale (€)", value=900000, step=50000)
    autre_immo = c2.number_input("Autres Biens Immobiliers (€)", value=600000, step=50000)
    dettes = c3.number_input("Passif déductible (€)", value=150000, step=10000)
    
    rp_nette = rp * 0.70
    patrimoine_net_taxable = rp_nette + autre_immo - dettes
    
    r1, r2 = st.columns(2)
    r1.metric("Résidence Principale (après abattement 30%)", f"{rp_nette:,.0f} €".replace(',', ' '))
    r2.metric("Patrimoine Net Taxable IFI", f"{patrimoine_net_taxable:,.0f} €".replace(',', ' '))
    
    ifi = 0
    if patrimoine_net_taxable > 1300000:
        p = patrimoine_net_taxable
        if p > 10000000: ifi += (p - 10000000) * 0.015; p = 10000000
        if p > 5000000: ifi += (p - 5000000) * 0.0125; p = 5000000
        if p > 2570000: ifi += (p - 2570000) * 0.01; p = 2570000
        if p > 1300000: ifi += (p - 1300000) * 0.007; p = 1300000
        if p > 800000: ifi += (p - 800000) * 0.005
        
        if 1300000 < patrimoine_net_taxable < 1400000:
            decote = 17500 - (0.0125 * patrimoine_net_taxable)
            ifi = max(0, ifi - decote)
        st.error(f"🔴 Montant de l'IFI à régler : {ifi:,.0f} € / an")
    else:
        st.success("🟢 Patrimoine Net Taxable inférieur à 1 300 000 €. Non assujetti à l'IFI.")

    # EXPORT PDF
    st.markdown("---")
    lignes_pdf = [
        f"- Valeur Residence Principale : {rp:,.0f} euros",
        f"- Abattement de 30% : - {rp - rp_nette:,.0f} euros",
        f"- Autres biens immobiliers : {autre_immo:,.0f} euros",
        f"- Dettes deductibles : - {dettes:,.0f} euros",
        "",
        f"-> PATRIMOINE NET TAXABLE : {patrimoine_net_taxable:,.0f} euros",
        f"-> MONTANT IFI ESTIME : {ifi:,.0f} euros"
    ]
    generer_bouton_pdf("Audit Impot sur la Fortune Immobiliere", lignes_pdf, "Bilan_IFI")

# ==========================================
# MODULE 4 : TRANSMISSION
# ==========================================
elif menu == "4. Transmission & Démembrement":
    st.title("👨‍👩‍👧‍👦 Démembrement de Propriété (CGI)")
    c1, c2 = st.columns(2)
    valeur_bien = c1.number_input("Valeur du bien en Pleine Propriété (€)", value=400000, step=10000)
    age_donateur = c2.slider("Âge du donateur (Usufruitier)", 40, 95, 65)
    
    # Calcul manuel pour éviter les erreurs d'appel
    if age_donateur <= 20: u_pct, n_pct = 0.9, 0.1
    elif age_donateur <= 30: u_pct, n_pct = 0.8, 0.2
    elif age_donateur <= 40: u_pct, n_pct = 0.7, 0.3
    elif age_donateur <= 50: u_pct, n_pct = 0.6, 0.4
    elif age_donateur <= 60: u_pct, n_pct = 0.5, 0.5
    elif age_donateur <= 70: u_pct, n_pct = 0.4, 0.6
    elif age_donateur <= 80: u_pct, n_pct = 0.3, 0.7
    elif age_donateur <= 90: u_pct, n_pct = 0.2, 0.8
    else: u_pct, n_pct = 0.1, 0.9
    
    val_u = valeur_bien * u_pct
    val_n = valeur_bien * n_pct
    
    r1, r2 = st.columns(2)
    r1.metric(f"Valeur Usufruit ({u_pct*100:.0f}%)", f"{val_u:,.0f} €".replace(',', ' '))
    r2.metric(f"Valeur Nue-Propriété ({n_pct*100:.0f}%)", f"{val_n:,.0f} €".replace(',', ' '))
    st.info(f"💡 Droits de succession calculés sur **{val_n:,.0f} €** au lieu de {valeur_bien:,.0f} €.")

    # EXPORT PDF
    st.markdown("---")
    lignes_pdf = [
        f"- Age du donateur : {age_donateur} ans",
        f"- Valeur du bien (Pleine Propriete) : {valeur_bien:,.0f} euros",
        "",
        f"- Valeur de l'Usufruit conserve ({u_pct*100:.0f}%) : {val_u:,.0f} euros",
        f"- Valeur de la Nue-Propriete transmise ({n_pct*100:.0f}%) : {val_n:,.0f} euros",
        "",
        "Strategie : En donnant la nue-propriete aujourd'hui, les droits",
        "seront calcules uniquement sur la base de la nue-propriete.",
        "Au deces de l'usufruitier, la pleine propriete est reconstituee",
        "sans impots supplementaires."
    ]
    generer_bouton_pdf("Bilan Transmission & Demembrement", lignes_pdf, "Bilan_Transmission")
