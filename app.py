import streamlit as st
from datetime import datetime
import pandas as pd
import os
import json
from fpdf import FPDF

# Fichier de base de données (CSV)
DB_FILE = "rapports_les_palmiers.csv"

# Fonction intelligente : Gère les ajouts de rapports ET les modifications de doublons
def sauvegarder_rapport(donnees):
    nouveau_df = pd.DataFrame([donnees])
    
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            
            # Vérification : existe-t-il déjà un rapport pour cette date et ce shift ?
            if not df.empty and 'Date' in df.columns and 'Shift' in df.columns:
                doublon_index = df[(df['Date'] == donnees['Date']) & (df['Shift'] == donnees['Shift'])].index
                if not doublon_index.empty:
                    df = df.drop(doublon_index)
            
            # Fusion propre des lignes
            df = pd.concat([df, nouveau_df], ignore_index=True, sort=False)
        except Exception:
            df = nouveau_df
    else:
        df = nouveau_df
        
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# Fonction pour nettoyer les textes (supprime les "nan" et gère les accents pour FPDF)
def clean_txt(valeur):
    if pd.isna(valeur) or str(valeur).strip().lower() == "nan" or str(valeur).strip() == "":
        return "Aucune"
    return str(valeur).encode('latin-1', 'replace').decode('latin-1')

# Fonction pour décoder proprement le JSON stocké dans le CSV
def safe_load_json(valeur):
    if pd.isna(valeur) or str(valeur).strip() == "" or str(valeur).strip().lower() == "nan":
        return []
    try:
        return json.loads(valeur)
    except:
        import ast
        try:
            return ast.literal_eval(valeur)
        except:
            return []

