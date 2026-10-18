import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Tennis Dataland Pro", layout="centered", page_icon="🎾")

# 2. PARAMÈTRES DANS LA BARRE LATÉRALE
st.sidebar.header("⚙️ Paramètres")
player_a = st.sidebar.text_input("Joueur A", value="Joueur A")
rank_a = st.sidebar.text_input("Classement A", value="N/C")
st.sidebar.markdown("---")
player_b = st.sidebar.text_input("Joueur B", value="Joueur B")
rank_b = st.sidebar.text_input("Classement B", value="N/C")
st.sidebar.markdown("---")
match_date = st.sidebar.date_input("Date match", datetime.now())

# 3. INITIALISATION DES ÉTATS SESSIONS
if 'all_match_summaries' not in st.session_state: st.session_state.all_match_summaries = []
if 'all_points_logs' not in st.session_state: st.session_state.all_points_logs = []
if 'match_data' not in st.session_state: st.session_state.match_data = []
if 'score' not in st.session_state:
    st.session_state.score = {
        "pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0,
        "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False,
        "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None
    }
if 'score_history' not in st.session_state: st.session_state.score_history = []
if 'service_history' not in st.session_state: st.session_state.service_history = []
if 'service_state' not in st.session_state: st.session_state.service_state = "1ère Balle"
if 'pending_event' not in st.session_state: st.session_state.pending_event = None
if not st.session_state.match_data and st.session_state.score["pA_points"] == 0 and st.session_state.score["pA_jeux"] == 0 and len(st.session_state.score["sets_history_A"]) == 0:
    st.session_state.score["serveur_actuel"] = st.sidebar.selectbox("Serveur tirage :", [player_a, player_b])

