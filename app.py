import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import datetime
from fpdf import FPDF
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="VIP PARTNER | Cockpit Financier", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(181, 162, 123, 0.05);
        border-left: 4px solid #B5A27B;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2, h3 { color: #B5A27B !important; font-family: 'Arial', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { color: #E0E0E0; font-weight: bold; }
    .stTabs [aria-selected="true"] { color: #B5A27B !important; border-bottom-color: #B5A27B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTEUR PDF PREMIUM ANTI-CRASH ---
class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(181, 162, 123)
            self.cell(190, 10, "VIP PARTNER - Cockpit Financier", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 20, 200, 20)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(190, 10, f"Page {self.page_no()} - Document confidentiel du {datetime.date.today().strftime('%d/%m/%Y')}", align="C")

def nettoyer_texte_pdf(texte):
    """Filtre absolu pour empêcher FPDF de crasher sur les espaces et accents français"""
    t = str(texte)
    remplacements = {
        "€": "EUR", "%": "pourcents", "->": "=>",
        "é": "e", "è": "e", "ê": "e", "à": "a", "â": "a", 
        "ô": "o", "î": "i", "û": "u", "ç": "c", 
        "\xa0": " ", "\u202f": " " # Tue les espaces insécables !
    }
    for k, v in remplacements.items():
        t = t.replace(k, v)
    return t.encode('ascii', 'ignore').decode('ascii')

def generer_pdf_premium(titre_doc, sections, nom_fichier):
    pdf = PDF()
    pdf.set_margins(left=10, top=10, right=10)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page de Garde
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=85, y=40, w=40)
    
    pdf.set_y(100)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(10, 26, 63)
    pdf.cell(190, 15, "BILAN FINANCIER", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(181, 162, 123)
    pdf.cell(190, 10, nettoyer_texte_pdf(titre_doc).upper(), align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Contenu
    pdf.add_page()
    for titre_section, lignes in sections:
        pdf.set_fill_color(10, 26, 63)
        pdf.set_text_color(181, 162, 123)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(190, 10, f"  {nettoyer_texte_pdf(titre_section)}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        for ligne in lignes:
            if str(ligne).strip() == "":
                pdf.ln(4)
            else:
                l_propre = nettoyer_texte_pdf(ligne)
                if l_propre.startswith("=>") or "TOTAL" in l_propre.upper() or "NET" in l_propre.upper():
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.set_text_color(10, 26, 63)
                else:
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_text_color(30, 30, 30)
                
                pdf.multi_cell(w=190, h=8, text=l_propre)
        pdf.ln(8)
    
    pdf.output("temp_luxe.pdf")
    with open("temp_luxe.pdf", "rb") as f:
        st.download_button(label=f"📥 Télécharger le Rapport PDF ({nom_fichier})", data=f, file_name=f"{nom_fichier}.pdf", mime="application/pdf")

# --- FONCTION BOURSE SÉCURISÉE (Regarde sur 7 jours) ---
@st.cache_data(ttl=900)
def get_live_price(ticker):
    val = ticker.strip().upper()
    try:
        # Si c'est un ISIN, on trouve le vrai Ticker Yahoo
        if len(val) == 12 and val[:2].isalpha():
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={val}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                val = data['quotes'][0]['symbol']
                
        # On va chercher l'historique sur 7 jours (pour les fonds qui mettent du temps à actualiser)
        stock = yf.Ticker(val)
        hist = stock.history(period="7d")
        if not hist.empty:
            # On prend le dernier prix de fermeture valide
            dernier_prix = hist['Close'].dropna().iloc[-1]
            return float(dernier_prix), val
        return 0.0, val
    except:
        return 0.0, val

# --- SIDEBAR ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Mon Cockpit Financier", [
    "1. Tableau de Bord Global", 
    "2. Gestion du Budget", 
    "3. Mes Placements (Temps Réel)", 
    "4. Liberté Financière (FIRE)"
])

# ==========================================
# MODULE 1 : TABLEAU DE BORD (NET WORTH)
# ==========================================
if menu == "1. Tableau de Bord Global":
    st.title("🌐 Vision Globale du Patrimoine")
    st.write("Analysez vos actifs, vos dettes et vos ratios de santé financière.")
    
    col_actifs, col_passifs = st.columns(2)
    
    with col_actifs:
        st.subheader("🟢 Actifs (Ce que je possède)")
        immo = st.number_input("Immobilier (Résidence principale, locatif)", value=250000, step=10000)
        liquidites = st.number_input("Liquidités (Comptes courants, Livret A)", value=20000, step=1000)
        investissements = st.number_input("Placements Bourse & Crypto", value=45000, step=1000)
        assurances_vie = st.number_input("Assurance-Vie (Fonds Euros)", value=15000, step=1000)
        autres_actifs = st.number_input("Autres (Voiture, Montres...)", value=10000, step=1000)
        total_actifs = immo + liquidites + investissements + assurances_vie + autres_actifs

    with col_passifs:
        st.subheader("🔴 Passifs (Ce que je dois)")
        credit_immo = st.number_input("Crédits Immobiliers (Restant dû)", value=180000, step=10000)
        credit_conso = st.number_input("Crédits Consommation / Auto", value=8000, step=1000)
        autres_dettes = st.number_input("Autres dettes (Fisc, Famille)", value=0, step=500)
        total_passifs = credit_immo + credit_conso + autres_dettes

    patrimoine_net = total_actifs - total_passifs
    
    ratio_endettement = (total_passifs / total_actifs * 100) if total_actifs > 0 else 0
    ratio_liquidite = (liquidites / total_actifs * 100) if total_actifs > 0 else 0
    
    st.markdown("---")
    st.subheader("Indicateurs Clés")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Actifs", f"{total_actifs:,.0f} €".replace(',', ' '))
    c2.metric("Total Passifs", f"{total_passifs:,.0f} €".replace(',', ' '))
    c3.metric("💰 PATRIMOINE NET", f"{patrimoine_net:,.0f} €".replace(',', ' '))
    c4.metric("Ratio d'Endettement", f"{ratio_endettement:.1f} %", "Idéal < 33%", delta_color="off")
    
    fig = px.pie(
        values=[immo, liquidites, investissements, assurances_vie, autres_actifs], 
        names=["Immobilier", "Liquidités", "Bourse/Crypto", "Fonds Euros", "Autres"],
        hole=0.4, color_discrete_sequence=['#B5A27B', '#0A1A3F', '#1F3A82', '#4A69A5', '#E0E0E0']
    )
    fig.update_layout(title="Allocation du Patrimoine Brut", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Synthese des Actifs", [
            f"- Immobilier : {immo:,.0f} EUR",
            f"- Liquidites disponibles : {liquidites:,.0f} EUR",
            f"- Bourse et Cryptomonnaies : {investissements:,.0f} EUR",
            f"- Assurance-Vie (Fonds garantis) : {assurances_vie:,.0f} EUR",
            f"- Actifs divers : {autres_actifs:,.0f} EUR",
            "",
            f"TOTAL ACTIFS : {total_actifs:,.0f} EUR"
        ]),
        ("Synthese des Passifs", [
            f"- Capitaux restants dus (Immo) : {credit_immo:,.0f} EUR",
            f"- Credits consommation : {credit_conso:,.0f} EUR",
            f"- Dettes diverses : {autres_dettes:,.0f} EUR",
            "",
            f"TOTAL PASSIFS : {total_passifs:,.0f} EUR"
        ]),
        ("Bilan et Ratios", [
            f"=> PATRIMOINE NET (Actifs - Passifs) : {patrimoine_net:,.0f} EUR",
            "",
            f"- Ratio d'endettement global : {ratio_endettement:.1f} %",
            f"- Poids des liquidites : {ratio_liquidite:.1f} % du patrimoine total"
        ])
    ]
    generer_pdf_premium("Photographie du Patrimoine", sections_pdf, "Cockpit_Patrimoine")