# Fonction pour générer le PDF propre
def generer_pdf(row, date_texte, shift, espaces_liste):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # --- EN-TÊTE ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, clean_txt("LES PALMIERS BOUTIQUE HOTEL & SPA"), ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 10, clean_txt(f"Rapport de Shift - {shift}"), ln=True, align="C")
    pdf.cell(0, 5, clean_txt(f"Date : {date_texte}"), ln=True, align="C")
    pdf.ln(10)
    
    # --- RÉSUMÉ DES OPÉRATIONS ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, clean_txt("1. Résumé des Opérations"), ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(70, 6, clean_txt(f"- Chambres occupées : {int(row.get('Chambres_Occupees', 0))}"), ln=False)
    pdf.cell(70, 6, clean_txt(f"- Chambres VIP : {int(row.get('VIP', 0))}"), ln=True)
    
    if shift == "MATIN":
        pdf.cell(70, 6, clean_txt(f"- Arrivées prévues : {int(row.get('Arrivees_Prevues', 0))}"), ln=False)
        pdf.cell(70, 6, clean_txt(f"- Départs prévus : {int(row.get('Departs_Prevus', 0))}"), ln=True)
    else:
        pdf.cell(70, 6, clean_txt(f"- Late Check-in : {int(row.get('Late_Check_In', 0))}"), ln=False)
        pdf.cell(70, 6, clean_txt(f"- Départs tardifs : {int(row.get('Departs_Tardifs', 0))}"), ln=True)
        
    pdf.cell(70, 6, clean_txt(f"- Incidents techniques : {int(row.get('Incidents_Techniques', 0))}"), ln=True)
    pdf.ln(6)
    
    # --- RÉCLAMATIONS CLIENTS ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, clean_txt("2. Réclamations Clients"), ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    
    liste_rec = safe_load_json(row.get('Reclamations_Detail', '[]'))
        
    if liste_rec and len(liste_rec) > 0:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(20, 6, clean_txt("Heure"), border=1, align="C")
        pdf.cell(35, 6, clean_txt("Chambre / Client"), border=1)
        pdf.cell(60, 6, clean_txt("Sujet"), border=1)
        pdf.cell(65, 6, clean_txt("Action prise"), border=1, ln=True)
        
        pdf.set_font("Helvetica", "", 9)
        for rec in liste_rec:
            pdf.cell(20, 6, clean_txt(rec.get('Heure','')), border=1, align="C")
            pdf.cell(35, 6, clean_txt(rec.get('Chambre',''))[:20], border=1)
            pdf.cell(60, 6, clean_txt(rec.get('Sujet',''))[:35], border=1)
            pdf.cell(65, 6, clean_txt(rec.get('Action',''))[:38], border=1, ln=True)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune réclamation sur ce shift."), ln=True)
    pdf.ln(6)
    
    # --- PRIORITÉS TRANSMISES ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, clean_txt("3. Priorités Transmises"), ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    
    liste_prio = safe_load_json(row.get('Priorites_Liste', '[]'))
        
    if liste_prio and len(liste_prio) > 0:
        pdf.set_font("Helvetica", "", 10)
        for idx, p in enumerate(liste_prio, 1):
            pdf.multi_cell(0, 6, clean_txt(f"{idx}. {p}"))
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune priorité spécifique enregistrée."), ln=True)
    pdf.ln(6)
    
    # --- NOTES MANAGER ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, clean_txt("4. Notes du Manager"), ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    
    notes = row.get('Notes_Manager', '')
    if pd.isna(notes) or str(notes).strip() == "" or str(notes).strip().lower() == "nan":
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune observation générale rédigée."), ln=True)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, clean_txt(notes))
    pdf.ln(6)
    
    # --- ÉTAT DES ESPACES ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, clean_txt("5. Suivi des Espaces Communs"), ln=True)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 6, clean_txt("Espace"), border=1)
    pdf.cell(20, 6, clean_txt("État"), border=1, align="C")
    pdf.cell(60, 6, clean_txt("Observations"), border=1)
    pdf.cell(55, 6, clean_txt("Intervention"), border=1, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    for esp in espaces_liste:
        pdf.cell(45, 6, clean_txt(esp), border=1)
        
        raw_etat = row.get(f"{esp}_Etat", "OK")
        etat_val = "Alerte" if str(raw_etat).strip().lower() == "alerte" else "OK"
        
        if etat_val == "Alerte":
            pdf.set_text_color(231, 76, 60)
        else:
            pdf.set_text_color(46, 204, 113)
            
        pdf.cell(20, 6, clean_txt(etat_val), border=1, align="C")
        pdf.set_text_color(0, 0, 0)
        
        obs_val = clean_txt(row.get(f"{esp}_Observations", "Aucune"))
        interv_val = clean_txt(row.get(f"{esp}_Intervention", "Aucune"))
        
        pdf.cell(60, 6, obs_val[:35], border=1)
        pdf.cell(55, 6, interv_val[:32], border=1, ln=True)
        
    return pdf.output()

# --- CONFIGURATION DE PAGE CORRIGÉE AVEC LOGO.PNG ---
st.set_page_config(
    page_title="Les Palmiers - Rapports", 
    page_icon="logo.png", 
    layout="centered"
)

# CSS pour masquer le header (Fork/GitHub), le menu principal et le footer
masquer_interface_cloud = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stDecoration"] {display: none;}
            </style>
            """
st.markdown(masquer_interface_cloud, unsafe_allow_html=True)

st.title("Les Palmiers Boutique Hotel & Spa")
st.markdown("---")

page = st.sidebar.radio("Navigation", ["✍️ Saisir un Rapport", "📋 Consulter les Rapports"])

# Initialisation persistante du Session State pour les listes dynamiques
if 'reclamations_matin' not in st.session_state:
    st.session_state.reclamations_matin = []
if 'reclamations_soir' not in st.session_state:
    st.session_state.reclamations_soir = []
if 'priorites_matin' not in st.session_state:
    st.session_state.priorites_matin = []
if 'priorites_soir' not in st.session_state:
    st.session_state.priorites_soir = []

espaces = [
    "Entrée / Réception", "Piscine 1", "Piscine 2", "Restaurant", 
    "Salle de Sport", "Spa", "Restaurant Noir", "Vestiaire Piscine", "Cuisine"
]

# ==========================================
# PAGE 1 : SAISIR UN RAPPORT
# ==========================================
if page == "✍️ Saisir un Rapport":
    shift = st.sidebar.radio("Sélectionnez le Shift", ["☀️ Shift MATIN", "🌙 Shift SOIR"])
    
    # Sélection de la date à la saisie pour plus de flexibilité
    date_selectionnee = st.sidebar.date_input("📅 Date du Rapport", value=datetime.now().date())
    date_rapport_str = date_selectionnee.strftime("%Y-%m-%d")

    if shift == "☀️ Shift MATIN":
        st.header(f"☀️ Morning Shift Manager Report — {date_selectionnee.strftime('%d/%m/%Y')}")
        st.subheader("Opérations du Jour")
        col1, col2 = st.columns(2)
        with col1:
            chambres_occ = st.number_input("Chambres occupées", min_value=0, value=0, key="m_occ_input")
            arrivees = st.number_input("Arrivées prévues", min_value=0, value=0, key="m_arr_input")
            departs = st.number_input("Départs prévus", min_value=0, value=0, key="m_dep_input")
        with col2:
            vip = st.number_input("Chambres VIP", min_value=0, value=0, key="m_vip_input")
            incidents = st.number_input("Incidents techniques", min_value=0, value=0, key="m_inc_input")

        st.markdown("---")
        st.subheader("SUIVI DES ESPACES")
        etat_espaces_matin = {}
        for espace in espaces:
            st.write(f"**{espace}**")
            c1, c2, c3 = st.columns([1.5, 2.5, 2.5])
            with c1:
                etat = st.selectbox("État", ["OK", "Alerte"], key=f"matin_etat_{espace}")
            with c2:
                obs = st.text_input("Observations", placeholder="RAS", key=f"matin_obs_{espace}")
            with c3:
                interv = st.text_input("Intervention nécessaire", placeholder="Aucune", key=f"matin_int_{espace}")
            
            etat_espaces_matin[f"{espace}_Etat"] = etat
            etat_espaces_matin[f"{espace}_Observations"] = obs if obs.strip() != "" else "Aucune"
            etat_espaces_matin[f"{espace}_Intervention"] = interv if interv.strip() != "" else "Aucune"
            st.markdown("<hr style='margin:0.5em 0px;', size='1'>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("RÉCLAMATIONS CLIENTS")
        
        with st.form("form_rec_matin", clear_on_submit=True):
            rc1, rc2, rc3, rc4 = st.columns([1, 1.5, 2.5, 2.5])
            rm_heure = rc1.text_input("Heure", placeholder="10h00")
            rm_chambre = rc2.text_input("Chambre / Client", placeholder="Ch 2")
            rm_sujet = rc3.text_input("Sujet", placeholder="Problème Wi-Fi")
            rm_action = rc4.text_input("Action prise", placeholder="Répéteur relancé")
            submit_rec_m = st.form_submit_button("➕ Ajouter la réclamation (Matin)", use_container_width=True)
            
            if submit_rec_m:
                if rm_chambre or rm_sujet:
                    st.session_state.reclamations_matin.append({
                        "Heure": rm_heure if rm_heure else "--h--", 
                        "Chambre": rm_chambre if rm_chambre else "Inconnu", 
                        "Sujet": rm_sujet if rm_sujet else "Non spécifié", 
                        "Action": rm_action if rm_action else "Aucune"
                    })
                st.rerun()
                
        if st.session_state.reclamations_matin:
            st.table(pd.DataFrame(st.session_state.reclamations_matin))
            if st.button("❌ Effacer la liste des réclamations (Matin)", key="btn_del_rm"):
                st.session_state.reclamations_matin = []
                st.rerun()

        st.markdown("---")
        st.subheader("PRIORITÉS POUR LE SHIFT SOIR")
        with st.form("form_prio_matin", clear_on_submit=True):
            nouvelle_prio_m = st.text_input("Rédiger une priorité pour le soir...", placeholder="Ex: Donner la clé de la 10...")
            submit_prio_m = st.form_submit_button("➕ Ajouter cette priorité", use_container_width=True)
            
            if submit_prio_m and nouvelle_prio_m:
                st.session_state.priorites_matin.append(nouvelle_prio_m)
                st.rerun()
                
        if st.session_state.priorites_matin:
            for i, prio in enumerate(st.session_state.priorites_matin, 1):
                st.write(f"**{i}.** {prio}")
            if st.button("❌ Effacer les priorités (Matin)", key="btn_del_prio_m"):
                st.session_state.priorites_matin = []
                st.rerun()

        st.markdown("---")
        st.subheader("NOTES MANAGER")
        notes_manager_matin = st.text_area("Observations générales du matin", placeholder="Saisir vos notes ici...", key="nm_text")

        if st.button("💾 Enregistrer le Rapport Matin", use_container_width=True, key="btn_save_matin"):
            donnees_rapport = {
                "Date": date_rapport_str,
                "Shift": "MATIN",
                "Chambres_Occupees": chambres_occ,
                "Arrivees_Prevues": arrivees,
                "Departs_Prevus": departs,
                "VIP": vip,
                "Incidents_Techniques": incidents,
                "Priorites_Liste": json.dumps(st.session_state.priorites_matin),
                "Notes_Manager": notes_manager_matin if notes_manager_matin.strip() != "" else "Aucune",
                "Reclamations_Detail": json.dumps(st.session_state.reclamations_matin)
            }
            donnees_rapport.update(etat_espaces_matin)
            sauvegarder_rapport(donnees_rapport)
            st.success("🎉 Le rapport du matin a été enregistré / mis à jour avec succès !")
            
            st.session_state.reclamations_matin = []
            st.session_state.priorites_matin = []
            st.rerun()

    elif shift == "🌙 Shift SOIR":
        st.header(f"🌙 Evening Shift Manager Report — {date_selectionnee.strftime('%d/%m/%Y')}")
        if os.path.exists(DB_FILE):
            try:
                df = pd.read_csv(DB_FILE)
                rapport_matin = df[(df['Date'] == date_rapport_str) & (df['Shift'] == 'MATIN')]
                if not rapport_matin.empty:
                    st.warning("⚠️ **Rappel du Shift MATIN :**")
                    st.write(f"• Incidents techniques ce matin : {rapport_matin['Incidents_Techniques'].values[0]}")
                    
                    prio_m_aff = safe_load_json(rapport_matin['Priorites_Liste'].values[0])
                    if prio_m_aff:
                        for idx, p in enumerate(prio_m_aff, 1):
                            st.write(f"   {idx}. {p}")
                    else:
                        st.write("• Aucune priorité transmise.")
            except:
                pass
        
        st.markdown("---")
        st.subheader("RÉSUMÉ DU SOIR")
        col1, col2 = st.columns(2)
        with col1:
            s_chambres_occ = st.number_input("Chambres occupées", min_value=0, value=0, key="s_occ")
            s_late_check = st.number_input("Late Check-in", min_value=0, value=0, key="s_late")
            s_departs_tardifs = st.number_input("Départs tardifs", min_value=0, value=0, key="s_dep_t")
        with col2:
            s_vip = st.number_input("Chambres VIP", min_value=0, value=0, key="s_vip")
            s_incidents = st.number_input("Incidents techniques", min_value=0, value=0, key="s_inc")

        st.markdown("---")
        st.subheader("SUIVI DES ESPACES")
        etat_espaces_soir = {}
        for espace in espaces:
            st.write(f"**{espace}**")
            c1, c2, c3 = st.columns([1.5, 2.5, 2.5])
            with c1:
                etat = st.selectbox("État", ["OK", "Alerte"], key=f"soir_etat_{espace}")
            with c2:
                obs = st.text_input("Observations", placeholder="RAS", key=f"soir_obs_{espace}")
            with c3:
                interv = st.text_input("Intervention nécessaire", placeholder="Aucune", key=f"soir_int_{espace}")
            
            etat_espaces_soir[f"{espace}_Etat"] = etat
            etat_espaces_soir[f"{espace}_Observations"] = obs if obs.strip() != "" else "Aucune"
            etat_espaces_soir[f"{espace}_Intervention"] = interv if interv.strip() != "" else "Aucune"
            st.markdown("<hr style='margin:0.5em 0px;', size='1'>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("RÉCLAMATIONS CLIENTS")
        with st.form("form_rec_soir", clear_on_submit=True):
            rc1, rc2, rc3, rc4 = st.columns([1, 1.5, 2.5, 2.5])
            r_heure = rc1.text_input("Heure", placeholder="20h30")
            r_chambre = rc2.text_input("Chambre / Client", placeholder="Ch 1")
            r_sujet = rc3.text_input("Sujet", placeholder="Pas d'eau chaude")
            r_action = rc4.text_input("Action prise", placeholder="Technicien envoyé")
            submit_rec_s = st.form_submit_button("➕ Ajouter la réclamation (Soir)", use_container_width=True)
            
            if submit_rec_s:
                if r_chambre or r_sujet:
                    st.session_state.reclamations_soir.append({
                        "Heure": r_heure if r_heure else "--h--", 
                        "Chambre": r_chambre if r_chambre else "Inconnu", 
                        "Sujet": r_sujet if r_sujet else "Non spécifié", 
                        "Action": r_action if r_action else "Aucune"
                    })
                st.rerun()
        
        if st.session_state.reclamations_soir:
            st.table(pd.DataFrame(st.session_state.reclamations_soir))
            if st.button("❌ Effacer la liste des réclamations (Soir)", key="btn_del_rs"):
                st.session_state.reclamations_soir = []
                st.rerun()

        st.markdown("---")
        st.subheader("PRIORITÉS POUR LA NUIT")
        with st.form("form_prio_soir", clear_on_submit=True):
            nouvelle_prio_s = st.text_input("Rédiger une priorité pour la nuit...", placeholder="Ex: Ronde à faire à 3h du matin...")
            submit_prio_s = st.form_submit_button("➕ Ajouter cette priorité", use_container_width=True)
            
            if submit_prio_s and nouvelle_prio_s:
                st.session_state.priorites_soir.append(nouvelle_prio_s)
                st.rerun()
                
        if st.session_state.priorites_soir:
            for i, prio in enumerate(st.session_state.priorites_soir, 1):
                st.write(f"**{i}.** {prio}")
            if st.button("❌ Effacer les priorités (Soir)", key="btn_del_prio_s"):
                st.session_state.priorites_soir = []
                st.rerun()

        st.markdown("---")
        st.subheader("NOTES MANAGER")
        notes_manager_soir = st.text_area("Observations générales du soir", placeholder="Saisir vos notes ici...", key="ns_text")

        if st.button("💾 Enregistrer le Rapport Soir", use_container_width=True, key="btn_save_soir"):
            donnees_soir = {
                "Date": date_rapport_str,
                "Shift": "SOIR",
                "Chambres_Occupees": s_chambres_occ,
                "Late_Check_In": s_late_check,
                "Departs_Tardifs": s_departs_tardifs,
                "VIP": s_vip,
                "Incidents_Techniques": s_incidents,
                "Priorites_Liste": json.dumps(st.session_state.priorites_soir),
                "Notes_Manager": notes_manager_soir if notes_manager_soir.strip() != "" else "Aucune",
                "Reclamations_Detail": json.dumps(st.session_state.reclamations_soir)
            }
            donnees_soir.update(etat_espaces_soir)
            sauvegarder_rapport(donnees_soir)
            st.success("🎉 Le rapport du soir a été enregistré / mis à jour avec succès !")
            
            st.session_state.reclamations_soir = []
            st.session_state.priorites_soir = []
            st.rerun()

# ==========================================
# PAGE 2 : CONSULTATION ET TÉLÉCHARGEMENT PDF
# ==========================================
elif page == "📋 Consulter les Rapports":
    st.header("📋 Liste des Rapports Enregistrés")
    
    if not os.path.exists(DB_FILE):
        st.info("ℹ️ Aucun rapport n'a été enregistré pour le moment.")
    else:
        df_consult = pd.read_csv(DB_FILE)
        
        if df_consult.empty:
            st.info("ℹ️ Aucun rapport trouvé dans la base de données.")
        else:
            date_aujourdhui_dt = datetime.now().date()
            
            c_date, c_shift = st.columns(2)
            with c_date:
                date_selectionnee_dt = st.date_input("📅 Choisir la Date", value=date_aujourdhui_dt)
                date_choisie = date_selectionnee_dt.strftime("%Y-%m-%d")
                date_fr = date_selectionnee_dt.strftime("%d/%m/%Y")
            
            with c_shift:
                shifts_dispo = df_consult[df_consult['Date'] == date_choisie]['Shift'].unique() if 'Date' in df_consult.columns else []
                if len(shifts_dispo) > 0:
                    shift_choisi = st.selectbox("⏰ Choisir le Shift", shifts_dispo)
                else:
                    shift_choisi = None
            
            if shift_choisi is None:
                st.warning(f"⚠️ Aucun rapport n'a été enregistré à la date du {date_fr}.")
            else:
                rapport_selectionne = df_consult[(df_consult['Date'] == date_choisie) & (df_consult['Shift'] == shift_choisi)]
                
                if not rapport_selectionne.empty:
                    st.markdown("---")
                    st.success(f"### 📄 Rapport du {date_fr} — Shift {shift_choisi}")
                    
                    st.subheader("📊 Résumé des Opérations")
                    row = rapport_selectionne.iloc[0]
                    
                    if shift_choisi == "MATIN":
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("Chambres Occ.", int(row.get('Chambres_Occupees', 0)))
                        c2.metric("Chambres VIP", int(row.get('VIP', 0)))
                        c3.metric("Arrivées Prév.", int(row.get('Arrivees_Prevues', 0)))
                        c4.metric("Départs Prév.", int(row.get('Departs_Prevus', 0)))
                        c5.metric("Incidents Tech.", int(row.get('Incidents_Techniques', 0)))
                        
                    elif shift_choisi == "SOIR":
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("Chambres Occ.", int(row.get('Chambres_Occupees', 0)))
                        c2.metric("Chambres VIP", int(row.get('VIP', 0)))
                        c3.metric("Late Check-in", int(row.get('Late_Check_In', 0)))
                        c4.metric("Départs Tard.", int(row.get('Departs_Tardifs', 0)))
                        c5.metric("Incidents Tech.", int(row.get('Incidents_Techniques', 0)))
                    
                    st.subheader("🚨 Réclamations Clients")
                    liste_rec = safe_load_json(row.get('Reclamations_Detail', '[]'))
                    if liste_rec and len(liste_rec) > 0:
                        st.table(pd.DataFrame(liste_rec))
                    else:
                        st.write("✓ Aucune réclamation sur ce shift.")
                    
                    st.subheader("📌 Priorités Transmises")
                    liste_prio = safe_load_json(row.get('Priorites_Liste', '[]'))
                    if liste_prio and len(liste_prio) > 0:
                        for idx, p in enumerate(liste_prio, 1):
                            st.write(f"**{idx}.** {p}")
                    else:
                        st.write("✓ Aucune priorité spécifique enregistrée.")
                    
                    st.subheader("📝 Notes du Manager")
                    notes = row.get('Notes_Manager', '')
                    if pd.isna(notes) or str(notes).strip() == "" or str(notes).strip().lower() == "nan":
                        st.write("*Aucune observation générale rédigée.*")
                    else:
                        st.info(notes)
                        
                    with st.expander("🔍 Voir le détail de l'état des espaces"):
                        espaces_data = []
                        for esp in espaces:
                            espaces_data.append({
                                "Espace": esp,
                                "État": row.get(f"{esp}_Etat", "N/A"),
                                "Observations": "Aucune" if pd.isna(row.get(f"{esp}_Observations")) or str(row.get(f"{esp}_Observations")).strip().lower() == "nan" or str(row.get(f"{esp}_Observations")).strip() == "" else row.get(f"{esp}_Observations"),
                                "Intervention": "Aucune" if pd.isna(row.get(f"{esp}_Intervention")) or str(row.get(f"{esp}_Intervention")).strip().lower() == "nan" or str(row.get(f"{esp}_Intervention")).strip() == "" else row.get(f"{esp}_Intervention")
                            })
                        st.table(pd.DataFrame(espaces_data))
                    
                    st.markdown("---")
                    
                    pdf_data_raw = generer_pdf(row, date_fr, shift_choisi, espaces)
                    pdf_data = bytes(pdf_data_raw) 
                    
                    st.download_button(
                        label="📥 Télécharger le Rapport en PDF",
                        data=pdf_data,
                        file_name=f"Rapport_{shift_choisi}_{date_choisie}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
