"""
Business Modeling Studio — POC
Baseado em: Bridgeland & Zahavi (2009) + OMG Standards (BMM, BPMN 2.0, SBVR, DMN)
"""
import streamlit as st
import json
import uuid
from datetime import date, datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from auth import require_auth, render_user_bar, get_permission

# ─────────────────────────────────────────────
# CONFIGURAÇÃO INICIAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Business Modeling Studio",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── AUTENTICAÇÃO — bloqueia tudo abaixo se não logado ────────────
require_auth()

# ─────────────────────────────────────────────
# ESTADO GLOBAL (Session State)
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "company_name": "",
        "vision": "",
        "mission": "",
        "goals": [],
        "objectives": [],
        "strategies": [],
        "influencers": [],
        "processes": [],
        "activities": [],
        "actors": [],
        "raci": [],
        "rules": [],
        "decision_tables": [],
        "glossary": [],
        "active_module": "home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def new_id():
    return str(uuid.uuid4())[:8]

def get_completeness():
    """Calcula Business Model Completeness Score (0-100)"""
    scores = {
        "Motivação": 0,
        "Processos": 0,
        "Organização": 0,
        "Regras": 0,
    }
    # Motivação (25 pts)
    if st.session_state.vision: scores["Motivação"] += 5
    if st.session_state.mission: scores["Motivação"] += 5
    if st.session_state.goals: scores["Motivação"] += 8
    if st.session_state.strategies: scores["Motivação"] += 7

    # Processos (25 pts)
    if st.session_state.processes: scores["Processos"] += 10
    if st.session_state.activities: scores["Processos"] += 15

    # Organização (25 pts)
    if st.session_state.actors: scores["Organização"] += 12
    if st.session_state.raci: scores["Organização"] += 13

    # Regras (25 pts)
    if st.session_state.rules: scores["Regras"] += 12
    if st.session_state.glossary: scores["Regras"] += 8
    if st.session_state.decision_tables: scores["Regras"] += 5

    return scores

def va_ratio():
    activities = st.session_state.activities
    if not activities: return 0, 0, 0
    va = sum(1 for a in activities if a.get("value_type") == "VA")
    nva = sum(1 for a in activities if a.get("value_type") == "NVA")
    bva = sum(1 for a in activities if a.get("value_type") == "BVA")
    return va, nva, bva