# ==========================================
# MODULE 2 : BUDGET MENSUEL & WATERFALL
# ==========================================
elif menu == "2. Gestion du Budget":
    st.title("💶 Cash-Flow & Analyse des Flux")
    st.write("Suivez la règle du **50/30/20** pour structurer vos dépenses et identifier votre capacité d'épargne réelle.")

    col_inc, col_exp = st.columns(2)
    with col_inc:
        st.subheader("Entrées d'argent (Mensuel)")
        salaire = st.number_input("Salaires et Primes nets", value=3200, step=100)
        revenus_side = st.number_input("Locatif / Aides / Autres", value=400, step=50)
        total_revenus = salaire + revenus_side
        
    with col_exp:
        st.subheader("Sorties d'argent (Mensuel)")
        charges_fixes = st.number_input("Besoins fixes (Loyer, Assurances, Courses)", value=1500, step=50)
        depenses_plaisir = st.number_input("Envies (Sorties, Shopping, Loisirs)", value=700, step=50)
        epargne_invest = st.number_input("Épargne & Investissements programmés", value=800, step=50)
        total_depenses = charges_fixes + depenses_plaisir + epargne_invest

    reste_a_vivre = total_revenus - total_depenses
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Revenus", f"{total_revenus:,.0f} €".replace(',', ' '))
    r2.metric("Total Dépenses", f"{total_depenses:,.0f} €".replace(',', ' '))
    r3.metric("Reste à vivre (Non alloué)", f"{reste_a_vivre:,.0f} €".replace(',', ' '), delta="Surplus dispo" if reste_a_vivre >= 0 else "Déficit !", delta_color="normal" if reste_a_vivre >= 0 else "inverse")

    fig_waterfall = go.Figure(go.Waterfall(
        name="Budget", orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "total"],
        x=["Salaires", "Autres Revenus", "Charges Fixes", "Plaisirs", "Épargne", "Reste à vivre"],
        textposition="outside",
        y=[salaire, revenus_side, -charges_fixes, -depenses_plaisir, -epargne_invest, reste_a_vivre],
        connector={"line":{"color":"#E0E0E0"}},
        decreasing={"marker":{"color":"#0A1A3F"}},
        increasing={"marker":{"color":"#B5A27B"}},
        totals={"marker":{"color":"green" if reste_a_vivre >= 0 else "red"}}
    ))
    fig_waterfall.update_layout(title="Cascade du Budget Mensuel", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Flux Entrants (Revenus)", [
            f"- Salaires nets : {salaire:,.0f} EUR",
            f"- Revenus annexes : {revenus_side:,.0f} EUR",
            f"TOTAL REVENUS : {total_revenus:,.0f} EUR"
        ]),
        ("Flux Sortants (Depenses & Epargne)", [
            f"- Besoins incompressibles : {charges_fixes:,.0f} EUR",
            f"- Depenses de confort : {depenses_plaisir:,.0f} EUR",
            f"- Epargne forcee : {epargne_invest:,.0f} EUR",
            f"TOTAL DEPENSES : {total_depenses:,.0f} EUR"
        ]),
        ("Analyse du Cash-Flow", [
            f"=> RESTE A VIVRE (Libre) : {reste_a_vivre:,.0f} EUR",
            "",
            "Conformite a la regle 50/30/20 :",
            f"- Besoins (Ideal 50%) : {(charges_fixes/total_revenus*100):.1f} %",
            f"- Plaisirs (Ideal 30%) : {(depenses_plaisir/total_revenus*100):.1f} %",
            f"- Epargne (Ideal 20%) : {(epargne_invest/total_revenus*100):.1f} %"
        ])
    ]
    generer_pdf_premium("Analyse Budgetaire", sections_pdf, "Cockpit_Budget")