app_mode = st.sidebar.radio("📍 Mode Écran :", ["🕹️ Arbitrage en Direct", "📊 Statistiques Saison"])
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset Match Courant"):
    st.session_state.match_data, st.session_state.score_history, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.session_state.score = {"pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0, "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False, "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None}
    st.rerun()

if st.sidebar.button("⚠️ Effacer TOUT l'historique de la saison"):
    st.session_state.all_match_summaries, st.session_state.all_points_logs, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.sidebar.success("Historique global vidé !")
    st.rerun()
st.markdown("""
<style>
    .stApp { background-color: #b14d2a !important; }
    
    .sticky-score-wrapper {
        position: fixed !important;
        top: 0 !important; left: 0 !important; right: 0 !important;
        background-color: #b14d2a !important;
        z-index: 99999 !important;
        padding: 5px 8px 0 8px !important;
        margin: 0 !important;
        width: 100vw !important;
    }
    
    .main-control-spacer { margin-top: 145px !important; }
    
    .header-container {
        text-align: center; padding: 4px; margin-bottom: 4px;
        background-color: #0b110b; border-radius: 6px; border: 1px solid #1e2b1e;
    }
    .header-title {
        color: #ffeb3b !important; font-family: sans-serif; font-weight: 900;
        font-size: 15px; text-transform: uppercase; letter-spacing: 1px; margin: 0;
    }
    
    .stWidgetForm label, .stMarkdown p, p, h3, h4 { color: #ffffff !important; font-weight: bold; margin-bottom: 2px; }
    
    .stButton > button, .stButton > button p, .stButton > button span,
    div.btn-srv div.stButton > button, div.btn-blue div.stButton > button, div.btn-red div.stButton > button {
        color: #000000 !important; font-weight: 900 !important; 
        font-size: 11px !important; line-height: 1.1 !important;
        padding: 2px 4px !important; min-height: 34px !important;
        max-height: 36px !important; width: 100% !important;
        border-radius: 5px !important;
    }
    
    .stButton > button:hover { color: #ffffff !important; }
    
    div.btn-srv > div.stButton > button { background-color: #a7f3d0 !important; border: 2px solid #065f46 !important; }
    div.btn-blue > div.stButton > button { background-color: #bfdbfe !important; border: 2px solid #1e40af !important; }
    div.btn-red > div.stButton > button { background-color: #fecaca !important; border: 2px solid #991b1b !important; }
    div.btn-undo > div.stButton > button { background-color: #fef08a !important; border: 2px solid #854d0e !important; min-height: 28px !important; }
    
    .score-banner-box {
        background-color: #0b110b; padding: 6px; border-radius: 6px;
        border: 1px solid #1e2b1e; text-align: center; margin-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)
def alterner_serveur():
    sc = st.session_state.score
    sc["serveur_actuel"] = player_b if sc["serveur_actuel"] == player_a else player_a

def valider_fin_set(winner_set):
    sc = st.session_state.score
    sc["sets_history_A"].append(sc["pA_jeux"])
    sc["sets_history_B"].append(sc["pB_jeux"])
    if winner_set == player_a: sc["pA_sets"] += 1
    else: sc["pB_sets"] += 1
    sc["pA_jeux"], sc["pB_jeux"], sc["pA_points"], sc["pB_points"], sc["in_tiebreak"], sc["pts_servis_tb"] = 0, 0, 0, 0, False, 0

def update_score(winner):
    sc = st.session_state.score
    st.session_state.score_history.append(sc.copy())
    st.session_state.service_history.append(st.session_state.service_state)
    
    if winner == player_a: sc["pA_points"] += 1
    else: sc["pB_points"] += 1
    
    evenement = "Point"
    if sc["in_supertb"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 10 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]; valider_fin_set(player_a); evenement = "🎉 FIN DE MATCH"
        elif sc["pB_points"] >= 10 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]; valider_fin_set(player_b); evenement = "🎉 FIN DE MATCH"
    elif sc["in_tiebreak"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 7 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = 7; sc["pB_jeux"] = 6; valider_fin_set(player_a); alterner_serveur(); evenement = "🎉 SET"
        elif sc["pB_points"] >= 7 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = 6; sc["pB_jeux"] = 7; valider_fin_set(player_b); alterner_serveur(); evenement = "🎉 SET"
    else:
        if sc["pA_points"] >= 4 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "Jeu"
        elif sc["pB_points"] >= 4 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pB_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "Jeu"
        if sc["pA_points"] >= 4 and sc["pB_points"] >= 4 and sc["pA_points"] == sc["pB_points"]: sc["pA_points"], sc["pB_points"] = 3, 3
        if sc["pA_jeux"] == 6 and sc["pB_jeux"] == 6: sc["in_tiebreak"] = True; sc["pts_servis_tb"] = 0
        elif sc["pA_jeux"] >= 6 and (sc["pA_jeux"] - sc["pB_jeux"]) >= 2: valider_fin_set(player_a); evenement = "🎉 SET"
        elif sc["pB_jeux"] >= 6 and (sc["pB_jeux"] - sc["pA_jeux"]) >= 2: valider_fin_set(player_b); evenement = "🎉 SET"
        
    if sc["pA_sets"] == 1 and sc["pB_sets"] == 1 and not sc["in_supertb"]: sc["in_supertb"] = True; sc["pts_servis_tb"] = 0
    return evenement

def get_pts(pa, pb, in_tb, in_stb):
    if in_tb or in_stb: return str(pa), str(pb)
    if pa >= 3 and pb >= 3:
        if pa == pb: return "40", "40"
        return ("Ad", "40") if pa > pb else ("40", "Ad")
    return {0:"0", 1:"15", 2:"30", 3:"40"}.get(pa,"0"), {0:"0", 1:"15", 2:"30", 3:"40"}.get(pb,"0")
sc = st.session_state.score
pt_a, pt_b = get_pts(sc["pA_points"], sc["pB_points"], sc["in_tiebreak"], sc["in_supertb"])
match_termine = sc["pA_sets"] == 2 or sc["pB_sets"] == 2 or sc["abandon_player"] is not None
set_actuel = sc["pA_sets"] + sc["pB_sets"] + 1

# CORRECTION DU SCOREFINAL : Transformation propre des listes Python en texte épuré (ex: 6/1 6/0)
text_score_visuel = ""
for i in range(len(sc["sets_history_A"])):
    text_score_visuel += f" {sc['sets_history_A'][i]}/{sc['sets_history_B'][i]}"

if not match_termine:
    text_score_visuel += f" ({sc['pA_jeux']}/{sc['pB_jeux']})"

if not match_termine and len(st.session_state.match_data) > 0:
    st.sidebar.markdown("---")
    if st.sidebar.button(f"Abandon de {player_a}", key="abandon_a"): sc["abandon_player"] = player_a; st.rerun()
    if st.sidebar.button(f"Abandon de {player_b}", key="abandon_b"): sc["abandon_player"] = player_b; st.rerun()

st.markdown('<div class="sticky-score-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="header-container"><h1 class="header-title">🎾 Tennis Dataland Pro</h1></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="score-banner-box">
    <p style='margin:0; font-size:12px; color:#ffeb3b;'><b>{player_a[:10]}</b> vs <b>{player_b[:10]}</b></p>
    <p style='margin:2px 0; font-size:16px; font-family:monospace;'>
        <span style='color:#cbd5e0;'>{text_score_visuel.strip()}</span>
        <b style='color:#ffeb3b; margin-left:6px;'>{pt_a if not match_termine else 'Fin'} - {pt_b if not match_termine else 'Fin'}</b>
    </p>
    <p style='margin:0; font-size:10px; color:#a0aec0;'>{"Srv : " + sc["serveur_actuel"][:10] + " 🟡" if not match_termine else "🔒 Match Terminé"}</p>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if match_termine:
    winner_officiel = player_b if sc["abandon_player"] == player_a else (player_a if sc["pA_sets"] == 2 or sc["abandon_player"] == player_b else player_b)
    st.sidebar.success(f"🏆 Victoire : {winner_officiel}")

def queue_event(w, p, t, s="N/A"):
    if t in ["Ace", "Double Faute"]: execute_log(w, p, t, s, "- 4 échanges")
    else: st.session_state.pending_event = {"w": w, "p": p, "t": t, "s": s}; st.rerun()

def execute_log(w, p, t, s, rally_length):
    current_service = st.session_state.service_state; evt_msg = update_score(w)
    st.session_state.match_data.append({
        "Date": match_date.strftime("%d/%m/%Y"), "Match": f"{player_a} vs {player_b}", "Gagnant du point": w,
        "Joueur ayant fait l'action/erreur": p, "Type d'action": t, "Côté du coup": s, "Longueur Échange": rally_length,
        "Serveur du point": sc["serveur_actuel"], "Balle de service": current_service, "Événement Match": evt_msg
    })
    st.session_state.service_state = "1ère Balle"; st.session_state.pending_event = None; st.rerun()
st.markdown('<div class="main-control-spacer"></div>', unsafe_allow_html=True)

if app_mode == "🕹️ Arbitrage en Direct":
    if st.session_state.pending_event is not None:
        pe = st.session_state.pending_event
        st.markdown("<p style='text-align:center; font-size:11px; margin:0;'>Frappes Échange :</p>", unsafe_allow_html=True)
        c_r1, c_r2, c_r3 = st.columns(3)
        if c_r1.button("📉 - 4", key="r_s"): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "- 4 échanges")
        if c_r2.button("⚖️ 4-8", key="r_m"): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "4-8 échanges")
        if c_r3.button("🚀 + 8", key="r_l"): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "+ 8 échanges")
        if st.button("❌ Annuler", key="c_p"): st.session_state.pending_event = None; st.rerun()
        
    elif match_termine:
        if st.button("💾 Sauvegarder & Clôturer le match", use_container_width=True, type="primary"):
            df_t = pd.DataFrame(st.session_state.match_data)
            if not df_t.empty:
                if "Type d'action" in df_t.columns:
                    df_t["Type d'action"] = df_t["Type d'action"].replace({"As": "Ace", "Révérend": "Revers"})
                
                tot = max(1, len(df_t))
                v_a_1 = len(df_t[(df_t["Serveur du point"] == player_a) & (df_t["Balle de service"] == "1ère Balle")])
                v_a_2 = len(df_t[(df_t["Serveur du point"] == player_a) & (df_t["Balle de service"] == "2e Balle")])
                v_b_1 = len(df_t[(df_t["Serveur du point"] == player_b) & (df_t["Balle de service"] == "1ère Balle")])
                v_b_2 = len(df_t[(df_t["Serveur du point"] == player_b) & (df_t["Balle de service"] == "2e Balle")])
                
                tot_ue_a = max(1, len(df_t[(df_t["Joueur ayant fait l'action/erreur"] == player_a) & (df_t["Type d'action"] == "Faute Directe")]))
                tot_ue_b = max(1, len(df_t[(df_t["Joueur ayant fait l'action/erreur"] == player_b) & (df_t["Type d'action"] == "Faute Directe")]))

                if sc["abandon_player"] is not None:
                    winner_name = player_b if sc["abandon_player"] == player_a else player_a
                    status_label = f" (Victoire de {winner_name} par abandon de {sc['abandon_player']}) Score: {text_score_visuel.strip()}"
                else:
                    winner_name = player_a if sc["pA_sets"] == 2 else player_b
                    status_label = f" (Victoire de {winner_name}) Score: {text_score_visuel.strip()}"
                
                summary = {
                    "Date": match_date.strftime("%d/%m/%Y"), 
                    "Match": f"{player_a} ({rank_a}) vs {player_b} ({rank_b}){status_label}", 
                    "Total Points": tot,
                    f"Aces % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Ace')]) / tot):.1%}",
                    f"Aces % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Ace')]) / tot):.1%}",
                    f"% 1er Srv In {player_a}": f"{(v_a_1/max(1,v_a_1+v_a_2)):.1%}", 
                    f"% Pts Gagne 1er Srv {player_a}": f"{(len(df_t[(df_t['Serveur du point'] == player_a) & (df_t['Balle de service'] == '1ère Balle') & (df_t['Gagnant du point'] == player_a)])/max(1,v_a_1)):.1%}",
                    f"% Pts Gagne 2nd Srv {player_a}": f"{(len(df_t[(df_t['Serveur du point'] == player_a) & (df_t['Balle de service'] == '2e Balle') & (df_t['Gagnant du point'] == player_a)])/max(1,v_a_2)):.1%}",
                    f"% 1er Srv In {player_b}": f"{(v_b_1/max(1,v_b_1+v_b_2)):.1%}", 
                    f"% Pts Gagne 1er Srv {player_b}": f"{(len(df_t[(df_t['Serveur du point'] == player_b) & (df_t['Balle de service'] == '1ère Balle') & (df_t['Gagnant du point'] == player_b)])/max(1,v_b_1)):.1%}",
                    f"% Pts Gagne 2nd Srv {player_b}": f"{(len(df_t[(df_t['Serveur du point'] == player_b) & (df_t['Balle de service'] == '2e Balle') & (df_t['Gagnant du point'] == player_b)])/max(1,v_b_2)):.1%}",
                    f"CD Winners % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}",
                    f"REV Winners % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"CD Winners % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}",
                    f"REV Winners % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Winner') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"Fautes Directes CD % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot_ue_a):.1%}",
                    f"Fautes Directes REV % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Revers')]) / tot_ue_a):.1%}",
                    f"Fautes Directes CD % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot_ue_b):.1%}",
                    f"Fautes Directes REV % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Directe') & (df_t['Côté du coup'] == 'Revers')]) / tot_ue_b):.1%}",
                    f"F. Provoquées CD % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}",
                    f"F. Provoquées REV % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"F. Provoquées CD % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Coup Droit')]) / tot):.1%}",
                    f"F. Provoquées REV % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Type d\'action'] == 'Faute Provoquée') & (df_t['Côté du coup'] == 'Revers')]) / tot):.1%}",
                    f"Rallyes Courts (-4) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '- 4 échanges')]) / tot):.1%}",
                    f"Rallyes Moyens (4-8) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '4-8 échanges')]) / tot):.1%}",
                    f"Rallyes Longs (+8) % {player_a}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_a) & (df_t['Longueur Échange'] == '+ 8 échanges')]) / tot):.1%}",
                    f"Rallyes Courts (-4) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '- 4 échanges')]) / tot):.1%}",
                    f"Rallyes Moyens (4-8) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '4-8 échanges')]) / tot):.1%}",
                    f"Rallyes Longs (+8) % {player_b}": f"{(len(df_t[(df_t['Joueur ayant fait l\'action/erreur'] == player_b) & (df_t['Longueur Échange'] == '+ 8 échanges')]) / tot):.1%}",
                }
                st.session_state.all_match_summaries.append(summary)
                if st.session_state.match_data: st.session_state.match_data[-1]["Événement Match"] = "🎉 FIN DE MATCH"
                st.session_state.all_points_logs.extend(st.session_state.match_data)
            st.session_state.match_data, st.session_state.score_history, st.session_state.service_state = [], [], "1ère Balle"
            st.session_state.score = {"pA_points":0,"pB_points":0,"pA_jeux":0,"pB_jeux":0,"pA_sets":0,"pB_sets":0,"sets_history_A":[],"sets_history_B":[],"in_tiebreak":False,"in_supertb":False,"serveur_actuel":player_a,"pts_servis_tb":0, "abandon_player":None}
            st.rerun()
    else:
        st.markdown('<div class="btn-srv">', unsafe_allow_html=True)
        cs1, cs2, cs3 = st.columns(3)
        if cs1.button("🔄 2e Srv", disabled=st.session_state.service_state == "2e Balle"): st.session_state.service_state = "2e Balle"; st.rerun()
        if cs2.button("🎯 Ace"): queue_event(sc["serveur_actuel"], sc["serveur_actuel"], "Ace", "Service")
        if cs3.button("❌ DblF"): rc = player_b if sc["serveur_actuel"] == player_a else player_a; queue_event(rc, sc["serveur_actuel"], "Double Faute", "Service")
        st.markdown('</div>', unsafe_allow_html=True)
        
        cpA, cpB = st.columns(2)
        with cpA:
            st.markdown(f'<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔥 CD Gagnant", key="w_cd_a"): queue_event(player_a, player_a, "Winner", "Coup Droit")
            if st.button("🔥 Revers Gagnant", key="w_rev_a"): queue_event(player_a, player_a, "Winner", "Revers")
            if st.button("📉 Faute CD", key="ue_cd_a"): queue_event(player_b, player_a, "Faute Directe", "Coup Droit")
            if st.button("📉 Faute Rev", key="ue_rev_a"): queue_event(player_b, player_a, "Faute Directe", "Revers")
            if st.button("🛡️ F.Prov CD", key="fe_cd_a"): queue_event(player_b, player_a, "Faute Provoquée", "Coup Droit")
            if st.button("🛡️ F.Prov Rev", key="fe_rev_a"): queue_event(player_b, player_a, "Faute Provoquée", "Revers")
            st.markdown('</div>', unsafe_allow_html=True)
        with cpB:
            st.markdown(f'<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 CD Gagnant ", key="w_cd_b"): queue_event(player_b, player_b, "Winner", "Coup Droit")
            if st.button("🔥 Revers Gagnant ", key="w_rev_b"): queue_event(player_b, player_b, "Winner", "Revers")
            if st.button("📉 Faute CD ", key="ue_cd_b"): queue_event(player_a, player_b, "Faute Directe", "Coup Droit")
            if st.button("📉 Faute Rev ", key="ue_rev_b"): queue_event(player_a, player_b, "Faute Directe", "Revers")
            if st.button("🛡️ F.Prov CD ", key="fe_cd_b"): queue_event(player_a, player_b, "Faute Provoquée", "Coup Droit")
            if st.button("🛡️ F.Prov Rev ", key="fe_rev_b"): queue_event(player_a, player_b, "Faute Provoquée", "Revers")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
        if st.button("↩️ Annuler le dernier coup", disabled=not st.session_state.match_data): undo_last_point()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<div style='margin:4px 0;'></div>", unsafe_allow_html=True)
        c_abd1, c_abd2 = st.columns(2)
        with c_abd1:
            st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
            if st.button(f"🤕 Ab. {player_a[:8]}", key="sidebar_abd_a"): sc["abandon_player"] = player_a; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_abd2:
            st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
            if st.button(f"🤕 Ab. {player_b[:8]}", key="sidebar_abd_b"): sc["abandon_player"] = player_b; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    df = pd.DataFrame(st.session_state.match_data)
    df_active = df if not df.empty else pd.DataFrame(st.session_state.all_points_logs)
    
    if not df_active.empty and "Type d'action" in df_active.columns:
        df_active["Type d'action"] = df_active["Type d'action"].replace({"As": "Ace", "Révérend": "Revers"})
    
    if not df_active.empty:
        def calc_radar(p, t, c): return len(df_active[(df_active["Joueur ayant fait l'action/erreur"] == p) & (df_active["Type d'action"] == t) & (df_active["Côté du coup"] == c)])
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[calc_radar(player_a,"Winner","Coup Droit"), calc_radar(player_a,"Winner","Revers"), calc_radar(player_a,"Faute Directe","Coup Droit"), calc_radar(player_a,"Faute Directe","Revers")], theta=['Win CD','Win REV','Faute CD','Faute REV'], fill='toself', name=player_a, line_color="#3b82f6"))
        fig.add_trace(go.Scatterpolar(r=[calc_radar(player_b,"Winner","Coup Droit"), calc_radar(player_b,"Winner","Revers"), calc_radar(player_b,"Faute Directe","Coup Droit"), calc_radar(player_b,"Faute Directe","Revers")], theta=['Win CD','Win REV','Faute CD','Faute REV'], fill='toself', name=player_b, line_color="#ef4444"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False)), paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        
    if not st.session_state.all_match_summaries: st.info("Aucun match archivé.")
    else:
        df_gs = pd.DataFrame(st.session_state.all_match_summaries)
        df_gp = pd.DataFrame(st.session_state.all_points_logs)
        if not df_gp.empty and "Type d'action" in df_gp.columns:
            df_gp["Type d'action"] = df_gp["Type d'action"].replace({"As": "Ace", "Révérend": "Revers"})
            
        st.dataframe(df_gs, use_container_width=True, hide_index=True)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_gs.to_excel(writer, sheet_name='Efficacite Service Saison', index=False)
            df_gp.to_excel(writer, sheet_name='Historique Detaille Points', index=False)
            workbook = writer.book; from openpyxl.styles import PatternFill, Border, Side
            fA, fB, fE = PatternFill(start_color="E6F0FA", fill_type="solid"), PatternFill(start_color="FCE8E6", fill_type="solid"), PatternFill(start_color="C3E6CB", fill_type="solid")
            ts = Side(style='thin', color='CBD5E1'); db = Border(bottom=Side(style='double', color='155724')); sb = Border(left=ts, right=ts, top=ts, bottom=ts)
            
            ws_s = writer.sheets['Efficacite Service Saison']
            for r in range(2, len(df_gs) + 2):
                for c in range(1, len(df_gs.columns) + 1):
                    cell = ws_s.cell(row=r, column=c); cell.border = sb; h_name = ws_s.cell(row=1, column=c).value
                    if h_name and player_a in str(h_name): cell.fill = fA
                    elif h_name and player_b in str(h_name): cell.fill = fB
            
            ws_p = writer.sheets['Historique Detaille Points']
            for r in range(2, len(df_gp) + 2):
                is_f = any("FIN DE MATCH" in str(ws_p.cell(row=r, column=c).value).upper() for c in range(1, len(df_gp.columns)+1) if ws_p.cell(row=r, column=c).value)
                act = ws_p.cell(row=r, column=4).value
                for c in range(1, len(df_gp.columns) + 1):
                    cell = ws_p.cell(row=r, column=c); cell.border = sb
                    if is_f: cell.fill = fE; cell.border = db
                    elif act == player_a: cell.fill = fA
                    elif act == player_b: cell.fill = fB
        st.download_button(label="📥 Télécharger (.xlsx)", data=excel_buffer.getvalue(), file_name="bilan_tennis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