# ─────────────────────────────────────────────
# CSS CUSTOMIZADO
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2e6da4 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .module-card {
        background: white;
        border: 2px solid #e0e7ef;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        transition: border-color 0.2s;
    }
    .module-card:hover { border-color: #2e6da4; }
    .kpi-box {
        background: linear-gradient(135deg, #f8faff, #eef4ff);
        border-left: 4px solid #2e6da4;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
    }
    .discipline-tag {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.15rem;
    }
    .tag-motivation { background:#fff3cd; color:#856404; }
    .tag-process { background:#cce5ff; color:#004085; }
    .tag-org { background:#d4edda; color:#155724; }
    .tag-rules { background:#f8d7da; color:#721c24; }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    .score-badge {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2e6da4;
    }
    .sidebar-section {
        background: #f0f4fa;
        border-radius: 8px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — NAVEGAÇÃO
# ─────────────────────────────────────────────
with st.sidebar:
    render_user_bar()   # ← bloco do usuário logado + botão logout
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,400&family=Outfit:wght@300;400;500;600&display=swap');
    </style>
    <div style="padding: 0.3rem 0 1rem;">
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.6rem; font-weight:300; color:#f5f0e8; line-height:1;">
            <span style="color:#c9a84c; font-weight:600; font-style:italic;">b</span>Valor<span style="font-family:'Outfit',sans-serif; font-size:0.45em; color:#4dd9c0; vertical-align:super; font-weight:500;">.ai</span>
        </div>
        <div style="font-size:0.65rem; letter-spacing:2px; text-transform:uppercase; color:rgba(184,200,216,0.35); margin-top:0.2rem;">Business Modeling Studio</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    company = st.text_input("🏢 Empresa", value=st.session_state.company_name, key="co_input")
    if company != st.session_state.company_name:
        st.session_state.company_name = company

    st.divider()
    st.markdown("### Módulos")
    nav_items = [
        ("🏠", "home", "Dashboard"),
        ("🎯", "motivation", "1. Motivação (BMM)"),
        ("⚙️", "process", "2. Processos (BPMN)"),
        ("👥", "organization", "3. Organização"),
        ("📋", "rules", "4. Regras (SBVR/DMN)"),
        ("📊", "dashboard", "5. Value Dashboard"),
        ("🔗", "traceability", "6. Rastreabilidade"),
    ]
    for icon, key, label in nav_items:
        if st.button(f"{icon} {label}", use_container_width=True,
                     type="primary" if st.session_state.active_module == key else "secondary"):
            st.session_state.active_module = key
            st.rerun()

    st.divider()
    # Quick stats
    scores = get_completeness()
    total = sum(scores.values())
    st.markdown(f"**Completude:** `{total:.0f}/100`")
    st.progress(total / 100)
    st.caption("Baseado em: Bridgeland & Zahavi (2009)")

# ─────────────────────────────────────────────
# HOME — PÁGINA INICIAL
# ─────────────────────────────────────────────
if st.session_state.active_module == "home":
    name = st.session_state.company_name or "sua empresa"
    st.markdown(f"""
    <div class="main-header">
        <h1>🏗️ Business Modeling Studio</h1>
        <p style="margin:0; opacity:0.9">Modelagem de Negócios para Realização de Valor — {name}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### O que é Business Modeling?
    Segundo **Bridgeland & Zahavi (2009)**, business modeling é a arte de criar representações
    simplificadas de uma organização usando **quatro disciplinas complementares**:
    """)

    col1, col2, col3, col4 = st.columns(4)
    disciplines = [
        (col1, "🎯", "Motivação", "BMM v1.3", "Por quê? — Visão, Missão, Metas, Estratégias", "#fff3cd", "#856404"),
        (col2, "⚙️", "Processos", "BPMN 2.0.2", "Como? — Atividades, fluxos, swimlanes", "#cce5ff", "#004085"),
        (col3, "👥", "Organização", "ArchiMate 3.2", "Quem? — Atores, papéis, RACI", "#d4edda", "#155724"),
        (col4, "📋", "Regras", "SBVR/DMN 1.5", "O quê? — Políticas, decisões, vocabulário", "#f8d7da", "#721c24"),
    ]
    for col, icon, title, std, desc, bg, fg in disciplines:
        with col:
            st.markdown(f"""
            <div style="background:{bg}; color:{fg}; border-radius:12px; padding:1rem; height:180px;">
                <div style="font-size:2rem;">{icon}</div>
                <h4 style="margin:0.3rem 0;">{title}</h4>
                <small><b>{std}</b></small>
                <p style="font-size:0.85rem; margin-top:0.5rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📈 Status do Modelo de Negócio")
    scores = get_completeness()
    total = sum(scores.values())

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div style="text-align:center; padding:2rem; background:#f0f7ff; border-radius:12px;">
            <div class="score-badge">{total:.0f}</div>
            <div style="color:#666;">/ 100 pontos</div>
            <div style="margin-top:0.5rem; font-weight:600; color:#2e6da4;">
            {"🟢 Avançado" if total>=75 else "🟡 Em desenvolvimento" if total>=40 else "🔴 Inicial"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        fig = go.Figure(go.Bar(
            x=list(scores.values()),
            y=list(scores.keys()),
            orientation='h',
            marker_color=['#ffc107','#0d6efd','#198754','#dc3545'],
            text=[f"{v}/25" for v in scores.values()],
            textposition='inside',
        ))
        fig.update_layout(
            height=200, margin=dict(l=0,r=0,t=10,b=10),
            xaxis_range=[0,25], xaxis_title="Pontos",
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 🚀 Por onde começar?")
    st.info("""
    **Fluxo recomendado** (Bridgeland & Zahavi, Cap. 7-9):
    1. **Motivação** — Defina Visão, Missão, Metas e Estratégias
    2. **Processos** — Mapeie como o negócio opera (BPMN 2.0)
    3. **Organização** — Defina quem faz o quê (RACI)
    4. **Regras** — Documente políticas e decisões (SBVR/DMN)
    5. **Dashboard** — Analise a realização de valor
    """)

    st.caption("📚 Referências: BMM v1.3 | BPMN 2.0.2 | SBVR v1.5 | DMN 1.5 | ArchiMate 3.2 | APQC PCF v7.3")

# ─────────────────────────────────────────────
# MÓDULO 1 — MOTIVAÇÃO (BMM)
# ─────────────────────────────────────────────
elif st.session_state.active_module == "motivation":
    st.markdown("""
    <div class="main-header">
        <h2>🎯 Módulo 1: Business Motivation Model</h2>
        <p style="margin:0; opacity:0.9">OMG BMM v1.3 — Visão, Missão, Metas, Estratégias, Influenciadores</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔭 Visão & Missão", "🎯 Metas & Objetivos", "🗺️ Estratégias & Táticas", "🌍 Influenciadores"])

    with tab1:
        st.markdown("#### 🔭 Visão & Missão")
        st.info("**BMM:** A *Vision* descreve o estado futuro desejado. A *Mission* descreve o que a organização faz para alcançar a visão.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🌟 Visão")
            vision = st.text_area(
                "Declaração de Visão",
                value=st.session_state.vision,
                placeholder="Ex: Ser a empresa de restaurantes mais admirada dos EUA, reconhecida pela experiência gastronômica excepcional.",
                height=120, key="vision_input"
            )
            st.session_state.vision = vision
            if vision:
                words = len(vision.split())
                st.caption(f"✅ {words} palavras — {'Boa concisão' if words<=30 else 'Considere ser mais conciso' if words>50 else 'OK'}")

        with col2:
            st.markdown("##### 🧭 Missão")
            mission = st.text_area(
                "Declaração de Missão",
                value=st.session_state.mission,
                placeholder="Ex: Criar experiências gastronômicas memoráveis em restaurantes de alto padrão, com foco em qualidade, serviço e sustentabilidade.",
                height=120, key="mission_input"
            )
            st.session_state.mission = mission

        if vision and mission:
            st.success("✅ Visão e Missão definidas. Próximo passo: defina as Metas.")
            st.markdown("---")
            st.markdown("##### 📋 Declarações Atuais")
            st.markdown(f"**Visão:** *{vision}*")
            st.markdown(f"**Missão:** *{mission}*")

    with tab2:
        st.markdown("#### 🎯 Metas e Objetivos SMART")
        st.info("**BMM:** *Goals* são estados desejados de longo prazo. *Objectives* são SMART: Específicos, Mensuráveis, Alcançáveis, Relevantes e com Prazo.")

        col_form, col_list = st.columns([1, 1])
        with col_form:
            st.markdown("##### ➕ Adicionar Meta")
            goal_name = st.text_input("Nome da Meta", placeholder="Ex: Crescimento de Receita")
            goal_cat = st.selectbox("Perspectiva (Balanced Scorecard)", 
                                     ["Financeiro", "Cliente", "Processos Internos", "Aprendizado & Crescimento"])
            goal_desc = st.text_area("Descrição", placeholder="Ex: Aumentar receita anual em mercados premium", height=80)
            
            st.markdown("##### 🎯 Objetivo SMART vinculado")
            obj_specific = st.text_input("Específico (o quê?)", placeholder="Aumentar receita de restaurantes flagship")
            obj_measurable = st.text_input("Mensurável (quanto?)", placeholder="Crescimento de 25% em faturamento")
            obj_target = st.number_input("Meta numérica", value=0.0, format="%.1f")
            obj_unit = st.text_input("Unidade", placeholder="% crescimento, R$, NPS...")
            obj_date = st.date_input("Prazo", value=date(2026, 12, 31))

            if get_permission("can_edit") and st.button("✅ Adicionar Meta", type="primary"):
                if goal_name:
                    goal_id = new_id()
                    st.session_state.goals.append({
                        "id": goal_id, "name": goal_name,
                        "category": goal_cat, "description": goal_desc
                    })
                    if obj_specific:
                        st.session_state.objectives.append({
                            "id": new_id(), "goal_id": goal_id,
                            "specific": obj_specific, "measurable": obj_measurable,
                            "target": obj_target, "unit": obj_unit, "deadline": str(obj_date)
                        })
                    st.success(f"Meta '{goal_name}' adicionada!")
                    st.rerun()

        with col_list:
            st.markdown("##### 📊 Metas Definidas")
            cat_colors = {"Financeiro":"🟡","Cliente":"🔵","Processos Internos":"🟢","Aprendizado & Crescimento":"🔴"}
            if st.session_state.goals:
                for g in st.session_state.goals:
                    icon = cat_colors.get(g["category"], "⚪")
                    with st.expander(f"{icon} {g['name']} — {g['category']}"):
                        st.write(g.get("description",""))
                        related_objs = [o for o in st.session_state.objectives if o["goal_id"] == g["id"]]
                        for o in related_objs:
                            st.markdown(f"""
                            <div class="kpi-box">
                                <b>Objetivo SMART:</b> {o['specific']}<br>
                                <b>Meta:</b> {o['target']} {o['unit']} até {o['deadline']}
                            </div>""", unsafe_allow_html=True)
                        if get_permission("can_delete") and st.button(f"🗑️ Remover", key=f"del_goal_{g['id']}"):
                            st.session_state.goals = [x for x in st.session_state.goals if x['id'] != g['id']]
                            st.rerun()
            else:
                st.info("Nenhuma meta definida ainda.")

            # BSC Radar
            if st.session_state.goals:
                cats = ["Financeiro","Cliente","Processos Internos","Aprendizado & Crescimento"]
                counts = [sum(1 for g in st.session_state.goals if g["category"]==c) for c in cats]
                fig = go.Figure(go.Scatterpolar(r=counts, theta=cats, fill='toself',
                    line_color='#2e6da4', fillcolor='rgba(46,109,164,0.2)'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(counts)+1])),
                    showlegend=False, height=250, margin=dict(l=30,r=30,t=30,b=30),
                    title="Distribuição BSC")
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("#### 🗺️ Estratégias & Táticas")
        st.info("**BMM:** *Strategies* são abordagens para alcançar Goals. *Tactics* são ações concretas para implementar Strategies.")

        col_f, col_l = st.columns([1,1])
        with col_f:
            st.markdown("##### ➕ Adicionar Estratégia")
            strat_name = st.text_input("Estratégia", placeholder="Ex: Expansão para mercados premium costeiros")
            strat_type = st.selectbox("Tipo Porter", ["Diferenciação", "Liderança em Custo", "Foco/Nicho"])
            linked_goal = st.selectbox("Meta vinculada", 
                                        ["(nenhuma)"] + [g["name"] for g in st.session_state.goals])
            tactic = st.text_input("Tática associada", placeholder="Ex: Abrir 3 restaurantes em Miami até Q3 2026")

            if st.button("✅ Adicionar Estratégia", type="primary"):
                if strat_name:
                    st.session_state.strategies.append({
                        "id": new_id(), "name": strat_name, "type": strat_type,
                        "goal": linked_goal, "tactic": tactic
                    })
                    st.success("Estratégia adicionada!")
                    st.rerun()

        with col_l:
            st.markdown("##### 🗺️ Estratégias Definidas")
            type_icons = {"Diferenciação":"💎","Liderança em Custo":"💰","Foco/Nicho":"🎯"}
            for s in st.session_state.strategies:
                icon = type_icons.get(s["type"],"📍")
                st.markdown(f"""
                <div class="module-card">
                    <b>{icon} {s['name']}</b><br>
                    <small>Tipo: {s['type']} | Meta: {s['goal']}</small><br>
                    {f"<i>Tática:</i> {s['tactic']}" if s.get('tactic') else ""}
                </div>""", unsafe_allow_html=True)
            if not st.session_state.strategies:
                st.info("Nenhuma estratégia definida.")

    with tab4:
        st.markdown("#### 🌍 Análise de Influenciadores (PESTEL + SWOT)")
        st.info("**BMM:** Influenciadores são fatores externos e internos que afetam as metas e estratégias.")

        col_pestel, col_swot = st.columns(2)
        with col_pestel:
            st.markdown("##### 🔍 PESTEL")
            pestel_cats = ["Político", "Econômico", "Social", "Tecnológico", "Ambiental", "Legal"]
            pestel_factor = st.selectbox("Categoria", pestel_cats)
            pestel_desc = st.text_area("Fator / Influenciador", height=80,
                                        placeholder="Descreva o fator externo...")
            pestel_impact = st.select_slider("Impacto", ["Baixo","Médio","Alto"])

            if st.button("➕ Adicionar Influenciador"):
                if pestel_desc:
                    st.session_state.influencers.append({
                        "id": new_id(), "category": pestel_factor,
                        "description": pestel_desc, "impact": pestel_impact, "type": "PESTEL"
                    })
                    st.rerun()

        with col_swot:
            st.markdown("##### 🎯 SWOT")
            swot_cats = ["Força", "Fraqueza", "Oportunidade", "Ameaça"]
            swot_cat = st.selectbox("Tipo SWOT", swot_cats)
            swot_desc = st.text_area("Descrição", height=80, key="swot_desc")

            if st.button("➕ Adicionar SWOT"):
                if swot_desc:
                    st.session_state.influencers.append({
                        "id": new_id(), "category": swot_cat,
                        "description": swot_desc, "type": "SWOT"
                    })
                    st.rerun()

        # Visualização SWOT matrix
        if st.session_state.influencers:
            swot_items = [i for i in st.session_state.influencers if i["type"] == "SWOT"]
            if swot_items:
                st.markdown("##### 📊 Matriz SWOT")
                swot_map = {"Força":[], "Fraqueza":[], "Oportunidade":[], "Ameaça":[]}
                for i in swot_items:
                    swot_map[i["category"]].append(i["description"])

                s_col, w_col = st.columns(2)
                o_col, t_col = st.columns(2)
                quadrants = [(s_col,"Força","✅","#d4edda"),(w_col,"Fraqueza","⚠️","#fff3cd"),
                             (o_col,"Oportunidade","🚀","#cce5ff"),(t_col,"Ameaça","🚨","#f8d7da")]
                for col, cat, icon, bg in quadrants:
                    with col:
                        items = swot_map[cat]
                        content = "".join([f"• {x}<br>" for x in items]) if items else "<i>Vazio</i>"
                        st.markdown(f"""<div style="background:{bg};border-radius:8px;padding:0.8rem;">
                            <b>{icon} {cat}</b><br>{content}</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MÓDULO 2 — PROCESSOS (BPMN)
# ─────────────────────────────────────────────
elif st.session_state.active_module == "process":
    st.markdown("""
    <div class="main-header">
        <h2>⚙️ Módulo 2: Business Process Model</h2>
        <p style="margin:0; opacity:0.9">BPMN 2.0.2 (ISO/IEC 19510:2013) — Processos, Atividades, Análise de Valor</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Processos", "🔄 Atividades & Fluxo", "📊 Análise de Valor"])

    with tab1:
        st.markdown("#### 📋 Catálogo de Processos")
        st.info("**BPMN 2.0:** Um *Process* é um conjunto de atividades que produz resultado de valor para o cliente. Use *Pools* para organizações e *Lanes* para papéis.")

        col_f, col_l = st.columns([1,1])
        with col_f:
            st.markdown("##### ➕ Novo Processo")
            proc_name = st.text_input("Nome do Processo", placeholder="Ex: Reserva de Mesa")
            proc_type = st.selectbox("Tipo BPMN", ["Process", "Sub-Process", "Call Activity"])
            proc_trigger = st.selectbox("Evento Inicial", ["Cliente solicita", "Timer", "Mensagem recebida", "Manual", "Condicional"])
            proc_goal = st.selectbox("Meta vinculada (BMM)",
                                      ["(nenhuma)"] + [g["name"] for g in st.session_state.goals])
            proc_level = st.selectbox("Nível (APQC PCF)", ["Nível 1 — Categoria", "Nível 2 — Grupo", "Nível 3 — Processo", "Nível 4 — Atividade"])

            if st.button("✅ Adicionar Processo", type="primary"):
                if proc_name:
                    st.session_state.processes.append({
                        "id": new_id(), "name": proc_name, "type": proc_type,
                        "trigger": proc_trigger, "goal": proc_goal, "level": proc_level
                    })
                    st.success(f"Processo '{proc_name}' adicionado!")
                    st.rerun()

        with col_l:
            st.markdown("##### 📋 Processos Mapeados")
            if st.session_state.processes:
                for p in st.session_state.processes:
                    activities_for_proc = [a for a in st.session_state.activities if a.get("process_id") == p["id"]]
                    with st.expander(f"⚙️ {p['name']} ({p['type']})"):
                        st.write(f"**Gatilho:** {p['trigger']} | **Meta:** {p['goal']}")
                        st.write(f"**Nível APQC:** {p['level']}")
                        st.write(f"**Atividades:** {len(activities_for_proc)}")
                        if get_permission("can_delete") and st.button("🗑️ Remover", key=f"del_proc_{p['id']}"):
                            st.session_state.processes = [x for x in st.session_state.processes if x['id'] != p['id']]
                            st.rerun()
            else:
                st.info("Nenhum processo mapeado. Adicione processos ao lado.")

    with tab2:
        st.markdown("#### 🔄 Atividades e Fluxo BPMN")
        st.info("**BPMN 2.0:** *Tasks* são trabalho atômico. Classifique cada atividade por tipo de valor: **VA** (Valor Agregado), **NVA** (Não agrega valor — eliminar), **BVA** (Business Value-Added — necessário mas não percebido pelo cliente).")

        if not st.session_state.processes:
            st.warning("⚠️ Crie pelo menos um processo na aba anterior.")
        else:
            col_f, col_l = st.columns([1,1])
            with col_f:
                st.markdown("##### ➕ Nova Atividade")
                act_process = st.selectbox("Processo", [p["name"] for p in st.session_state.processes])
                act_name = st.text_input("Nome da Atividade", placeholder="Ex: Verificar disponibilidade")
                act_type = st.selectbox("Tipo BPMN", ["Task","User Task","Service Task","Manual Task","Script Task","Sub-Process"])
                act_value = st.radio("Classificação de Valor (Lean/BPM)", ["VA","NVA","BVA"], horizontal=True,
                                      help="VA=Valor Agregado | NVA=Não Agrega | BVA=Necessário ao Negócio")
                act_role = st.selectbox("Responsável", ["(nenhum)"] + [a["name"] for a in st.session_state.actors])
                act_time = st.number_input("Tempo médio (minutos)", value=5, min_value=1)
                act_rule = st.selectbox("Regra aplicável", ["(nenhuma)"] + [r["name"] for r in st.session_state.rules])

                if st.button("✅ Adicionar Atividade", type="primary"):
                    if act_name:
                        proc_id = next((p["id"] for p in st.session_state.processes if p["name"] == act_process), None)
                        st.session_state.activities.append({
                            "id": new_id(), "name": act_name, "type": act_type,
                            "value_type": act_value, "process_id": proc_id,
                            "process_name": act_process, "role": act_role,
                            "time_min": act_time, "rule": act_rule
                        })
                        st.success(f"Atividade '{act_name}' adicionada!")
                        st.rerun()

            with col_l:
                st.markdown("##### 📊 Atividades por Processo")
                if st.session_state.activities:
                    proc_filter = st.selectbox("Filtrar por processo", 
                                                ["Todos"] + [p["name"] for p in st.session_state.processes],
                                                key="proc_filter_acts")
                    acts = [a for a in st.session_state.activities if 
                            proc_filter == "Todos" or a["process_name"] == proc_filter]

                    value_colors = {"VA":"#d4edda","NVA":"#f8d7da","BVA":"#fff3cd"}
                    value_labels = {"VA":"✅ VA","NVA":"❌ NVA","BVA":"⚠️ BVA"}
                    for a in acts:
                        bg = value_colors.get(a["value_type"],"#fff")
                        label = value_labels.get(a["value_type"],"")
                        st.markdown(f"""
                        <div style="background:{bg};border-radius:8px;padding:0.6rem 0.8rem;margin:0.3rem 0;">
                            <b>{a['name']}</b> <small>({a['type']})</small>
                            <span style="float:right;font-weight:600;">{label}</span><br>
                            <small>🔄 {a['process_name']} | 👤 {a['role']} | ⏱️ {a['time_min']}min</small>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Nenhuma atividade cadastrada.")

                # BPMN-like diagram via Mermaid text
                if st.session_state.activities and st.session_state.processes:
                    st.markdown("##### 🗺️ Fluxo do Processo (texto BPMN)")
                    sel_proc = st.selectbox("Processo para visualizar", [p["name"] for p in st.session_state.processes], key="mermaid_proc")
                    proc_acts = [a for a in st.session_state.activities if a["process_name"] == sel_proc]
                    if proc_acts:
                        mermaid_lines = ["flowchart LR", "    START([▶ Início])"]
                        prev = "START"
                        for i, a in enumerate(proc_acts):
                            node_id = f"A{i}"
                            shape_open = ">" if a["type"] == "Task" else "[["
                            shape_close = "]" if a["type"] == "Task" else "]]"
                            color = "style " + node_id + (" fill:#d4edda" if a["value_type"]=="VA" else " fill:#f8d7da" if a["value_type"]=="NVA" else " fill:#fff3cd")
                            mermaid_lines.append(f"    {node_id}[\"{a['name']}\"]")
                            mermaid_lines.append(f"    {color}")
                            mermaid_lines.append(f"    {prev} --> {node_id}")
                            prev = node_id
                        mermaid_lines.append("    END([⏹ Fim])")
                        mermaid_lines.append(f"    {prev} --> END")
                        mermaid_code = "\n".join(mermaid_lines)
                        st.code(mermaid_code, language="text")
                        st.caption("💡 Cole este código em https://mermaid.live para visualizar")

    with tab3:
        st.markdown("#### 📊 Análise de Valor Agregado")
        st.info("Metodologia Lean BPM: classifique atividades em VA (Valor para Cliente), BVA (Necessário ao Negócio) e NVA (Desperdício — eliminar).")

        va, nva, bva = va_ratio()
        total_acts = va + nva + bva

        if total_acts == 0:
            st.warning("Adicione atividades na aba anterior para ver a análise de valor.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total de Atividades", total_acts)
            col2.metric("✅ Valor Agregado (VA)", va, f"{va/total_acts:.0%}")
            col3.metric("⚠️ Necessário (BVA)", bva, f"{bva/total_acts:.0%}")
            col4.metric("❌ Desperdício (NVA)", nva, f"{nva/total_acts:.0%}", delta_color="inverse")

            fig = go.Figure(go.Pie(
                labels=["VA — Valor Agregado", "BVA — Valor de Negócio", "NVA — Não Agrega Valor"],
                values=[va, bva, nva],
                marker_colors=["#198754","#ffc107","#dc3545"],
                hole=0.45,
                textinfo='label+percent'
            ))
            fig.update_layout(height=350, showlegend=True, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)

            # Tempo total
            total_time = sum(a.get("time_min", 0) for a in st.session_state.activities)
            va_time = sum(a.get("time_min", 0) for a in st.session_state.activities if a.get("value_type") == "VA")
            if total_time > 0:
                st.metric("⏱️ Eficiência de Tempo (VA)", f"{va_time/total_time:.0%}", 
                           help="% do tempo total gasto em atividades que agregam valor")

            if nva > 0:
                st.warning(f"⚡ **Oportunidade de melhoria:** {nva} atividades NVA identificadas. Considere eliminá-las para aumentar a eficiência do processo.")

# ─────────────────────────────────────────────
# MÓDULO 3 — ORGANIZAÇÃO
# ─────────────────────────────────────────────
elif st.session_state.active_module == "organization":
    st.markdown("""
    <div class="main-header">
        <h2>👥 Módulo 3: Business Organization Model</h2>
        <p style="margin:0; opacity:0.9">ArchiMate 3.2 Business Layer — Atores, Papéis, RACI, Stakeholders</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Atores & Papéis", "📋 Matriz RACI", "🎯 Stakeholder Map"])

    with tab1:
        col_f, col_l = st.columns([1,1])
        with col_f:
            st.markdown("##### ➕ Novo Ator")
            actor_name = st.text_input("Nome", placeholder="Ex: Gerente de Operações")
            actor_type = st.selectbox("Tipo", ["Interno", "Externo", "Sistema", "Parceiro"])
            actor_roles = st.text_input("Papéis", placeholder="Aprovador, Revisor, Executor...")
            actor_dept = st.text_input("Departamento/Área", placeholder="Ex: Operações")

            if st.button("✅ Adicionar Ator", type="primary"):
                if actor_name:
                    st.session_state.actors.append({
                        "id": new_id(), "name": actor_name, "type": actor_type,
                        "roles": actor_roles, "department": actor_dept
                    })
                    st.success(f"Ator '{actor_name}' adicionado!")
                    st.rerun()

        with col_l:
            st.markdown("##### 👥 Atores Registrados")
            type_icons = {"Interno":"🏢","Externo":"🌐","Sistema":"💻","Parceiro":"🤝"}
            if st.session_state.actors:
                for a in st.session_state.actors:
                    icon = type_icons.get(a["type"],"👤")
                    st.markdown(f"""
                    <div class="module-card">
                        <b>{icon} {a['name']}</b> <small>({a['type']})</small><br>
                        <small>Dept: {a.get('department','—')} | Papéis: {a.get('roles','—')}</small>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Nenhum ator definido.")

        # Org chart visualization
        if st.session_state.actors:
            internal = [a for a in st.session_state.actors if a["type"] == "Interno"]
            external = [a for a in st.session_state.actors if a["type"] != "Interno"]
            
            fig = go.Figure()
            cols_int = len(internal)
            for i, a in enumerate(internal):
                fig.add_trace(go.Scatter(
                    x=[i], y=[1], mode='markers+text',
                    marker=dict(size=50, color='#2e6da4', symbol='square'),
                    text=[a['name'][:15]], textposition='bottom center',
                    name=a['name'], showlegend=False
                ))
            for i, a in enumerate(external):
                fig.add_trace(go.Scatter(
                    x=[i], y=[0], mode='markers+text',
                    marker=dict(size=40, color='#6c757d', symbol='circle'),
                    text=[a['name'][:15]], textposition='bottom center',
                    name=a['name'], showlegend=False
                ))
            fig.update_layout(
                height=250, xaxis=dict(showticklabels=False), 
                yaxis=dict(showticklabels=False, tickvals=[0,1], ticktext=["Externos","Internos"]),
                title="Mapa de Atores", margin=dict(l=20,r=20,t=40,b=40),
                plot_bgcolor='rgba(240,247,255,0.5)'
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("#### 📋 Matriz RACI")
        st.info("**R**esponsável · **A**provador · **C**onsultado · **I**nformado — Por atividade de processo")

        if not st.session_state.actors or not st.session_state.activities:
            st.warning("⚠️ Adicione atores (aba anterior) e atividades (Módulo 2) primeiro.")
        else:
            st.markdown("##### ➕ Definir RACI")
            col_f, col_l = st.columns([1,1])
            with col_f:
                raci_act = st.selectbox("Atividade", [a["name"] for a in st.session_state.activities])
                raci_actor = st.selectbox("Ator", [a["name"] for a in st.session_state.actors])
                raci_role = st.selectbox("Papel RACI", ["R — Responsável", "A — Aprovador", "C — Consultado", "I — Informado"])

                if st.button("✅ Adicionar RACI", type="primary"):
                    st.session_state.raci.append({
                        "activity": raci_act, "actor": raci_actor, "role": raci_role[0]
                    })
                    st.success("RACI adicionado!")
                    st.rerun()

            with col_l:
                if st.session_state.raci:
                    raci_df = pd.DataFrame(st.session_state.raci)
                    pivot = raci_df.pivot_table(index="activity", columns="actor", values="role", aggfunc="first")
                    st.dataframe(pivot.fillna(""), use_container_width=True)

                    raci_colors = {"R":"#d4edda","A":"#cce5ff","C":"#fff3cd","I":"#e2e3e5"}
                    st.markdown("**Legenda:** 🟢 R=Responsável | 🔵 A=Aprovador | 🟡 C=Consultado | ⚪ I=Informado")
                else:
                    st.info("Nenhuma entrada RACI definida.")

    with tab3:
        st.markdown("#### 🎯 Mapa de Stakeholders")
        st.info("Posicione stakeholders no mapa **Poder × Interesse** para definir estratégia de engajamento.")

        if not st.session_state.actors:
            st.warning("Adicione atores na primeira aba.")
        else:
            stakeholder_data = []
            for a in st.session_state.actors:
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    st.write(f"**{a['name']}**")
                with col2:
                    power = st.slider("Poder", 1, 5, 3, key=f"power_{a['id']}")
                with col3:
                    interest = st.slider("Interesse", 1, 5, 3, key=f"interest_{a['id']}")
                stakeholder_data.append({"name": a["name"], "power": power, "interest": interest, "type": a["type"]})

            if stakeholder_data:
                df = pd.DataFrame(stakeholder_data)
                fig = px.scatter(df, x="interest", y="power", text="name", color="type",
                                  color_discrete_map={"Interno":"#2e6da4","Externo":"#dc3545","Sistema":"#6c757d","Parceiro":"#198754"},
                                  size=[30]*len(df))
                fig.add_vline(x=3, line_dash="dash", line_color="gray")
                fig.add_hline(y=3, line_dash="dash", line_color="gray")
                fig.update_traces(textposition='top center')
                fig.add_annotation(x=1.5, y=4.5, text="GERENCIE DE PERTO", showarrow=False, font=dict(size=10, color="#dc3545"))
                fig.add_annotation(x=4, y=4.5, text="MANTENHA SATISFEITO", showarrow=False, font=dict(size=10, color="#198754"))
                fig.add_annotation(x=1.5, y=1.5, text="MONITORE", showarrow=False, font=dict(size=10, color="#6c757d"))
                fig.add_annotation(x=4, y=1.5, text="MANTENHA INFORMADO", showarrow=False, font=dict(size=10, color="#0d6efd"))
                fig.update_layout(xaxis_range=[0,6], yaxis_range=[0,6], height=400,
                                   xaxis_title="Interesse", yaxis_title="Poder")
                st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# MÓDULO 4 — REGRAS (SBVR/DMN)
# ─────────────────────────────────────────────
elif st.session_state.active_module == "rules":
    st.markdown("""
    <div class="main-header">
        <h2>📋 Módulo 4: Business Rules Model</h2>
        <p style="margin:0; opacity:0.9">SBVR v1.5 + DMN 1.5 (OMG) — Vocabulário, Regras, Tabelas de Decisão</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📖 Glossário (SBVR)", "📏 Regras de Negócio", "🎰 Tabelas de Decisão (DMN)"])

    with tab1:
        st.markdown("#### 📖 Vocabulário de Negócio Controlado")
        st.info("**SBVR + NISO Z39.19:** Um glossário controlado garante que todos usem os mesmos termos da mesma forma — base para regras precisas e sem ambiguidade.")

        col_f, col_l = st.columns([1,1])
        with col_f:
            term_name = st.text_input("Termo", placeholder="Ex: Mesa Premium")
            term_def = st.text_area("Definição", height=80, placeholder="Ex: Mesa localizada em área especial com capacidade ≥ 4 pessoas e vista panorâmica")
            term_synonyms = st.text_input("Sinônimos", placeholder="Mesa VIP, Mesa Especial")
            term_context = st.text_input("Contexto/Domínio", placeholder="Ex: Gestão de Reservas")
            term_source = st.text_input("Fonte", placeholder="Ex: Manual Operacional v3.2")

            if st.button("✅ Adicionar Termo", type="primary"):
                if term_name:
                    st.session_state.glossary.append({
                        "id": new_id(), "term": term_name, "definition": term_def,
                        "synonyms": term_synonyms, "context": term_context, "source": term_source
                    })
                    st.success(f"Termo '{term_name}' adicionado!")
                    st.rerun()

        with col_l:
            st.markdown("##### 📚 Glossário")
            if st.session_state.glossary:
                search = st.text_input("🔍 Buscar termo", key="gloss_search")
                terms = [t for t in st.session_state.glossary if 
                         not search or search.lower() in t["term"].lower()]
                for t in sorted(terms, key=lambda x: x["term"]):
                    with st.expander(f"📖 **{t['term']}**"):
                        st.write(f"**Definição:** {t['definition']}")
                        if t.get("synonyms"): st.write(f"**Sinônimos:** {t['synonyms']}")
                        if t.get("context"): st.write(f"**Contexto:** {t['context']}")
                        if t.get("source"): st.write(f"**Fonte:** {t['source']}")
            else:
                st.info("Glossário vazio. Adicione termos de negócio.")

    with tab2:
        st.markdown("#### 📏 Regras de Negócio")
        st.info("**SBVR:** Regras podem ser *Obrigações* (deve), *Proibições* (não deve) ou *Permissões* (pode). Classifique em *Estruturais* (definem o negócio) ou *Operativas* (guiam comportamento).")

        col_f, col_l = st.columns([1,1])
        with col_f:
            rule_name = st.text_input("Nome da Regra", placeholder="Ex: Reserva Requer Pagamento Antecipado")
            rule_stmt = st.text_area("Declaração (SBVR)", height=90,
                                      placeholder="Ex: É obrigatório que toda reserva de mesa premium seja acompanhada de pagamento antecipado de 50% do valor estimado.")
            rule_type = st.selectbox("Tipo SBVR", ["Structural Rule", "Operative Rule"])
            rule_modality = st.selectbox("Modalidade", ["Obrigação (deve)", "Proibição (não deve)", "Permissão (pode)"])
            rule_source = st.text_input("Fonte/Regulação", placeholder="Ex: Política Interna #12 / Lei 8.078/90")
            rule_activities = st.multiselect("Atividades impactadas", 
                                              [a["name"] for a in st.session_state.activities])

            if st.button("✅ Adicionar Regra", type="primary"):
                if rule_name and rule_stmt:
                    st.session_state.rules.append({
                        "id": new_id(), "name": rule_name, "statement": rule_stmt,
                        "type": rule_type, "modality": rule_modality,
                        "source": rule_source, "activities": rule_activities
                    })
                    st.success("Regra adicionada!")
                    st.rerun()

        with col_l:
            st.markdown("##### 📋 Regras Definidas")
            modality_icons = {"Obrigação (deve)":"🔵","Proibição (não deve)":"🔴","Permissão (pode)":"🟢"}
            if st.session_state.rules:
                for r in st.session_state.rules:
                    icon = modality_icons.get(r["modality"],"⚪")
                    with st.expander(f"{icon} {r['name']}"):
                        st.write(f"**Declaração:** {r['statement']}")
                        st.write(f"**Tipo:** {r['type']} | **Modalidade:** {r['modality']}")
                        if r.get("source"): st.write(f"**Fonte:** {r['source']}")
                        if r.get("activities"): st.write(f"**Atividades:** {', '.join(r['activities'])}")
            else:
                st.info("Nenhuma regra definida.")

    with tab3:
        st.markdown("#### 🎰 Tabelas de Decisão (DMN 1.5)")
        st.info("**DMN 1.5:** Tabelas de decisão estruturam lógica condicional. *Hit Policy*: **U**=Única resposta, **A**=Todas que aplicam, **F**=Primeira que aplica.")

        col_f, col_l = st.columns([1,1])
        with col_f:
            dt_name = st.text_input("Nome da Decisão", placeholder="Ex: Tipo de Desconto")
            dt_policy = st.selectbox("Hit Policy (DMN)", ["U — Unique","A — Any","F — First","R — Rule Order","C — Collect"])
            dt_input1 = st.text_input("Entrada 1", placeholder="Ex: Tipo de Cliente")
            dt_input2 = st.text_input("Entrada 2 (opcional)", placeholder="Ex: Valor da Compra")
            dt_output = st.text_input("Saída", placeholder="Ex: Percentual de Desconto")

            st.markdown("**Regras da Tabela:**")
            if "temp_dt_rules" not in st.session_state:
                st.session_state.temp_dt_rules = []

            r_in1 = st.text_input("Condição 1", placeholder='Ex: "VIP"', key="dt_r_in1")
            r_in2 = st.text_input("Condição 2", placeholder='Ex: ">1000"', key="dt_r_in2")
            r_out = st.text_input("Resultado", placeholder="Ex: 15%", key="dt_r_out")

            if st.button("➕ Adicionar Linha"):
                if r_out:
                    st.session_state.temp_dt_rules.append(
                        {"in1": r_in1, "in2": r_in2, "out": r_out}
                    )
                    st.rerun()

            if st.session_state.temp_dt_rules:
                rule_df = pd.DataFrame(st.session_state.temp_dt_rules)
                rule_df.columns = [dt_input1 or "Entrada 1", dt_input2 or "Entrada 2", dt_output or "Saída"]
                st.dataframe(rule_df, use_container_width=True)

            if st.button("✅ Salvar Tabela de Decisão", type="primary"):
                if dt_name and st.session_state.temp_dt_rules:
                    st.session_state.decision_tables.append({
                        "id": new_id(), "name": dt_name, "hit_policy": dt_policy,
                        "input1": dt_input1, "input2": dt_input2, "output": dt_output,
                        "rules": st.session_state.temp_dt_rules.copy()
                    })
                    st.session_state.temp_dt_rules = []
                    st.success(f"Tabela '{dt_name}' salva!")
                    st.rerun()

        with col_l:
            st.markdown("##### 📊 Tabelas Salvas")
            for dt in st.session_state.decision_tables:
                with st.expander(f"🎰 {dt['name']} [{dt['hit_policy'][0]}]"):
                    df = pd.DataFrame(dt["rules"])
                    if not df.empty:
                        df.columns = [dt.get("input1","In1"), dt.get("input2","In2"), dt.get("output","Out")]
                        st.dataframe(df, use_container_width=True)

# ─────────────────────────────────────────────
# MÓDULO 5 — VALUE REALIZATION DASHBOARD
# ─────────────────────────────────────────────
elif st.session_state.active_module == "dashboard":
    st.markdown("""
    <div class="main-header">
        <h2>📊 Value Realization Dashboard</h2>
        <p style="margin:0; opacity:0.9">Bridgeland & Zahavi Cap.12 — Análise, Simulação e Deployment de Valor</p>
    </div>
    """, unsafe_allow_html=True)

    scores = get_completeness()
    total = sum(scores.values())
    va, nva, bva = va_ratio()
    total_acts = va + nva + bva

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🏆 Business Model Score", f"{total:.0f}/100",
                delta="Meta: 80+" if total < 80 else "✅ Meta atingida")
    col2.metric("🎯 Metas Definidas", len(st.session_state.goals))
    col3.metric("⚙️ Processos", len(st.session_state.processes))
    col4.metric("👥 Atores", len(st.session_state.actors))
    col5.metric("📋 Regras", len(st.session_state.rules))

    st.divider()
    c1, c2 = st.columns([1,1])

    with c1:
        st.markdown("#### 🕸️ Maturidade por Disciplina")
        cats = list(scores.keys())
        vals = list(scores.values())
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill='toself', name='Atual',
            line_color='#2e6da4', fillcolor='rgba(46,109,164,0.25)'
        ))
        fig.add_trace(go.Scatterpolar(
            r=[25,25,25,25,25], theta=cats + [cats[0]],
            name='Meta (100%)', line=dict(color='red', dash='dash'),
            fillcolor='rgba(255,0,0,0)'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,25])),
            showlegend=True, height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### 📈 Indicadores de Valor")
        
        # Alignment Score
        goals_count = len(st.session_state.goals)
        procs_with_goals = sum(1 for p in st.session_state.processes if p.get("goal") != "(nenhuma)")
        alignment = (procs_with_goals / len(st.session_state.processes) * 100) if st.session_state.processes else 0

        # Rules Coverage
        acts_with_rules = sum(1 for a in st.session_state.activities if a.get("rule") != "(nenhuma)")
        rules_coverage = (acts_with_rules / total_acts * 100) if total_acts > 0 else 0

        # VA Ratio
        va_pct = (va / total_acts * 100) if total_acts > 0 else 0

        indicators = [
            ("Strategy-Process Alignment", alignment, "% processos vinculados a metas"),
            ("Rules Coverage", rules_coverage, "% atividades com regra definida"),
            ("Value-Added Activity Ratio", va_pct, "% atividades que agregam valor"),
            ("Stakeholder Coverage", min(len(st.session_state.actors)*10, 100), "Abrangência de stakeholders"),
        ]

        for name, val, desc in indicators:
            color = "#198754" if val >= 70 else "#ffc107" if val >= 40 else "#dc3545"
            st.markdown(f"""
            <div class="kpi-box">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><b>{name}</b><br><small style="color:#666;">{desc}</small></div>
                    <div style="font-size:1.5rem;font-weight:800;color:{color};">{val:.0f}%</div>
                </div>
                <div style="background:#e9ecef;border-radius:4px;height:6px;margin-top:0.5rem;">
                    <div style="background:{color};height:6px;border-radius:4px;width:{val}%;"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🤖 Recomendações Inteligentes (AI-Augmented Analysis)")

    recommendations = []
    if not st.session_state.vision:
        recommendations.append(("🔴 Crítico", "Defina a Visão da empresa — elemento fundamental do BMM (OMG v1.3)"))
    if not st.session_state.goals:
        recommendations.append(("🔴 Crítico", "Adicione pelo menos 3 Metas cobrindo as 4 perspectivas do Balanced Scorecard"))
    if nva > 0:
        recommendations.append(("🟡 Melhoria", f"{nva} atividades NVA identificadas — aplique Lean para eliminá-las (potencial de {nva/(total_acts or 1):.0%} de redução no lead time)"))
    if not st.session_state.rules:
        recommendations.append(("🟡 Melhoria", "Documente as regras de negócio — processos sem regras são propensos a erros e inconsistências"))
    if alignment < 60 and st.session_state.processes:
        recommendations.append(("🟠 Atenção", f"Apenas {alignment:.0f}% dos processos estão vinculados a metas estratégicas — risco de desalinhamento organizacional"))
    if len(st.session_state.actors) == 0:
        recommendations.append(("🟡 Melhoria", "Defina atores e papéis — a Matriz RACI previne conflitos de responsabilidade"))
    if not st.session_state.decision_tables and st.session_state.rules:
        recommendations.append(("💡 Sugestão", "Converta regras complexas em Tabelas de Decisão DMN 1.5 para maior precisão e automação"))
    if total >= 80:
        recommendations.append(("🟢 Excelente", "Modelo de negócio bem estruturado! Considere realizar simulações de processo e análise de cenários"))

    if not recommendations:
        recommendations.append(("💡 Sugestão", "Continue adicionando detalhes ao modelo para aumentar a precisão da análise"))

    for level, rec in recommendations:
        color = {"🔴 Crítico":"#f8d7da","🟡 Melhoria":"#fff3cd","🟠 Atenção":"#ffeeba",
                 "🟢 Excelente":"#d4edda","💡 Sugestão":"#cce5ff"}.get(level,"#e9ecef")
        st.markdown(f"""<div style="background:{color};border-radius:8px;padding:0.7rem 1rem;margin:0.3rem 0;">
            <b>{level}:</b> {rec}</div>""", unsafe_allow_html=True)

    # Export section
    st.divider()
    st.markdown("#### 📤 Exportar Modelo")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        model_data = {
            "company": st.session_state.company_name,
            "timestamp": datetime.now().isoformat(),
            "standard": "OMG BMM 1.3 + BPMN 2.0.2 + SBVR 1.5 + DMN 1.5",
            "motivation": {
                "vision": st.session_state.vision,
                "mission": st.session_state.mission,
                "goals": st.session_state.goals,
                "strategies": st.session_state.strategies,
            },
            "processes": st.session_state.processes,
            "activities": st.session_state.activities,
            "organization": {"actors": st.session_state.actors, "raci": st.session_state.raci},
            "rules": {"rules": st.session_state.rules, "glossary": st.session_state.glossary,
                      "decision_tables": st.session_state.decision_tables},
            "scores": scores,
        }
        json_str = json.dumps(model_data, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ Exportar JSON (OMG-compatible)",
            data=json_str,
            file_name=f"business_model_{st.session_state.company_name or 'export'}.json",
            mime="application/json",
            use_container_width=True
        )

    with col_e2:
        # Generate summary report
        report = f"""# Business Model Report — {st.session_state.company_name}
Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Padrões: BMM 1.3 | BPMN 2.0.2 | SBVR 1.5 | DMN 1.5

## Score: {total}/100

## Motivação
- **Visão:** {st.session_state.vision or '(não definida)'}
- **Missão:** {st.session_state.mission or '(não definida)'}
- **Metas:** {len(st.session_state.goals)}
- **Estratégias:** {len(st.session_state.strategies)}

## Processos
- **Processos:** {len(st.session_state.processes)}
- **Atividades:** {total_acts}
- **VA/NVA/BVA:** {va}/{nva}/{bva}

## Organização
- **Atores:** {len(st.session_state.actors)}
- **Entradas RACI:** {len(st.session_state.raci)}

## Regras
- **Regras:** {len(st.session_state.rules)}
- **Termos no Glossário:** {len(st.session_state.glossary)}
- **Tabelas de Decisão:** {len(st.session_state.decision_tables)}

## Indicadores
- Strategy-Process Alignment: {alignment:.0f}%
- VA Activity Ratio: {va_pct:.0f}%

Referências: Bridgeland & Zahavi (2009) | OMG.org/spec
"""
        st.download_button(
            "⬇️ Exportar Relatório (Markdown)",
            data=report,
            file_name=f"report_{st.session_state.company_name or 'export'}.md",
            mime="text/markdown",
            use_container_width=True
        )

# ─────────────────────────────────────────────
# MÓDULO 6 — RASTREABILIDADE
# ─────────────────────────────────────────────
elif st.session_state.active_module == "traceability":
    st.markdown("""
    <div class="main-header">
        <h2>🔗 Módulo 6: Mapa de Rastreabilidade</h2>
        <p style="margin:0; opacity:0.9">Bridgeland & Zahavi — Interdependência entre as 4 Disciplinas de Business Modeling</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("A rastreabilidade é a capacidade de conectar **por quê** (Motivação) → **como** (Processos) → **quem** (Organização) → **o quê** (Regras). Sem isso, os modelos ficam isolados e perdem valor.")

    # Build traceability graph
    G = nx.DiGraph()

    # Add nodes
    if st.session_state.vision:
        G.add_node("Visão", layer="motivation", label=st.session_state.vision[:30]+"...")
    for g in st.session_state.goals:
        G.add_node(f"Meta:{g['name']}", layer="motivation", label=g['name'])
        if st.session_state.vision:
            G.add_edge("Visão", f"Meta:{g['name']}")
    for s in st.session_state.strategies:
        G.add_node(f"Estratégia:{s['name']}", layer="motivation", label=s['name'])
        if s.get("goal") and s["goal"] != "(nenhuma)":
            G.add_edge(f"Meta:{s['goal']}", f"Estratégia:{s['name']}")
    for p in st.session_state.processes:
        G.add_node(f"Processo:{p['name']}", layer="process", label=p['name'])
        if p.get("goal") and p["goal"] != "(nenhuma)":
            G.add_edge(f"Meta:{p['goal']}", f"Processo:{p['name']}")
    for a in st.session_state.activities:
        G.add_node(f"Atividade:{a['name']}", layer="activity", label=a['name'])
        G.add_edge(f"Processo:{a['process_name']}", f"Atividade:{a['name']}")
        if a.get("role") and a["role"] != "(nenhum)":
            G.add_node(f"Ator:{a['role']}", layer="organization", label=a['role'])
            G.add_edge(f"Atividade:{a['name']}", f"Ator:{a['role']}")
        if a.get("rule") and a["rule"] != "(nenhuma)":
            G.add_node(f"Regra:{a['rule']}", layer="rules", label=a['rule'])
            G.add_edge(f"Atividade:{a['name']}", f"Regra:{a['rule']}")

    if len(G.nodes()) < 2:
        st.warning("⚠️ Adicione dados nos módulos anteriores para visualizar a rastreabilidade.")
        st.markdown("""
        **Exemplo de rastreabilidade completa:**
        ```
        Visão → Meta (Financeiro) → Estratégia de Expansão
                                  → Processo: Reserva de Mesa
                                    → Atividade: Verificar Disponibilidade
                                      → Ator: Recepcionista
                                      → Regra: Capacidade Máxima
        ```
        """)
    else:
        # Visualize with plotly
        pos = nx.spring_layout(G, seed=42, k=2)
        layer_colors = {
            "motivation": "#ffc107",
            "process": "#0d6efd",
            "activity": "#6610f2",
            "organization": "#198754",
            "rules": "#dc3545"
        }

        edge_x, edge_y = [], []
        for e in G.edges():
            x0,y0 = pos[e[0]]; x1,y1 = pos[e[1]]
            edge_x += [x0,x1,None]; edge_y += [y0,y1,None]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines',
                                  line=dict(width=1.5, color='#aaa'), hoverinfo='none'))

        for layer in ["motivation","process","activity","organization","rules"]:
            layer_nodes = [(n, G.nodes[n]) for n in G.nodes() if G.nodes[n].get("layer") == layer]
            if layer_nodes:
                xs = [pos[n][0] for n,_ in layer_nodes]
                ys = [pos[n][1] for n,_ in layer_nodes]
                labels = [d.get("label", n.split(":",1)[-1])[:20] for n,d in layer_nodes]
                layer_labels = {"motivation":"🎯 Motivação","process":"⚙️ Processo",
                                "activity":"🔄 Atividade","organization":"👥 Organização","rules":"📋 Regra"}
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode='markers+text',
                    marker=dict(size=25, color=layer_colors[layer], line=dict(width=2, color='white')),
                    text=labels, textposition='top center',
                    name=layer_labels.get(layer, layer), textfont=dict(size=9)
                ))

        fig.update_layout(
            height=500, showlegend=True,
            xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False),
            plot_bgcolor='rgba(240,247,255,0.5)',
            margin=dict(l=20,r=20,t=30,b=20),
            title=f"Grafo de Rastreabilidade — {st.session_state.company_name or 'Modelo de Negócio'}"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Nós no grafo", len(G.nodes()))
        col2.metric("Conexões", len(G.edges()))
        isolated = len([n for n in G.nodes() if G.degree(n) == 0])
        col3.metric("Elementos Isolados", isolated, 
                     delta="Conecte-os" if isolated > 0 else "✅ Todos conectados",
                     delta_color="inverse" if isolated > 0 else "normal")

        if isolated > 0:
            st.warning(f"⚠️ {isolated} elemento(s) sem conexão. Rastreabilidade completa exige que todos os elementos estejam conectados à cadeia Visão→Objetivo→Processo→Regra.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption("""
**Business Modeling Studio — POC** | 
Baseado em: *Bridgeland & Zahavi (2009)* + **OMG BMM 1.3** + **BPMN 2.0.2** + **SBVR 1.5** + **DMN 1.5** + **ArchiMate 3.2** + **ANSI/NISO Z39.19** + **APQC PCF v7.3** |
Frameworks: Balanced Scorecard (Kaplan & Norton) · Business Model Canvas (Osterwalder) · Porter's Value Chain
""")