# ==========================================
# MODULE 3 : TABLEAU INTERACTIF BOURSE (SIMPLIFIÉ POUR LE GRAND PUBLIC)
# ==========================================
elif menu == "3. Mes Placements (Temps Réel)":
    st.title("📈 Suivi de mes Investissements")
    st.write("Entrez le code de votre placement (ISIN ou Nom court comme BTC-USD), la quantité et votre prix d'achat. **Le calcul se fait tout seul.**")
    
    # Données par défaut avec un vocabulaire grand public
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = pd.DataFrame({
            "Nom du placement (ISIN ou Ticker)": ["FR0010148981", "BTC-USD", "AAPL"],
            "Quantité possédée": [5.5, 0.25, 10.0],
            "Prix d'achat moyen (€/$)": [2500.0, 40000.0, 150.0]
        })
    
    # L'éditeur de tableau, qui met à jour l'application instantanément quand on modifie une case
    edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True)
    st.session_state.portfolio = edited_df
    
    # CALCUL AUTOMATIQUE SANS BOUTON
    result_data = []
    total_investi = 0
    total_actuel = 0
    
    for index, row in edited_df.iterrows():
        ticker_input = str(row["Nom du placement (ISIN ou Ticker)"])
        try:
            qty = float(row["Quantité possédée"])
            pru = float(row["Prix d'achat moyen (€/$)"])
            if pd.isna(qty) or pd.isna(pru): continue # Sécurité si case vide
        except:
            continue
        
        if ticker_input and ticker_input != "nan" and qty > 0:
            prix_actuel, vrai_ticker = get_live_price(ticker_input)
            
            valeur_achat = qty * pru
            valeur_live = qty * prix_actuel
            plus_value = valeur_live - valeur_achat
            performance = (plus_value / valeur_achat * 100) if valeur_achat > 0 else 0
            
            total_investi += valeur_achat
            total_actuel += valeur_live
            
            result_data.append({
                "Actif": vrai_ticker,
                "Quantité": qty,
                "Prix d'Achat": round(pru, 2),
                "Cours Actuel": round(prix_actuel, 2),
                "Montant Investi": round(valeur_achat, 2),
                "Valeur Aujourd'hui": round(valeur_live, 2),
                "Gain / Perte (€)": round(plus_value, 2),
                "Évolution (%)": round(performance, 2)
            })
    
    # Affichage des résultats s'il y en a
    if result_data:
        st.subheader("Bilan Actualisé en Temps Réel")
        res_df = pd.DataFrame(result_data)
        st.dataframe(res_df.style.map(lambda x: 'color: #00FF00' if x > 0 else 'color: #FF4B4B', subset=['Gain / Perte (€)', 'Évolution (%)']), use_container_width=True)
        
        pnl_global = total_actuel - total_investi
        perf_globale = (pnl_global / total_investi * 100) if total_investi > 0 else 0
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Montant Total Investi", f"{total_investi:,.2f} €".replace(',', ' '))
        c2.metric("Valeur de votre Portefeuille", f"{total_actuel:,.2f} €".replace(',', ' '))
        c3.metric("Plus-Value / Moins-Value", f"{pnl_global:,.2f} €", f"{perf_globale:.2f} %")
        
        # Lignes pour le PDF
        lignes_pdf_pos = []
        for item in result_data:
            lignes_pdf_pos.append(f"- {item['Actif']} : {item['Quantité']} unites achetees a {item['Prix d\'Achat']} EUR => Valeur Ajd: {item['Valeur Aujourd\'hui']} EUR (Perf: {item['Évolution (%)']}%)")
        
        sections_pdf = [
            ("Details des Positions", lignes_pdf_pos),
            ("Bilan de Performance Global", [
                f"- Total de l'argent investi : {total_investi:,.2f} EUR",
                f"- Valeur du portefeuille aujourd'hui : {total_actuel:,.2f} EUR",
                "",
                f"=> GAIN / PERTE GLOBALE : {pnl_global:,.2f} EUR ({perf_globale:.2f} %)"
            ])
        ]
        generer_pdf_premium("Suivi des Investissements", sections_pdf, "Cockpit_Placements")

