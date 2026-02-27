import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="SE Suite 2.1 — Plano de Ação",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

.stApp { background: #0a0e1a; }

/* Hero */
.hero {
    background: linear-gradient(135deg, #0d1628, #111827, #0a1020);
    border: 1px solid #1a2235;
    border-radius: 10px;
    padding: 28px 36px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "SE SUITE 2.1";
    position: absolute; right: -10px; top: 50%;
    transform: translateY(-50%);
    font-size: 80px; font-weight: 700;
    color: rgba(245,166,35,.04);
    white-space: nowrap;
    font-family: 'IBM Plex Mono', monospace;
    pointer-events: none;
}
.hero-title { font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 700; color: #f5a623; margin: 0 0 6px; }
.hero-sub   { font-size: 13px; color: #8899aa; margin: 0 0 18px; }
.hero-meta  { display: flex; gap: 28px; flex-wrap: wrap; }
.meta-item  { display: flex; flex-direction: column; gap: 2px; }
.meta-label { font-size: 9px; color: #8899aa; letter-spacing: .12em; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; }
.meta-val   { font-size: 12px; color: #e8f0f8; font-family: 'IBM Plex Mono', monospace; }

/* KPI cards */
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 20px; }
.kpi-card { background: #111827; border: 1px solid #1a2235; border-radius: 6px; padding: 14px 18px; }
.kpi-val  { font-family: 'IBM Plex Mono', monospace; font-size: 26px; font-weight: 700; line-height: 1; }
.kpi-lbl  { font-size: 10px; color: #8899aa; letter-spacing: .08em; text-transform: uppercase; margin-top: 4px; }
.kpi-blue { color: #00d4ff; } .kpi-green { color: #00e676; }
.kpi-amber{ color: #f5a623; } .kpi-red   { color: #ff5252; }
.kpi-muted{ color: #8899aa; }

/* Badges */
.badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 2px;
         font-size: 10px; font-family: 'IBM Plex Mono', monospace; font-weight: 600; white-space: nowrap; }
.b-pend { background: rgba(136,153,170,.1); color: #8899aa;  border: 1px solid rgba(136,153,170,.2); }
.b-wip  { background: rgba(245,166,35,.12); color: #f5a623;  border: 1px solid rgba(245,166,35,.3); }
.b-done { background: rgba(0,230,118,.12);  color: #00e676;  border: 1px solid rgba(0,230,118,.25); }
.b-blk  { background: rgba(255,82,82,.12);  color: #ff5252;  border: 1px solid rgba(255,82,82,.25); }

/* Resp tags */
.rt { display: inline-flex; align-items: center; padding: 2px 7px; border-radius: 2px;
      font-size: 10px; font-family: 'IBM Plex Mono', monospace; }

/* Section headers */
.sec-hdr { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 700;
           color: #e8f0f8; padding-bottom: 10px; border-bottom: 1px solid #1a2235; margin-bottom: 16px; }
.sec-sub  { font-size: 10px; color: #8899aa; font-weight: 400; margin-left: 8px; }

/* Tables */
.se-tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.se-tbl thead tr { background: #111827; border-bottom: 2px solid #f5a623; }
.se-tbl th { padding: 9px 12px; text-align: left; font-family: 'IBM Plex Mono', monospace;
             font-size: 9px; letter-spacing: .1em; text-transform: uppercase; color: #f5a623; }
.se-tbl tbody tr { border-bottom: 1px solid #111827; }
.se-tbl tbody tr:hover { background: rgba(0,212,255,.04); }
.se-tbl td { padding: 8px 12px; color: #c8d8e8; vertical-align: middle; }

/* Progress bar */
.pbar-wrap { display: flex; align-items: center; gap: 8px; }
.pbar-track { flex: 1; height: 6px; background: #1a2235; border-radius: 1px; overflow: hidden; min-width: 80px; }
.pbar-fill  { height: 100%; border-radius: 1px; }
.pbar-pct   { font-family: 'IBM Plex Mono', monospace; font-size: 10px; min-width: 30px; text-align: right; }

/* Timeline bar */
.tl-track { height: 18px; background: #1a2235; border-radius: 2px; position: relative; overflow: hidden; }
.tl-fill  { height: 100%; border-radius: 2px; position: absolute;
            display: flex; align-items: center; padding: 0 5px;
            font-family: 'IBM Plex Mono', monospace; font-size: 8px;
            color: rgba(255,255,255,.8); white-space: nowrap; overflow: hidden; }
.bar-pend { background: linear-gradient(90deg, #1F4E79, #2E75B6); }
.bar-done { background: linear-gradient(90deg, #1a5c35, #00e676); }
.bar-wip  { background: linear-gradient(90deg, #5c3a0a, #f5a623); }
.bar-blk  { background: linear-gradient(90deg, #5c0a0a, #ff5252); }

/* Callout boxes */
.callout { border-left: 3px solid; padding: 10px 14px; margin: 12px 0; border-radius: 0 4px 4px 0; font-size: 12px; }
.c-warn { border-color: #f5a623; background: rgba(245,166,35,.06); color: #c8d8e8; }
.c-info { border-color: #00d4ff; background: rgba(0,212,255,.05); color: #c8d8e8; }
.c-ok   { border-color: #00e676; background: rgba(0,230,118,.05); color: #c8d8e8; }
.callout b { font-family: 'IBM Plex Mono', monospace; font-size: 9px; letter-spacing: .12em; text-transform: uppercase; display: block; margin-bottom: 4px; }
.c-warn b { color: #f5a623; } .c-info b { color: #00d4ff; } .c-ok b { color: #00e676; }

/* Bloco de bloqueio */
.blk-box { background: rgba(255,82,82,.06); border: 1px solid rgba(255,82,82,.2);
           border-left: 3px solid #ff5252; padding: 10px 14px; margin: 6px 0;
           border-radius: 0 4px 4px 0; font-size: 12px; }
.blk-id   { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #ff5252;
            letter-spacing: .12em; text-transform: uppercase; margin-bottom: 3px; }
.blk-body { color: #c8d8e8; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #111827 !important; border-right: 1px solid #1a2235; }
section[data-testid="stSidebar"] .stSelectbox label { color: #8899aa !important; font-size: 11px !important; }

/* Remove default streamlit padding */
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Data ───────────────────────────────────────────────────
TASKS_RAW = [
    ("Pre-Instalacao", "T01", "Definir modalidade de hospedagem",              "Gestor TI", "2025-02-03", "2025-02-05", "pendente",      ""),
    ("Pre-Instalacao", "T02", "Estimar usuarios simultaneos",                  "Gestor TI", "2025-02-03", "2025-02-05", "pendente",      ""),
    ("Pre-Instalacao", "T03", "Escolher SGBD (SQL Server recomendado)",        "DBA",       "2025-02-04", "2025-02-05", "pendente",      ""),
    ("Pre-Instalacao", "T04", "Provisionar servidor de aplicacao (dedicado)",  "Infra",     "2025-02-05", "2025-02-07", "pendente",      ""),
    ("Pre-Instalacao", "T05", "Provisionar servidor de BD (dedicado)",         "DBA",       "2025-02-05", "2025-02-07", "pendente",      ""),
    ("Pre-Instalacao", "T06", "Obter certificado HTTPS",                       "Seguranca", "2025-02-06", "2025-02-08", "pendente",      ""),
    ("SO e Stack",     "T07", "Instalar SO Linux 64-bit no srv. de aplicacao", "SysAdmin",  "2025-02-10", "2025-02-11", "pendente",      ""),
    ("SO e Stack",     "T08", "Instalar dependencias Linux",                   "SysAdmin",  "2025-02-11", "2025-02-12", "pendente",      ""),
    ("SO e Stack",     "T09", "Compilar e instalar NGinx 1.20 da fonte",       "SysAdmin",  "2025-02-12", "2025-02-13", "pendente",      "NGinx deve ser compilado da fonte — pacotes RPM/DEB NAO sao compativeis"),
    ("SO e Stack",     "T10", "Instalar Java 8 AdoptOpenJDK HotSpot JDK",     "SysAdmin",  "2025-02-12", "2025-02-12", "pendente",      ""),
    ("SO e Stack",     "T11", "Instalar Apache Tomcat 9.x",                    "SysAdmin",  "2025-02-13", "2025-02-13", "pendente",      ""),
    ("SO e Stack",     "T12", "Instalar PHP 7.4",                              "SysAdmin",  "2025-02-13", "2025-02-13", "pendente",      ""),
    ("SO e Stack",     "T13", "Copiar fontes TTF Arial e Verdana",             "SysAdmin",  "2025-02-13", "2025-02-13", "pendente",      ""),
    ("Banco de Dados", "T14", "Instalar SO no servidor de BD",                 "DBA",       "2025-02-10", "2025-02-11", "pendente",      ""),
    ("Banco de Dados", "T15", "Instalar e configurar SQL Server",              "DBA",       "2025-02-11", "2025-02-12", "pendente",      ""),
    ("Banco de Dados", "T16", "Configurar collation CI_AI no SQL Server",      "DBA",       "2025-02-12", "2025-02-12", "pendente",      ""),
    ("Banco de Dados", "T17", "Executar comandos Snapshot Isolation",          "DBA",       "2025-02-12", "2025-02-12", "pendente",      "Executar SEM conexoes ativas no banco de dados"),
    ("Banco de Dados", "T18", "Instalar client do BD no srv. de aplicacao",   "DBA",       "2025-02-13", "2025-02-13", "pendente",      ""),
    ("SE Suite",       "T19", "Executar instalador SE Suite 2.1",              "SysAdmin",  "2025-02-14", "2025-02-14", "pendente",      ""),
    ("SE Suite",       "T20", "Verificar scripts SQL na instalacao",           "DBA",       "2025-02-14", "2025-02-14", "pendente",      "Instalacao so e concluida se TODOS os scripts SQL forem bem-sucedidos"),
    ("SE Suite",       "T21", "Verificar Elasticsearch 6.8.3 ativo e plugin", "SysAdmin",  "2025-02-14", "2025-02-14", "pendente",      ""),
    ("SE Suite",       "T22", "Instalar SE FileManager em servidor dedicado",  "Infra",     "2025-02-14", "2025-02-15", "pendente",      "FileManager exige servidor DEDICADO — nao instalar outros servicos junto"),
    ("Seguranca",      "T23", "Configurar certificado SSL/HTTPS no NGinx",     "Seguranca", "2025-02-17", "2025-02-17", "pendente",      ""),
    ("Seguranca",      "T24", "Configurar firewall e excecoes de antivirus",   "Seguranca", "2025-02-17", "2025-02-17", "pendente",      ""),
    ("Seguranca",      "T25", "Integrar Active Directory / LDAP",              "TI",        "2025-02-18", "2025-02-19", "pendente",      ""),
    ("Seguranca",      "T26", "Configurar SMTP/SSL para e-mail",               "TI",        "2025-02-18", "2025-02-18", "pendente",      ""),
    ("Validacao",      "T27", "Acessar SE Suite via HTTPS no Chrome",          "TI",        "2025-02-20", "2025-02-20", "pendente",      ""),
    ("Validacao",      "T28", "Testar login e funcionalidades basicas",        "TI",        "2025-02-20", "2025-02-20", "pendente",      ""),
    ("Validacao",      "T29", "Testar conversao de documentos para PDF",       "TI",        "2025-02-20", "2025-02-20", "pendente",      ""),
    ("Validacao",      "T30", "Testar acesso via dispositivo movel",           "TI",        "2025-02-20", "2025-02-20", "pendente",      ""),
    ("Validacao",      "T31", "Testar envio de e-mail de notificacao",         "TI",        "2025-02-20", "2025-02-20", "pendente",      ""),
    ("Validacao",      "T32", "Configurar backup do banco de dados",           "DBA",       "2025-02-21", "2025-02-21", "pendente",      ""),
    ("Validacao",      "T33", "Configurar monitoramento de performance",       "TI",        "2025-02-21", "2025-02-21", "pendente",      ""),
    ("Entrega",        "T34", "Documentar credenciais e acesso",               "Consultor", "2025-02-24", "2025-02-24", "pendente",      ""),
    ("Entrega",        "T35", "Treinar equipe de usuarios-chave",              "Consultor", "2025-02-24", "2025-02-25", "pendente",      ""),
]

DEPS = {
    "T03": ["T01"], "T04": ["T01", "T02"], "T05": ["T03"],
    "T06": ["T04"], "T07": ["T04"], "T08": ["T07"],
    "T09": ["T08"], "T10": ["T07"], "T11": ["T10"],
    "T12": ["T11"], "T13": ["T07"], "T14": ["T05"],
    "T15": ["T14"], "T16": ["T15"], "T17": ["T16"],
    "T18": ["T15", "T11"], "T19": ["T12", "T13", "T18"],
    "T20": ["T19"], "T21": ["T19"], "T22": ["T19"],
    "T23": ["T06", "T21"], "T24": ["T23"],
    "T25": ["T23"], "T26": ["T23"],
    "T27": ["T23", "T24"], "T28": ["T27"],
    "T29": ["T28"], "T30": ["T28"], "T31": ["T26", "T28"],
    "T32": ["T27"], "T33": ["T27"],
    "T34": ["T28"], "T35": ["T34"],
}

FASES      = ["Pre-Instalacao", "SO e Stack", "Banco de Dados", "SE Suite", "Seguranca", "Validacao", "Entrega"]
RESP_LIST  = ["Gestor TI", "DBA", "Infra", "SysAdmin", "Seguranca", "TI", "Consultor"]
STATUS_OPT = ["pendente", "em andamento", "concluido", "bloqueado"]

RESP_COLORS = {
    "Gestor TI": "#2E75B6", "DBA": "#C55A11",    "Infra":     "#7030A0",
    "SysAdmin":  "#375623", "Seguranca": "#833C0B", "TI": "#1F4E79", "Consultor": "#4472C4",
}

# ── Session state ──────────────────────────────────────────
if "task_state" not in st.session_state:
    st.session_state.task_state = {
        t[1]: {"status": t[6], "aviso": t[7]} for t in TASKS_RAW
    }

ts = st.session_state.task_state


# ── Helper functions ───────────────────────────────────────
def sbadge(s):
    m = {
        "pendente":     ("b-pend", "◯ pendente"),
        "em andamento": ("b-wip",  "⟳ em andamento"),
        "concluido":    ("b-done", "✓ concluido"),
        "bloqueado":    ("b-blk",  "✗ bloqueado"),
    }
    cls, lbl = m.get(s, ("b-pend", s))
    return f'<span class="badge {cls}">{lbl}</span>'

def rtag(r):
    c = RESP_COLORS.get(r, "#8899aa")
    return f'<span class="rt" style="background:{c}22;border:1px solid {c}55;color:{c}">{r}</span>'

def pbar(pct, color="#00e676"):
    return (
        f'<div class="pbar-wrap">'
        f'<div class="pbar-track"><div class="pbar-fill" style="width:{pct}%;background:{color}"></div></div>'
        f'<span class="pbar-pct" style="color:{color}">{pct}%</span>'
        f'</div>'
    )

def get_kpis():
    vals  = list(ts.values())
    total = len(vals)
    done  = sum(1 for v in vals if v["status"] == "concluido")
    wip   = sum(1 for v in vals if v["status"] == "em andamento")
    blk   = sum(1 for v in vals if v["status"] == "bloqueado")
    pend  = sum(1 for v in vals if v["status"] == "pendente")
    pct   = int(done / total * 100) if total else 0
    return total, done, wip, blk, pend, pct


# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f5a623;padding:8px 0 16px">SE Suite 2.1</div>', unsafe_allow_html=True)
    pagina = st.radio(
        "Navegação",
        ["📊 Dashboard", "📋 Tarefas", "📅 Timeline", "🔴 Bloqueios", "✏️ Atualizar"],
        label_visibility="collapsed",
    )
    st.divider()

    # Mini-progresso no sidebar
    total, done, wip, blk, pend, pct = get_kpis()
    st.markdown(f'<div style="font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Progresso Geral</div>', unsafe_allow_html=True)
    st.progress(pct / 100)
    st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:12px;color:#00e676">{pct}% — {done}/{total} tarefas</div>', unsafe_allow_html=True)
    st.divider()

    # Legenda de responsáveis
    st.markdown('<div style="font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">Responsáveis</div>', unsafe_allow_html=True)
    for resp, color in RESP_COLORS.items():
        tasks_resp = [t for t in TASKS_RAW if t[3] == resp]
        done_resp  = sum(1 for t in tasks_resp if ts[t[1]]["status"] == "concluido")
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
            f'<span style="font-size:11px;color:{color};font-family:IBM Plex Mono,monospace">{resp}</span>'
            f'<span style="font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace">{done_resp}/{len(tasks_resp)}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown('<div style="font-size:9px;color:#8899aa;font-family:IBM Plex Mono,monospace">DT21.PT0002 Rev 19<br>Atualizado: ' + datetime.now().strftime("%d/%m/%Y %H:%M") + '</div>', unsafe_allow_html=True)


# ── Hero ───────────────────────────────────────────────────
total, done, wip, blk, pend, pct = get_kpis()

st.markdown(f"""
<div class="hero">
  <div class="hero-title">SE Suite 2.1 — Plano de Ação</div>
  <div class="hero-sub">SoftExpert Excellence Suite · Equipe mista · DT21.PT0002 Rev 19</div>
  <div class="hero-meta">
    <div class="meta-item"><span class="meta-label">Início</span><span class="meta-val">03/02/2025</span></div>
    <div class="meta-item"><span class="meta-label">Fim</span><span class="meta-val">25/02/2025</span></div>
    <div class="meta-item"><span class="meta-label">Progresso</span><span class="meta-val" style="color:#00e676">{pct}% ({done}/{total})</span></div>
    <div class="meta-item"><span class="meta-label">Em Andamento</span><span class="meta-val" style="color:#f5a623">{wip}</span></div>
    <div class="meta-item"><span class="meta-label">Bloqueadas</span><span class="meta-val" style="color:#ff5252">{blk}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# KPIs
st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-val kpi-blue">{total}</div><div class="kpi-lbl">Total</div></div>
  <div class="kpi-card"><div class="kpi-val kpi-green">{done}</div><div class="kpi-lbl">Concluídas</div></div>
  <div class="kpi-card"><div class="kpi-val kpi-amber">{wip}</div><div class="kpi-lbl">Em Andamento</div></div>
  <div class="kpi-card"><div class="kpi-val kpi-red">{blk}</div><div class="kpi-lbl">Bloqueadas</div></div>
  <div class="kpi-card"><div class="kpi-val kpi-muted">{pend}</div><div class="kpi-lbl">Pendentes</div></div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sec-hdr">Por Fase</div>', unsafe_allow_html=True)
        fase_rows = ""
        for fase in FASES:
            ftasks = [t for t in TASKS_RAW if t[0] == fase]
            ftotal = len(ftasks)
            fdone  = sum(1 for t in ftasks if ts[t[1]]["status"] == "concluido")
            fwip   = sum(1 for t in ftasks if ts[t[1]]["status"] == "em andamento")
            fblk   = sum(1 for t in ftasks if ts[t[1]]["status"] == "bloqueado")
            fpend  = ftotal - fdone - fwip - fblk
            fpct   = int(fdone / ftotal * 100) if ftotal else 0
            fase_rows += (
                f"<tr>"
                f"<td><strong style='color:#e8f0f8'>{fase}</strong></td>"
                f"<td style='font-family:IBM Plex Mono,monospace;text-align:center'>{ftotal}</td>"
                f"<td style='text-align:center'>{sbadge('concluido')} {fdone}</td>"
                f"<td style='text-align:center'>{sbadge('em andamento')} {fwip}</td>"
                f"<td style='text-align:center'>{sbadge('bloqueado')} {fblk}</td>"
                f"<td>{pbar(fpct)}</td>"
                f"</tr>"
            )
        st.markdown(
            f"<table class='se-tbl'><thead><tr>"
            f"<th>Fase</th><th>Total</th><th>Concluído</th><th>Andamento</th><th>Bloqueado</th><th>Progresso</th>"
            f"</tr></thead><tbody>{fase_rows}</tbody></table>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown('<div class="sec-hdr">Por Responsável</div>', unsafe_allow_html=True)
        resp_rows = ""
        for resp in RESP_LIST:
            rtasks = [t for t in TASKS_RAW if t[3] == resp]
            if not rtasks: continue
            rtotal = len(rtasks)
            rdone  = sum(1 for t in rtasks if ts[t[1]]["status"] == "concluido")
            rblk   = sum(1 for t in rtasks if ts[t[1]]["status"] == "bloqueado")
            rpct   = int(rdone / rtotal * 100) if rtotal else 0
            blk_str = f" {sbadge('bloqueado')} {rblk}" if rblk else ""
            resp_rows += (
                f"<tr>"
                f"<td>{rtag(resp)}</td>"
                f"<td style='font-family:IBM Plex Mono,monospace;text-align:center'>{rtotal}</td>"
                f"<td style='font-family:IBM Plex Mono,monospace;color:#00e676;text-align:center'>{rdone}</td>"
                f"<td style='font-family:IBM Plex Mono,monospace;text-align:center'>{rtotal-rdone}</td>"
                f"<td>{pbar(rpct, '#2E75B6')}{blk_str}</td>"
                f"</tr>"
            )
        st.markdown(
            f"<table class='se-tbl'><thead><tr>"
            f"<th>Responsável</th><th>Total</th><th>Feito</th><th>Restam</th><th>Progresso</th>"
            f"</tr></thead><tbody>{resp_rows}</tbody></table>",
            unsafe_allow_html=True
        )

        st.markdown('<br><div class="sec-hdr">Bloqueios e Avisos Ativos</div>', unsafe_allow_html=True)
        any_blk = False
        for t in TASKS_RAW:
            s = ts[t[1]]
            if s["status"] == "bloqueado" or s["aviso"]:
                any_blk = True
                st.markdown(
                    f'<div class="blk-box">'
                    f'<div class="blk-id">{t[1]} — {t[2]}</div>'
                    f'<div class="blk-body">{s["aviso"] if s["aviso"] else "Marcada como bloqueada"}</div>'
                    f'<div style="margin-top:5px">{rtag(t[3])} &nbsp; {sbadge(s["status"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        if not any_blk:
            st.markdown('<div class="callout c-ok"><b>Status</b>Nenhum bloqueio ativo 🎉</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# TAREFAS
# ══════════════════════════════════════════════════════════
elif pagina == "📋 Tarefas":
    st.markdown('<div class="sec-hdr">Tarefas <span class="sec-sub">Filtros abaixo</span></div>', unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        f_fase = st.selectbox("Fase", ["Todas"] + FASES)
    with fc2:
        f_resp = st.selectbox("Responsável", ["Todos"] + RESP_LIST)
    with fc3:
        f_status = st.selectbox("Status", ["Todos"] + STATUS_OPT)

    rows = ""
    count = 0
    for t in TASKS_RAW:
        fase, tid, nome, resp, ini, fim = t[0], t[1], t[2], t[3], t[4], t[5]
        s  = ts[tid]
        st_ = s["status"]
        aviso = s["aviso"]
        deps = DEPS.get(tid, [])

        if f_fase   != "Todas" and fase != f_fase:   continue
        if f_resp   != "Todos" and resp != f_resp:   continue
        if f_status != "Todos" and st_  != f_status: continue
        count += 1

        dep_str   = ", ".join(deps) if deps else "—"
        warn_icon = ' <span style="color:#ff5252;font-size:10px" title="' + aviso + '">[!]</span>' if aviso else ""
        rows += (
            f"<tr>"
            f"<td style='font-family:IBM Plex Mono,monospace;color:#8899aa'>{tid}</td>"
            f"<td><strong style='color:#e8f0f8'>{nome}</strong>{warn_icon}</td>"
            f"<td><span style='font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace'>{fase}</span></td>"
            f"<td>{rtag(resp)}</td>"
            f"<td style='font-family:IBM Plex Mono,monospace;font-size:10px'>{ini}</td>"
            f"<td style='font-family:IBM Plex Mono,monospace;font-size:10px'>{fim}</td>"
            f"<td>{sbadge(st_)}</td>"
            f"<td><span style='font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace'>{dep_str}</span></td>"
            f"</tr>"
        )

    st.markdown(f'<div style="font-size:11px;color:#8899aa;font-family:IBM Plex Mono,monospace;margin-bottom:10px">{count} tarefa(s) exibida(s)</div>', unsafe_allow_html=True)
    st.markdown(
        f"<table class='se-tbl'><thead><tr>"
        f"<th>ID</th><th>Tarefa</th><th>Fase</th><th>Responsável</th><th>Início</th><th>Fim</th><th>Status</th><th>Depende de</th>"
        f"</tr></thead><tbody>{rows}</tbody></table>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════
# TIMELINE
# ══════════════════════════════════════════════════════════
elif pagina == "📅 Timeline":
    st.markdown('<div class="sec-hdr">Timeline <span class="sec-sub">03/02 → 25/02/2025 · Gantt</span></div>', unsafe_allow_html=True)

    START      = datetime(2025, 2, 3)
    TOTAL_DAYS = 17

    header = "".join(
        f'<th style="font-size:8px;color:#8899aa;padding:3px 1px;text-align:center;min-width:22px">'
        f'{(START + timedelta(days=i)).strftime("%d/%m")}</th>'
        for i in range(TOTAL_DAYS)
    )

    rows = ""
    for fase in FASES:
        rows += (
            f'<tr><td colspan="{TOTAL_DAYS + 2}" style="padding:6px 11px 2px;'
            f'font-family:IBM Plex Mono,monospace;font-size:9px;color:#f5a623;'
            f'letter-spacing:.1em;text-transform:uppercase;background:#111827">{fase}</td></tr>'
        )
        for t in TASKS_RAW:
            if t[0] != fase: continue
            tid, nome, resp, ini, fim = t[1], t[2], t[3], t[4], t[5]
            st_ = ts[tid]["status"]
            bar_cls = {"concluido": "bar-done", "em andamento": "bar-wip", "bloqueado": "bar-blk"}.get(st_, "bar-pend")
            try:
                s_d   = datetime.strptime(ini, "%Y-%m-%d")
                e_d   = datetime.strptime(fim, "%Y-%m-%d")
                s_off = (s_d - START).days
                dur   = max(1, (e_d - s_d).days + 1)
                s_pct = round(max(0, s_off) / TOTAL_DAYS * 100, 1)
                w_pct = round(dur / TOTAL_DAYS * 100, 1)
            except:
                s_pct, w_pct = 0, 6
            short = nome[:34] + "..." if len(nome) > 34 else nome
            rows += (
                f"<tr>"
                f"<td style='font-size:11px;color:#c8d8e8;padding:3px 11px;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis' title='{nome}'>{short}</td>"
                f"<td style='padding:2px 6px'>{rtag(resp)}</td>"
                f"<td colspan='{TOTAL_DAYS}' style='padding:2px 0'>"
                f"<div class='tl-track'>"
                f"<div class='tl-fill {bar_cls}' style='left:{s_pct}%;width:{w_pct}%'>{tid}</div>"
                f"</div></td>"
                f"</tr>"
            )

    st.markdown(
        f"<div style='overflow-x:auto'>"
        f"<table class='se-tbl' style='min-width:700px'>"
        f"<thead><tr><th>Tarefa</th><th>Resp.</th>{header}</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True
    )

    # Legenda
    st.markdown("""
    <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap">
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#8899aa">
        <div style="width:20px;height:8px;background:linear-gradient(90deg,#1F4E79,#2E75B6);border-radius:1px"></div>Pendente</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#8899aa">
        <div style="width:20px;height:8px;background:linear-gradient(90deg,#1a5c35,#00e676);border-radius:1px"></div>Concluído</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#8899aa">
        <div style="width:20px;height:8px;background:linear-gradient(90deg,#5c3a0a,#f5a623);border-radius:1px"></div>Em Andamento</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#8899aa">
        <div style="width:20px;height:8px;background:linear-gradient(90deg,#5c0a0a,#ff5252);border-radius:1px"></div>Bloqueado</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# BLOQUEIOS
# ══════════════════════════════════════════════════════════
elif pagina == "🔴 Bloqueios":
    st.markdown('<div class="sec-hdr">Bloqueios e Dependências <span class="sec-sub">Itens que exigem atenção imediata</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="callout c-warn"><b>Atenção</b>Tarefas com avisos técnicos ou dependências pendentes que bloqueiam o avanço. Resolva antes de prosseguir.</div>', unsafe_allow_html=True)

    rows = ""
    for t in TASKS_RAW:
        tid = t[1]
        s   = ts[tid]
        aviso = s["aviso"]
        if not aviso and s["status"] != "bloqueado":
            continue
        # Deps pendentes
        deps_pend = []
        for dep in DEPS.get(tid, []):
            dep_task = next((x for x in TASKS_RAW if x[1] == dep), None)
            if dep_task and ts[dep]["status"] != "concluido":
                deps_pend.append(f"{dep}: {dep_task[2][:38]} [{ts[dep]['status']}]")
        deps_html = "".join(
            f'<br><span style="color:#f5a623;font-size:10px;font-family:IBM Plex Mono,monospace">↳ dep: {d}</span>'
            for d in deps_pend
        )
        rows += (
            f"<tr>"
            f"<td style='font-family:IBM Plex Mono,monospace;color:#ff5252'>{tid}</td>"
            f"<td><strong style='color:#e8f0f8'>{t[2]}</strong>{deps_html}</td>"
            f"<td><span style='font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace'>{t[0]}</span></td>"
            f"<td>{rtag(t[3])}</td>"
            f"<td style='font-size:11px;color:#ffaa00'>{aviso if aviso else '—'}</td>"
            f"<td>{sbadge(s['status'])}</td>"
            f"</tr>"
        )

    if rows:
        st.markdown(
            f"<table class='se-tbl'><thead><tr>"
            f"<th>ID</th><th>Tarefa / Deps Pendentes</th><th>Fase</th><th>Resp.</th><th>Aviso Técnico</th><th>Status</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>",
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="callout c-ok"><b>Tudo certo</b>Nenhum bloqueio ativo no momento 🎉</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ATUALIZAR
# ══════════════════════════════════════════════════════════
elif pagina == "✏️ Atualizar":
    st.markdown('<div class="sec-hdr">Atualizar Status de Tarefa</div>', unsafe_allow_html=True)
    st.markdown('<div class="callout c-info"><b>Como usar</b>Selecione a tarefa, atualize o status e clique em Salvar. O dashboard e todos os painéis atualizam automaticamente.</div>', unsafe_allow_html=True)

    # ── Formulário individual ──────────────────────────────
    tid_opts = [f"{t[1]} — {t[2]}" for t in TASKS_RAW]

    # selectbox fora do form para atualizar o preview ao vivo
    sel     = st.selectbox("Tarefa", tid_opts, key="sel_tarefa")
    tid_sel = sel.split(" — ")[0]

    t_sel = next(t for t in TASKS_RAW if t[1] == tid_sel)
    deps  = DEPS.get(tid_sel, [])

    # Preview acima do form
    deps_html = ""
    for dep in deps:
        dep_task = next((x for x in TASKS_RAW if x[1] == dep), None)
        if dep_task:
            dep_st = ts[dep]["status"]
            color  = "#00e676" if dep_st == "concluido" else "#f5a623" if dep_st == "em andamento" else "#ff5252" if dep_st == "bloqueado" else "#8899aa"
            deps_html += f'<div style="font-size:11px;font-family:IBM Plex Mono,monospace;color:{color};margin-bottom:3px">↳ {dep}: {dep_task[2][:42]} <span style="color:{color}">[{dep_st}]</span></div>'

    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1a2235;border-radius:6px;padding:16px;margin-bottom:16px">
      <div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#f5a623;margin-bottom:4px;letter-spacing:.06em">{tid_sel} · {t_sel[0]}</div>
      <div style="font-size:14px;color:#e8f0f8;font-weight:600;margin-bottom:8px">{t_sel[2]}</div>
      <div style="margin-bottom:8px">{rtag(t_sel[3])}</div>
      <div style="font-size:11px;color:#8899aa;font-family:IBM Plex Mono,monospace">{t_sel[4]} → {t_sel[5]}</div>
      {"<div style='margin-top:10px;font-size:9px;color:#8899aa;font-family:IBM Plex Mono,monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px'>Dependências</div>" + deps_html if deps_html else ""}
    </div>
    """, unsafe_allow_html=True)

    # Form para evitar rerun dentro de colunas
    with st.form("form_atualizar", clear_on_submit=False):
        cur_status = ts[tid_sel]["status"]
        cur_aviso  = ts[tid_sel]["aviso"]
        new_status = st.selectbox("Novo Status", STATUS_OPT, index=STATUS_OPT.index(cur_status))
        new_aviso  = st.text_area("Aviso / Bloqueio (opcional)", value=cur_aviso, height=80)
        submitted  = st.form_submit_button("💾  Salvar Alteração", type="primary", use_container_width=True)

    if submitted:
        st.session_state.task_state[tid_sel]["status"] = new_status
        st.session_state.task_state[tid_sel]["aviso"]  = new_aviso.strip()
        st.success(f"✅ **{tid_sel}** atualizado para **{new_status}**")
        st.rerun()

    # ── Atalho: marcar fase inteira ────────────────────────
    st.divider()
    st.markdown('<div style="font-size:10px;color:#8899aa;font-family:IBM Plex Mono,monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:10px">Atalho — Marcar fase inteira</div>', unsafe_allow_html=True)

    with st.form("form_bulk", clear_on_submit=False):
        fase_sel    = st.selectbox("Fase", FASES)
        status_bulk = st.selectbox("Novo status para todas as tarefas", STATUS_OPT)
        submitted_bulk = st.form_submit_button("Aplicar a toda a fase", use_container_width=True)

    if submitted_bulk:
        for t in TASKS_RAW:
            if t[0] == fase_sel:
                st.session_state.task_state[t[1]]["status"] = status_bulk
        st.success(f"✅ Todas as tarefas de **{fase_sel}** → **{status_bulk}**")
        st.rerun()