# ==========================================
# MODULE 4 : INDÉPENDANCE FINANCIÈRE (FIRE)
# ==========================================
elif menu == "4. Liberté Financière (FIRE)":
    st.title("⏳ Simulateur de Liberté Financière")
    st.write("Calculez à quel âge vous pourrez arrêter de travailler grâce à vos investissements (Mouvement F.I.R.E).")
    
    c1, c2, c3, c4 = st.columns(4)
    age_actuel = c1.number_input("Votre âge actuel", value=30, step=1)
    capital_init = c2.number_input("Capital déjà investi (€)", value=25000, step=1000)
    versement = c3.number_input("Capacité d'épargne (Mensuelle)", value=600, step=50)
    rente_visee = c4.number_input("Rente mensuelle souhaitée", value=2500, step=100)
    
    taux_brut = st.slider("Rendement moyen de vos placements (%)", 2.0, 10.0, 5.0, step=0.5)
    
    # Capital cible pour la Règle des 4%
    capital_cible = (rente_visee * 12) * 25
    
    taux_mensuel = (taux_brut / 100) / 12
    cap = capital_init
    mois_ecoules = 0
    historique_fire = [cap]
    
    while cap < capital_cible and mois_ecoules < (60 * 12): 
        cap = cap * (1 + taux_mensuel) + versement
        mois_ecoules += 1
        if mois_ecoules % 12 == 0:
            historique_fire.append(cap)
            
    annees_necessaires = mois_ecoules / 12
    age_fire = age_actuel + annees_necessaires
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Objectif de Capital", f"{capital_cible:,.0f} €".replace(',', ' '))
    r2.metric("Années d'épargne requises", f"{annees_necessaires:.1f} ans")
    r3.metric("Âge de la Retraite Anticipée", f"{age_fire:.1f} ans", delta="Indépendance totale", delta_color="normal")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(age_actuel, age_actuel + len(historique_fire)), y=historique_fire, fill='tozeroy', name="Capital accumulé", line_color='#B5A27B'))
    fig.add_hline(y=capital_cible, line_dash="dash", line_color="green", annotation_text="Objectif Atteint")
    fig.update_layout(title="Trajectoire vers la Liberté", xaxis_title="Votre Âge", yaxis_title="Patrimoine Placé (€)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Hypotheses de base", [
            f"- Age de depart : {age_actuel} ans",
            f"- Capital de depart deja investi : {capital_init:,.0f} EUR",
            f"- Epargne mensuelle continue : {versement:,.0f} EUR",
            f"- Rente cible souhaitee : {rente_visee:,.0f} EUR / mois",
            f"- Hypothese de rendement annuel : {taux_brut} %"
        ]),
        ("La Projection", [
            f"- Capital necessaire pour generer la rente : {capital_cible:,.0f} EUR",
            f"- Duree de la phase de capitalisation : {annees_necessaires:.1f} annees",
            "",
            f"=> AGE DE LA LIBERTE FINANCIERE : {age_fire:.1f} ans"
        ])
    ]
    generer_pdf_premium("Bilan d'Independance Financiere", sections_pdf, "Cockpit_FIRE")
