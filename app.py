"""
SE Suite 2.1 — Installation Pipeline Manager
============================================
Streamlit application to manage and track SE Suite installation pipelines.
Supports up to 2 distinct installations with granular phase control.

Run:
    streamlit run app.py

Requirements:
    pip install streamlit pandas plotly
"""

import streamlit as st
import json
import os
from datetime import datetime, date
from pathlib import Path
import copy

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SE Suite 2.1 — Pipeline Manager",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CONSTANTS & DATA MODEL
# ─────────────────────────────────────────────────────────────
DATA_FILE = "sesuite_pipeline_data.json"

STATUS_OPTIONS = ["Pendente", "Em Andamento", "Concluído", "Bloqueado", "Ignorado"]
STATUS_COLORS = {
    "Pendente":     "#94a3b8",
    "Em Andamento": "#f59e0b",
    "Concluído":    "#22c55e",
    "Bloqueado":    "#ef4444",
    "Ignorado":     "#cbd5e1",
}
STATUS_ICONS = {
    "Pendente":     "⬜",
    "Em Andamento": "🔄",
    "Concluído":    "✅",
    "Bloqueado":    "🔴",
    "Ignorado":     "➖",
}
PRIORITY_ICONS = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}

TEAMS = ["Infraestrutura", "DBA", "Segurança", "Dev / Arquitetura", "PM / Negócio", "Suporte / Help Desk"]

# ─────────────────────────────────────────────────────────────
# PIPELINE PHASES DEFINITION
# ─────────────────────────────────────────────────────────────
PIPELINE_PHASES = [
    {
        "id": "so_servidor",
        "name": "Sistema Operacional (Servidor)",
        "icon": "🖥️",
        "category": "Infraestrutura",
        "description": "Provisionar e configurar o SO do servidor de aplicação.",
        "tasks": [
            {"id": "so_01", "name": "Escolher distro Linux (Ubuntu 20.04 LTS recomendado)", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "so_02", "name": "Provisionar VM/servidor físico com requisitos de hardware", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "so_03", "name": "Instalar dependências Linux (gcc, libpng, libxml2, openssl, etc.)", "priority": "Alta", "team": "Infraestrutura", "notes": "Seção 6.8.2 da documentação"},
            {"id": "so_04", "name": "Instalar NGinx 1.20 (compilado — não usar pacotes RPM/DEB)", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "so_05", "name": "Configurar NGinx como proxy reverso para Tomcat", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "so_06", "name": "Copiar fontes de relatórios (Arial, Verdana) para /usr/X11R6/…/truetype", "priority": "Média", "team": "Infraestrutura", "notes": ""},
        ],
    },
    {
        "id": "java_middleware",
        "name": "Java & Middleware",
        "icon": "☕",
        "category": "Infraestrutura",
        "description": "Instalar Java, Tomcat, PHP e .NET no servidor.",
        "tasks": [
            {"id": "jm_01", "name": "Instalar AdoptOpenJDK 8 JDK HotSpot (x64)", "priority": "Alta", "team": "Infraestrutura", "notes": "Recomendado para evitar licença Oracle"},
            {"id": "jm_02", "name": "Instalar Apache Tomcat 9.x", "priority": "Alta", "team": "Infraestrutura", "notes": "Recomendado na 2.1.9"},
            {"id": "jm_03", "name": "Instalar PHP 7.4 (apenas uma instância por servidor)", "priority": "Alta", "team": "Infraestrutura", "notes": "Instalado automaticamente em Windows"},
            {"id": "jm_04", "name": "Instalar .NET 4.5 ou superior", "priority": "Média", "team": "Infraestrutura", "notes": "Obrigatório para conversão PDF e SE Captura"},
            {"id": "jm_05", "name": "Validar variáveis de ambiente JAVA_HOME e PATH", "priority": "Média", "team": "Infraestrutura", "notes": ""},
        ],
    },
    {
        "id": "banco_dados",
        "name": "Banco de Dados",
        "icon": "🗄️",
        "category": "Banco de Dados",
        "description": "Provisionar, configurar e parametrizar o SGBD para o SE Suite.",
        "tasks": [
            {"id": "bd_01", "name": "Provisionar servidor dedicado de banco de dados", "priority": "Alta", "team": "DBA", "notes": "Nunca no mesmo servidor da aplicação"},
            {"id": "bd_02", "name": "Instalar SGBD escolhido (SQL Server 2019 recomendado)", "priority": "Alta", "team": "DBA", "notes": ""},
            {"id": "bd_03", "name": "Criar base de dados com Collation correto (Latin1_General_CI_AI)", "priority": "Alta", "team": "DBA", "notes": "Para novas bases na 2.1+"},
            {"id": "bd_04", "name": "Habilitar READ_COMMITTED_SNAPSHOT para evitar locks", "priority": "Alta", "team": "DBA", "notes": "ALTER DATABASE ... SET READ_COMMITTED_SNAPSHOT ON"},
            {"id": "bd_05", "name": "Configurar parâmetros de performance (seção 6.9.1)", "priority": "Alta", "team": "DBA", "notes": "Effective cache, shared buffers, max connections, etc."},
            {"id": "bd_06", "name": "Criar usuário de banco com permissões adequadas (idioma: Inglês para SQL Server)", "priority": "Alta", "team": "DBA", "notes": ""},
            {"id": "bd_07", "name": "Configurar política de backup e restore", "priority": "Alta", "team": "DBA", "notes": ""},
            {"id": "bd_08", "name": "Dimensionar tablespaces/datafiles (Oracle: 2GB dados + 200MB índices)", "priority": "Média", "team": "DBA", "notes": "Apenas para Oracle"},
            {"id": "bd_09", "name": "Testar conectividade entre servidor de aplicação e banco", "priority": "Alta", "team": "DBA", "notes": ""},
        ],
    },
    {
        "id": "seguranca",
        "name": "Segurança & Certificados",
        "icon": "🔒",
        "category": "Segurança",
        "description": "Configurar HTTPS, firewall, certificados e políticas de segurança.",
        "tasks": [
            {"id": "sec_01", "name": "Emitir certificado HTTPS válido (Let's Encrypt recomendado)", "priority": "Alta", "team": "Segurança", "notes": "Obrigatório na versão 2.1"},
            {"id": "sec_02", "name": "Configurar redirecionamento HTTP → HTTPS no NGinx/IIS", "priority": "Alta", "team": "Segurança", "notes": ""},
            {"id": "sec_03", "name": "Configurar firewall: portas dos serviços SE Suite", "priority": "Alta", "team": "Segurança", "notes": ""},
            {"id": "sec_04", "name": "Adicionar URL do SE Suite como exceção em antivírus/proxy/URL Scan", "priority": "Alta", "team": "Segurança", "notes": ""},
            {"id": "sec_05", "name": "Configurar servidor de e-mail (SMTP/SSL-TLS) para notificações", "priority": "Média", "team": "Segurança", "notes": "Verificar regras de filtro de e-mail"},
            {"id": "sec_06", "name": "Configurar integração LDAP/AD ou SAML 2.0 (se aplicável)", "priority": "Média", "team": "Segurança", "notes": "ADFS ou AzureAD como IdP SAML"},
            {"id": "sec_07", "name": "Configurar renovação automática do certificado (certbot renew)", "priority": "Média", "team": "Segurança", "notes": ""},
        ],
    },
    {
        "id": "elasticsearch",
        "name": "Serviço de Indexação",
        "icon": "🔍",
        "category": "Infraestrutura",
        "description": "Instalar e configurar Elasticsearch para buscas rápidas.",
        "tasks": [
            {"id": "es_01", "name": "Instalar Elasticsearch 6.8.3 (embarcado ou externo)", "priority": "Alta", "team": "Infraestrutura", "notes": "Versão recomendada para on-premise"},
            {"id": "es_02", "name": "Instalar plugin: Ingest Attachment Processor Plugin", "priority": "Alta", "team": "Infraestrutura", "notes": "Obrigatório"},
            {"id": "es_03", "name": "Dimensionar heap size (máx 50% da RAM disponível)", "priority": "Alta", "team": "Infraestrutura", "notes": "0-50k arquivos: 2GB; 50-200k: 3GB; 200-500k: 5GB"},
            {"id": "es_04", "name": "Testar indexação e busca de documentos de teste", "priority": "Média", "team": "Infraestrutura", "notes": ""},
        ],
    },
    {
        "id": "filemanager",
        "name": "Servidor FileManager",
        "icon": "📂",
        "category": "Infraestrutura",
        "description": "Servidor dedicado para gerenciamento de arquivos.",
        "tasks": [
            {"id": "fm_01", "name": "Provisionar servidor dedicado para FileManager", "priority": "Alta", "team": "Infraestrutura", "notes": "Não deve ter outros serviços instalados"},
            {"id": "fm_02", "name": "Instalar Java 8 no servidor FileManager", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "fm_03", "name": "Instalar Apache Tomcat 9 no servidor FileManager", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "fm_04", "name": "Configurar diretório controlado para armazenamento de arquivos", "priority": "Alta", "team": "Infraestrutura", "notes": "Recomendado NAS para alta disponibilidade"},
        ],
    },
    {
        "id": "instalacao_suite",
        "name": "Instalação do SE Suite",
        "icon": "📦",
        "category": "Aplicação",
        "description": "Deploy e configuração inicial do SE Suite 2.1.9.",
        "tasks": [
            {"id": "inst_01", "name": "Executar instalação do SE Suite 2.1.9 em homologação", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "inst_02", "name": "Validar execução dos scripts SQL de criação de objetos", "priority": "Alta", "team": "DBA", "notes": "Instalação concluída apenas se scripts rodarem com sucesso"},
            {"id": "inst_03", "name": "Configurar URL base, HTTPS, e-mail e diretório controlado", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "inst_04", "name": "Configurar Microsoft Office Professional 2016+ para conversão PDF", "priority": "Alta", "team": "Infraestrutura", "notes": "Versão recomendada para conversor PDF"},
            {"id": "inst_05", "name": "Distribuir VectorDraw File Converter (MSI) para estações com DWG", "priority": "Média", "team": "Suporte / Help Desk", "notes": ""},
            {"id": "inst_06", "name": "Configurar parâmetros gerais no painel de administração do SE Suite", "priority": "Alta", "team": "PM / Negócio", "notes": ""},
        ],
    },
    {
        "id": "estacoes",
        "name": "Estações de Trabalho",
        "icon": "💻",
        "category": "Suporte",
        "description": "Preparar estações de trabalho dos usuários finais.",
        "tasks": [
            {"id": "est_01", "name": "Padronizar Google Chrome 90+ (recomendado) ou Microsoft Edge novo", "priority": "Alta", "team": "Suporte / Help Desk", "notes": "IE11 e Edge Legacy descontinuados"},
            {"id": "est_02", "name": "Verificar/instalar .NET Framework 4.5+ nas estações", "priority": "Alta", "team": "Suporte / Help Desk", "notes": ""},
            {"id": "est_03", "name": "Verificar/instalar Java 1.8 nas estações (para SE Projeto/Gantt)", "priority": "Média", "team": "Suporte / Help Desk", "notes": ""},
            {"id": "est_04", "name": "Configurar browser: habilitar popups, download, scripts para URL do SE Suite", "priority": "Alta", "team": "Suporte / Help Desk", "notes": "Adicionar URL em Trusted Sites (IE/Edge)"},
            {"id": "est_05", "name": "Verificar Microsoft Office instalado (Word, Excel, Visio) para SE Documento", "priority": "Média", "team": "Suporte / Help Desk", "notes": ""},
        ],
    },
    {
        "id": "validacao",
        "name": "Testes & Validação",
        "icon": "🧪",
        "category": "QA",
        "description": "Testes funcionais, UAT e validação de performance.",
        "tasks": [
            {"id": "val_01", "name": "Testar acesso HTTPS sem avisos de certificado", "priority": "Alta", "team": "Segurança", "notes": ""},
            {"id": "val_02", "name": "Testes de carga com usuários simultâneos esperados", "priority": "Alta", "team": "Infraestrutura", "notes": "JMeter ou k6"},
            {"id": "val_03", "name": "UAT com usuários-chave por módulo (Documento, Processo, Qualidade)", "priority": "Alta", "team": "PM / Negócio", "notes": ""},
            {"id": "val_04", "name": "Validar conversão e visualização de PDF e DWG", "priority": "Média", "team": "Dev / Arquitetura", "notes": ""},
            {"id": "val_05", "name": "Validar notificações de e-mail e relatórios gerados", "priority": "Média", "team": "Dev / Arquitetura", "notes": ""},
            {"id": "val_06", "name": "Validar acesso mobile (Android/iOS — app e navegador)", "priority": "Média", "team": "Suporte / Help Desk", "notes": ""},
            {"id": "val_07", "name": "Documentar evidências e obter aprovação formal de homologação", "priority": "Alta", "team": "PM / Negócio", "notes": ""},
        ],
    },
    {
        "id": "golive",
        "name": "Go-Live & Produção",
        "icon": "🚀",
        "category": "Operações",
        "description": "Cutover para produção e monitoramento inicial.",
        "tasks": [
            {"id": "gl_01", "name": "Realizar backup completo do banco e arquivos antes do cutover", "priority": "Alta", "team": "DBA", "notes": ""},
            {"id": "gl_02", "name": "Executar instalação/atualização em produção na janela de manutenção", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "gl_03", "name": "Smoke tests pós-deploy: acesso, login, módulos, e-mail, relatório", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "gl_04", "name": "Monitorar logs de aplicação e banco nas primeiras 4 horas", "priority": "Alta", "team": "Infraestrutura", "notes": ""},
            {"id": "gl_05", "name": "Comunicar usuários sobre go-live e canal de suporte", "priority": "Média", "team": "PM / Negócio", "notes": ""},
            {"id": "gl_06", "name": "Avaliar contratação RSA (Administração Remota SoftExpert)", "priority": "Baixa", "team": "PM / Negócio", "notes": "Recomendado para On-Premise"},
        ],
    },
]

CATEGORY_COLORS = {
    "Infraestrutura": "#3b82f6",
    "Banco de Dados":  "#8b5cf6",
    "Segurança":       "#ef4444",
    "Aplicação":       "#f59e0b",
    "Suporte":         "#6b7280",
    "QA":              "#10b981",
    "Operações":       "#f97316",
}

# ─────────────────────────────────────────────────────────────
# DATA PERSISTENCE
# ─────────────────────────────────────────────────────────────
def load_data() -> dict:
    """Load pipeline data from JSON file or initialize defaults."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _default_data()


def save_data(data: dict) -> None:
    """Persist pipeline data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _default_data() -> dict:
    """Build the default data structure for two installations."""
    installations = {}
    for idx in range(1, 3):
        inst_id = f"inst_{idx}"
        phases = {}
        for phase in PIPELINE_PHASES:
            tasks = {}
            for task in phase["tasks"]:
                tasks[task["id"]] = {
                    "status": "Pendente",
                    "assignee": "",
                    "due_date": "",
                    "notes": task["notes"],
                    "completed_at": "",
                }
            phases[phase["id"]] = {
                "enabled": True,
                "status": "Pendente",
                "tasks": tasks,
            }
        installations[inst_id] = {
            "name": f"Instalação {idx}",
            "environment": "Produção" if idx == 1 else "Homologação",
            "description": "",
            "created_at": datetime.now().isoformat(),
            "target_date": "",
            "sgbd": "SQL Server 2019",
            "os_server": "Ubuntu 20.04 LTS",
            "active": idx == 1,
            "phases": phases,
        }
    return {"installations": installations, "last_updated": datetime.now().isoformat()}


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def get_phase_progress(phase_data: dict) -> tuple[int, int]:
    """Return (completed, total) for enabled tasks in a phase."""
    tasks = phase_data.get("tasks", {})
    total = len(tasks)
    completed = sum(1 for t in tasks.values() if t["status"] == "Concluído")
    return completed, total


def get_installation_progress(inst_data: dict) -> tuple[int, int]:
    """Return overall (completed, total) tasks for an installation."""
    completed_total, grand_total = 0, 0
    for phase_id, phase_data in inst_data["phases"].items():
        if not phase_data["enabled"]:
            continue
        c, t = get_phase_progress(phase_data)
        completed_total += c
        grand_total += t
    return completed_total, grand_total


def compute_phase_status(phase_data: dict) -> str:
    """Auto-derive phase status from its tasks."""
    tasks = phase_data.get("tasks", {})
    if not tasks:
        return "Pendente"
    statuses = [t["status"] for t in tasks.values()]
    if all(s == "Concluído" or s == "Ignorado" for s in statuses):
        return "Concluído"
    if any(s == "Bloqueado" for s in statuses):
        return "Bloqueado"
    if any(s == "Em Andamento" or s == "Concluído" for s in statuses):
        return "Em Andamento"
    return "Pendente"


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#94a3b8")
    icon = STATUS_ICONS.get(status, "")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600">{icon} {status}</span>'


def progress_bar_html(pct: float, color: str = "#22c55e") -> str:
    return f"""
    <div style="background:#e2e8f0;border-radius:8px;height:10px;overflow:hidden">
      <div style="background:{color};width:{pct:.0f}%;height:100%;border-radius:8px;transition:width 0.4s ease"></div>
    </div>"""


# ─────────────────────────────────────────────────────────────
# CSS INJECTION
# ─────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

      html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

      .main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }

      /* Header card */
      .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        border: 1px solid #334155;
      }
      .header-card h1 { color: white; font-size: 1.6rem; font-weight: 700; margin: 0; }
      .header-card p  { color: #94a3b8; font-size: 14px; margin: 4px 0 0 0; }

      /* Metric cards */
      .metric-row { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }
      .metric-card {
        flex: 1; min-width: 140px;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,.06);
      }
      .metric-card .num  { font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1; }
      .metric-card .lbl  { font-size: 12px; color: #64748b; font-weight: 500; margin-top: 4px; }
      .metric-card.accent .num { color: #3b82f6; }
      .metric-card.green  .num { color: #22c55e; }
      .metric-card.orange .num { color: #f59e0b; }
      .metric-card.red    .num { color: #ef4444; }

      /* Phase card */
      .phase-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,.04);
        transition: box-shadow 0.2s;
      }
      .phase-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
      .phase-card.disabled { opacity: 0.45; background: #f8fafc; }

      .phase-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }
      .phase-title { font-size: 15px; font-weight: 600; color: #0f172a; }
      .phase-category {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        color: white;
        margin-left: 8px;
      }

      /* Task row */
      .task-row {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        background: #f8fafc;
        border: 1px solid #f1f5f9;
        gap: 10px;
        font-size: 13px;
      }
      .task-row.done  { background: #f0fdf4; border-color: #bbf7d0; }
      .task-row.block { background: #fff1f2; border-color: #fecdd3; }
      .task-row.prog  { background: #fffbeb; border-color: #fde68a; }

      /* Sidebar */
      section[data-testid="stSidebar"] { background: #0f172a !important; }
      section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
      section[data-testid="stSidebar"] .stSelectbox label,
      section[data-testid="stSidebar"] .stRadio label { color: #94a3b8 !important; font-size: 12px !important; }

      /* Streamlit overrides */
      .stExpander { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
      .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
      }
      .stTabs [data-baseweb="tab"] { font-weight: 600 !important; font-size: 14px !important; }

      /* Divider */
      hr { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }

      /* Timeline bar */
      .timeline-phase {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        gap: 12px;
        font-size: 13px;
      }
      .timeline-phase .label { width: 200px; color: #334155; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .timeline-bar-wrap { flex: 1; background: #f1f5f9; border-radius: 6px; height: 22px; overflow: hidden; }
      .timeline-bar { height: 100%; border-radius: 6px; display: flex; align-items: center; padding-left: 8px; font-size: 11px; color: white; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
def render_sidebar(data: dict) -> tuple[str, str]:
    """Render sidebar navigation. Returns (active_installation_id, active_view)."""
    with st.sidebar:
        st.markdown("## ⚙️ SE Suite Manager")
        st.markdown("---")

        # Installation selector
        st.markdown("**INSTALAÇÃO ATIVA**")
        inst_options = {
            iid: f"{'🟢' if d['active'] else '⚫'} {d['name']} ({d['environment']})"
            for iid, d in data["installations"].items()
        }
        selected_inst = st.radio(
            "Selecionar instalação",
            options=list(inst_options.keys()),
            format_func=lambda x: inst_options[x],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("**NAVEGAÇÃO**")
        view = st.radio(
            "Visualização",
            options=["🏠 Dashboard", "📋 Pipeline", "⚙️ Configurações", "📊 Relatório"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        # Quick stats in sidebar
        inst = data["installations"][selected_inst]
        done, total = get_installation_progress(inst)
        pct = (done / total * 100) if total else 0
        enabled_phases = sum(1 for p in inst["phases"].values() if p["enabled"])

        st.markdown("**STATUS RÁPIDO**")
        st.markdown(f"- **Fases ativas:** {enabled_phases}/{len(PIPELINE_PHASES)}")
        st.markdown(f"- **Tarefas:** {done}/{total} ({pct:.0f}%)")
        st.markdown(f"- **SGBD:** {inst.get('sgbd', '—')}")
        st.markdown(f"- **SO Servidor:** {inst.get('os_server', '—')}")

        st.markdown("---")
        if st.button("💾 Salvar Dados"):
            save_data(data)
            st.success("Dados salvos!")

        st.markdown(
            "<p style='font-size:11px;color:#475569;margin-top:16px'>SE Suite 2.1.9<br>Pipeline Manager v1.0</p>",
            unsafe_allow_html=True,
        )

    return selected_inst, view


# ─────────────────────────────────────────────────────────────
# DASHBOARD VIEW
# ─────────────────────────────────────────────────────────────
def render_dashboard(data: dict, inst_id: str):
    inst = data["installations"][inst_id]
    done, total = get_installation_progress(inst)
    pct = (done / total * 100) if total else 0

    # Header
    st.markdown(f"""
    <div class="header-card">
      <h1>🏠 Dashboard — {inst['name']}</h1>
      <p>{inst['environment']} · {inst.get('description') or 'Sem descrição'} · SGBD: {inst.get('sgbd','—')} · SO: {inst.get('os_server','—')}</p>
    </div>""", unsafe_allow_html=True)

    # KPI metrics
    blocked = sum(
        1 for ph in inst["phases"].values() if ph["enabled"]
        for t in ph["tasks"].values() if t["status"] == "Bloqueado"
    )
    in_progress = sum(
        1 for ph in inst["phases"].values() if ph["enabled"]
        for t in ph["tasks"].values() if t["status"] == "Em Andamento"
    )
    enabled_phases = sum(1 for p in inst["phases"].values() if p["enabled"])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Progresso Geral", f"{pct:.0f}%")
    with col2:
        st.metric("Tarefas Concluídas", f"{done}/{total}")
    with col3:
        st.metric("Em Andamento", in_progress)
    with col4:
        st.metric("Bloqueadas", blocked, delta=f"-{blocked}" if blocked else None, delta_color="inverse")
    with col5:
        st.metric("Fases Ativas", f"{enabled_phases}/{len(PIPELINE_PHASES)}")

    # Global progress bar
    st.markdown(f"**Progresso total: {pct:.0f}%**")
    color = "#22c55e" if pct == 100 else "#3b82f6" if pct > 50 else "#f59e0b"
    st.markdown(progress_bar_html(pct, color), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Per-phase progress
    st.markdown("### 📊 Progresso por Fase")
    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"], {})
        if not ph_data.get("enabled", True):
            st.markdown(
                f'<div style="opacity:.4;font-size:13px;padding:6px 0">➖ {phase["icon"]} **{phase["name"]}** — *desabilitada*</div>',
                unsafe_allow_html=True,
            )
            continue

        c, t = get_phase_progress(ph_data)
        p = (c / t * 100) if t else 0
        auto_status = compute_phase_status(ph_data)
        cat_color = CATEGORY_COLORS.get(phase["category"], "#64748b")

        col_a, col_b, col_c = st.columns([3, 6, 1])
        with col_a:
            st.markdown(
                f'{phase["icon"]} **{phase["name"]}** '
                f'<span class="phase-category" style="background:{cat_color}">{phase["category"]}</span>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(progress_bar_html(p, cat_color), unsafe_allow_html=True)
            st.caption(f"{c}/{t} tarefas")
        with col_c:
            st.markdown(status_badge(auto_status), unsafe_allow_html=True)

    # Both installations comparison
    st.markdown("---")
    st.markdown("### ⚖️ Comparação entre Instalações")
    cols = st.columns(2)
    for i, (iid, idata) in enumerate(data["installations"].items()):
        with cols[i]:
            d2, t2 = get_installation_progress(idata)
            p2 = (d2 / t2 * 100) if t2 else 0
            active_label = "🟢 Ativa" if iid == inst_id else ""
            st.markdown(f"**{idata['name']}** {active_label}")
            st.markdown(f"*{idata['environment']}*")
            st.markdown(progress_bar_html(p2, "#3b82f6"), unsafe_allow_html=True)
            st.caption(f"{d2}/{t2} tarefas — {p2:.0f}%")


# ─────────────────────────────────────────────────────────────
# PIPELINE VIEW
# ─────────────────────────────────────────────────────────────
def render_pipeline(data: dict, inst_id: str):
    inst = data["installations"][inst_id]

    st.markdown(f"""
    <div class="header-card">
      <h1>📋 Pipeline — {inst['name']}</h1>
      <p>Gerencie fases e tarefas individuais desta instalação.</p>
    </div>""", unsafe_allow_html=True)

    # Filter controls
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        filter_status = st.multiselect(
            "Filtrar por status",
            options=STATUS_OPTIONS,
            default=[],
            placeholder="Todos os status",
        )
    with col_f2:
        filter_team = st.multiselect(
            "Filtrar por equipe",
            options=TEAMS,
            default=[],
            placeholder="Todas as equipes",
        )
    with col_f3:
        filter_priority = st.multiselect(
            "Filtrar por prioridade",
            options=["Alta", "Média", "Baixa"],
            default=[],
            placeholder="Todas as prioridades",
        )

    st.markdown("---")

    # Render each phase
    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"])
        if not ph_data:
            continue

        enabled = ph_data.get("enabled", True)
        c, t = get_phase_progress(ph_data)
        pct = (c / t * 100) if t else 0
        auto_status = compute_phase_status(ph_data)
        cat_color = CATEGORY_COLORS.get(phase["category"], "#64748b")

        with st.expander(
            f"{phase['icon']} {phase['name']}  —  {'✅ ' if auto_status == 'Concluído' else ''}{c}/{t} tarefas  {'(DESABILITADA)' if not enabled else ''}",
            expanded=(auto_status in ("Em Andamento", "Bloqueado") and enabled),
        ):
            # Phase header controls
            hcol1, hcol2, hcol3 = st.columns([5, 2, 2])
            with hcol1:
                st.markdown(
                    f'<span class="phase-category" style="background:{cat_color}">{phase["category"]}</span> '
                    f'<small style="color:#64748b">{phase["description"]}</small>',
                    unsafe_allow_html=True,
                )
            with hcol2:
                new_enabled = st.checkbox(
                    "Fase ativa",
                    value=enabled,
                    key=f"enabled_{inst_id}_{phase['id']}",
                )
                if new_enabled != enabled:
                    inst["phases"][phase["id"]]["enabled"] = new_enabled
                    save_data(data)
                    st.rerun()
            with hcol3:
                st.markdown(progress_bar_html(pct, cat_color), unsafe_allow_html=True)
                st.caption(f"{pct:.0f}% concluído")

            if not enabled:
                st.info("Esta fase está desabilitada e não será contabilizada no progresso.")
                continue

            st.markdown("---")

            # Render tasks
            for task_def in phase["tasks"]:
                task_id = task_def["id"]
                task_state = ph_data["tasks"].get(task_id, {})
                task_status = task_state.get("status", "Pendente")

                # Apply filters
                team_for_task = task_def.get("team", "")
                prio_for_task = task_def.get("priority", "Média")
                if filter_status and task_status not in filter_status:
                    continue
                if filter_team and team_for_task not in filter_team:
                    continue
                if filter_priority and prio_for_task not in filter_priority:
                    continue

                row_class = (
                    "done"  if task_status == "Concluído"    else
                    "block" if task_status == "Bloqueado"    else
                    "prog"  if task_status == "Em Andamento" else ""
                )

                with st.container():
                    tc1, tc2, tc3, tc4 = st.columns([5, 2, 2, 1])
                    with tc1:
                        prio_icon = PRIORITY_ICONS.get(prio_for_task, "")
                        st.markdown(
                            f'{prio_icon} **{task_def["name"]}**  '
                            f'<span style="font-size:11px;color:#64748b">— {team_for_task}</span>',
                            unsafe_allow_html=True,
                        )
                        if task_state.get("notes"):
                            st.caption(f"📎 {task_state['notes']}")
                    with tc2:
                        new_status = st.selectbox(
                            "Status",
                            options=STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(task_status),
                            key=f"status_{inst_id}_{task_id}",
                            label_visibility="collapsed",
                        )
                        if new_status != task_status:
                            inst["phases"][phase["id"]]["tasks"][task_id]["status"] = new_status
                            if new_status == "Concluído":
                                inst["phases"][phase["id"]]["tasks"][task_id]["completed_at"] = datetime.now().isoformat()
                            save_data(data)
                            st.rerun()
                    with tc3:
                        assignee = st.text_input(
                            "Responsável",
                            value=task_state.get("assignee", ""),
                            placeholder="Nome…",
                            key=f"assignee_{inst_id}_{task_id}",
                            label_visibility="collapsed",
                        )
                        if assignee != task_state.get("assignee", ""):
                            inst["phases"][phase["id"]]["tasks"][task_id]["assignee"] = assignee
                            save_data(data)
                    with tc4:
                        if st.button("📝", key=f"note_btn_{inst_id}_{task_id}", help="Editar nota"):
                            st.session_state[f"show_note_{inst_id}_{task_id}"] = True

                    if st.session_state.get(f"show_note_{inst_id}_{task_id}"):
                        note = st.text_area(
                            "Nota / Observação",
                            value=task_state.get("notes", ""),
                            key=f"note_{inst_id}_{task_id}",
                            height=80,
                        )
                        if st.button("Salvar nota", key=f"save_note_{inst_id}_{task_id}"):
                            inst["phases"][phase["id"]]["tasks"][task_id]["notes"] = note
                            st.session_state[f"show_note_{inst_id}_{task_id}"] = False
                            save_data(data)
                            st.rerun()

                st.markdown('<hr style="border:none;border-top:1px solid #f1f5f9;margin:2px 0">', unsafe_allow_html=True)

            # Bulk actions for phase
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button(f"✅ Marcar todas como Concluído", key=f"bulk_done_{inst_id}_{phase['id']}"):
                    for tid in ph_data["tasks"]:
                        inst["phases"][phase["id"]]["tasks"][tid]["status"] = "Concluído"
                        inst["phases"][phase["id"]]["tasks"][tid]["completed_at"] = datetime.now().isoformat()
                    save_data(data)
                    st.rerun()
            with bcol2:
                if st.button(f"↩️ Resetar fase para Pendente", key=f"bulk_reset_{inst_id}_{phase['id']}"):
                    for tid in ph_data["tasks"]:
                        inst["phases"][phase["id"]]["tasks"][tid]["status"] = "Pendente"
                        inst["phases"][phase["id"]]["tasks"][tid]["completed_at"] = ""
                    save_data(data)
                    st.rerun()


# ─────────────────────────────────────────────────────────────
# CONFIGURATION VIEW
# ─────────────────────────────────────────────────────────────
def render_configuration(data: dict, inst_id: str):
    inst = data["installations"][inst_id]

    st.markdown(f"""
    <div class="header-card">
      <h1>⚙️ Configurações — {inst['name']}</h1>
      <p>Edite os metadados e ative/desative fases conforme o escopo da instalação.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("### 📝 Dados da Instalação")

    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        new_name = st.text_input("Nome da instalação", value=inst["name"], key=f"cfg_name_{inst_id}")
        new_env = st.selectbox(
            "Tipo de ambiente",
            options=["Produção", "Homologação", "Desenvolvimento", "DR", "Outro"],
            index=["Produção", "Homologação", "Desenvolvimento", "DR", "Outro"].index(inst.get("environment", "Produção")),
            key=f"cfg_env_{inst_id}",
        )
        new_desc = st.text_area("Descrição", value=inst.get("description", ""), key=f"cfg_desc_{inst_id}", height=80)
    with cfg_col2:
        new_sgbd = st.selectbox(
            "SGBD",
            options=["SQL Server 2019", "SQL Server 2017", "SQL Server 2016", "PostgreSQL 13", "PostgreSQL 12", "PostgreSQL 11", "Oracle 19c", "Oracle 18c"],
            index=0 if inst.get("sgbd") not in ["SQL Server 2019","SQL Server 2017","SQL Server 2016","PostgreSQL 13","PostgreSQL 12","PostgreSQL 11","Oracle 19c","Oracle 18c"] else ["SQL Server 2019","SQL Server 2017","SQL Server 2016","PostgreSQL 13","PostgreSQL 12","PostgreSQL 11","Oracle 19c","Oracle 18c"].index(inst.get("sgbd","SQL Server 2019")),
            key=f"cfg_sgbd_{inst_id}",
        )
        new_os = st.selectbox(
            "SO do Servidor",
            options=["Ubuntu 20.04 LTS", "Ubuntu 18.04 LTS", "CentOS 7", "Debian GNU/Linux 10", "Red Hat Enterprise Linux 8", "Oracle Linux 8.4", "Windows Server 2019", "Windows Server 2016"],
            index=0,
            key=f"cfg_os_{inst_id}",
        )
        new_target = st.date_input("Data alvo de go-live", key=f"cfg_target_{inst_id}")

    if st.button("💾 Salvar configurações", key=f"save_cfg_{inst_id}"):
        inst["name"] = new_name
        inst["environment"] = new_env
        inst["description"] = new_desc
        inst["sgbd"] = new_sgbd
        inst["os_server"] = new_os
        inst["target_date"] = str(new_target)
        save_data(data)
        st.success("✅ Configurações salvas com sucesso!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎛️ Escopo da Instalação — Fases Ativas")
    st.info("💡 Desabilite fases que não fazem parte do escopo desta operação. Por exemplo, para um **upgrade de banco de dados**, mantenha apenas a fase *Banco de Dados* ativa.")

    # Group phases by category
    categories = {}
    for phase in PIPELINE_PHASES:
        categories.setdefault(phase["category"], []).append(phase)

    for cat, phases_in_cat in categories.items():
        cat_color = CATEGORY_COLORS.get(cat, "#64748b")
        st.markdown(
            f'<span class="phase-category" style="background:{cat_color};font-size:13px;padding:4px 14px">{cat}</span>',
            unsafe_allow_html=True,
        )
        scope_cols = st.columns(len(phases_in_cat) if len(phases_in_cat) <= 4 else 4)
        for i, phase in enumerate(phases_in_cat):
            with scope_cols[i % 4]:
                current = inst["phases"][phase["id"]].get("enabled", True)
                new_val = st.checkbox(
                    f"{phase['icon']} {phase['name']}",
                    value=current,
                    key=f"scope_{inst_id}_{phase['id']}",
                )
                if new_val != current:
                    inst["phases"][phase["id"]]["enabled"] = new_val
                    save_data(data)
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔧 Ações Avançadas")
    danger_col1, danger_col2 = st.columns(2)
    with danger_col1:
        if st.button("🔄 Resetar TODA a instalação para Pendente", key=f"reset_all_{inst_id}"):
            for ph_id in inst["phases"]:
                for tid in inst["phases"][ph_id]["tasks"]:
                    inst["phases"][ph_id]["tasks"][tid]["status"] = "Pendente"
                    inst["phases"][ph_id]["tasks"][tid]["completed_at"] = ""
            save_data(data)
            st.success("Pipeline resetado.")
            st.rerun()
    with danger_col2:
        if st.button("📋 Copiar progresso para outra instalação", key=f"copy_{inst_id}"):
            other_id = [k for k in data["installations"] if k != inst_id][0]
            other = data["installations"][other_id]
            for ph_id in inst["phases"]:
                if ph_id in other["phases"]:
                    for tid in inst["phases"][ph_id]["tasks"]:
                        if tid in other["phases"][ph_id]["tasks"]:
                            other["phases"][ph_id]["tasks"][tid]["status"] = inst["phases"][ph_id]["tasks"][tid]["status"]
            save_data(data)
            st.success(f"Progresso copiado para {other['name']}!")


# ─────────────────────────────────────────────────────────────
# REPORT VIEW
# ─────────────────────────────────────────────────────────────
def render_report(data: dict, inst_id: str):
    inst = data["installations"][inst_id]
    done, total = get_installation_progress(inst)
    pct = (done / total * 100) if total else 0

    st.markdown(f"""
    <div class="header-card">
      <h1>📊 Relatório — {inst['name']}</h1>
      <p>Visão consolidada do estado atual da instalação.</p>
    </div>""", unsafe_allow_html=True)

    # Summary
    st.markdown("### 📈 Sumário Executivo")
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown(f"""
        **Instalação:** {inst['name']}  
        **Ambiente:** {inst['environment']}  
        **SGBD:** {inst.get('sgbd','—')}  
        **SO Servidor:** {inst.get('os_server','—')}
        """)
    with r1c2:
        st.markdown(f"""
        **Data alvo:** {inst.get('target_date') or '—'}  
        **Progresso:** {pct:.1f}%  
        **Tarefas concluídas:** {done}/{total}  
        **Fases ativas:** {sum(1 for p in inst['phases'].values() if p['enabled'])}/{len(PIPELINE_PHASES)}
        """)
    with r1c3:
        blocked = sum(
            1 for ph in inst["phases"].values() if ph["enabled"]
            for t in ph["tasks"].values() if t["status"] == "Bloqueado"
        )
        in_prog = sum(
            1 for ph in inst["phases"].values() if ph["enabled"]
            for t in ph["tasks"].values() if t["status"] == "Em Andamento"
        )
        pending = sum(
            1 for ph in inst["phases"].values() if ph["enabled"]
            for t in ph["tasks"].values() if t["status"] == "Pendente"
        )
        st.markdown(f"""
        **🔴 Bloqueadas:** {blocked}  
        **🔄 Em andamento:** {in_prog}  
        **⬜ Pendentes:** {pending}  
        **✅ Concluídas:** {done}
        """)

    st.markdown("---")
    st.markdown("### 🗂️ Status por Fase")

    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"])
        if not ph_data:
            continue
        enabled = ph_data.get("enabled", True)
        c, t = get_phase_progress(ph_data)
        p = (c / t * 100) if t else 0
        auto_status = compute_phase_status(ph_data)
        cat_color = CATEGORY_COLORS.get(phase["category"], "#64748b")

        rc1, rc2, rc3, rc4 = st.columns([3, 4, 2, 1])
        with rc1:
            disabled_txt = " *(desabilitada)*" if not enabled else ""
            st.markdown(f"{phase['icon']} **{phase['name']}**{disabled_txt}")
        with rc2:
            if enabled:
                st.markdown(progress_bar_html(p, cat_color), unsafe_allow_html=True)
                st.caption(f"{c}/{t} ({p:.0f}%)")
            else:
                st.caption("—")
        with rc3:
            st.markdown(status_badge(auto_status if enabled else "Ignorado"), unsafe_allow_html=True)
        with rc4:
            st.markdown(
                f'<span class="phase-category" style="background:{cat_color}">{phase["category"]}</span>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### 🔴 Itens Bloqueados")
    found_blocked = False
    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"], {})
        if not ph_data.get("enabled", True):
            continue
        for task_def in phase["tasks"]:
            tid = task_def["id"]
            task_state = ph_data["tasks"].get(tid, {})
            if task_state.get("status") == "Bloqueado":
                found_blocked = True
                st.error(
                    f"🔴 **{phase['icon']} {phase['name']}** → {task_def['name']}  \n"
                    f"Equipe: {task_def['team']} | Responsável: {task_state.get('assignee') or '—'}  \n"
                    f"Nota: {task_state.get('notes') or '—'}"
                )
    if not found_blocked:
        st.success("✅ Nenhum item bloqueado no momento.")

    st.markdown("---")
    st.markdown("### 🔄 Itens Em Andamento")
    found_prog = False
    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"], {})
        if not ph_data.get("enabled", True):
            continue
        for task_def in phase["tasks"]:
            tid = task_def["id"]
            task_state = ph_data["tasks"].get(tid, {})
            if task_state.get("status") == "Em Andamento":
                found_prog = True
                st.warning(
                    f"🔄 **{phase['icon']} {phase['name']}** → {task_def['name']}  \n"
                    f"Equipe: {task_def['team']} | Responsável: {task_state.get('assignee') or '—'}"
                )
    if not found_prog:
        st.info("Nenhum item em andamento no momento.")

    # Team workload
    st.markdown("---")
    st.markdown("### 👥 Carga por Equipe")
    team_stats: dict[str, dict[str, int]] = {team: {"total": 0, "done": 0, "blocked": 0} for team in TEAMS}
    for phase in PIPELINE_PHASES:
        ph_data = inst["phases"].get(phase["id"], {})
        if not ph_data.get("enabled", True):
            continue
        for task_def in phase["tasks"]:
            tid = task_def["id"]
            task_state = ph_data["tasks"].get(tid, {})
            team = task_def.get("team", "")
            if team in team_stats:
                team_stats[team]["total"] += 1
                if task_state.get("status") == "Concluído":
                    team_stats[team]["done"] += 1
                if task_state.get("status") == "Bloqueado":
                    team_stats[team]["blocked"] += 1

    tw_cols = st.columns(3)
    for i, (team, stats) in enumerate(team_stats.items()):
        if stats["total"] == 0:
            continue
        tp = (stats["done"] / stats["total"] * 100) if stats["total"] else 0
        with tw_cols[i % 3]:
            st.markdown(f"**{team}**")
            st.markdown(progress_bar_html(tp, "#3b82f6"), unsafe_allow_html=True)
            st.caption(f"{stats['done']}/{stats['total']} concluídas | {stats['blocked']} bloqueadas")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    inject_css()

    # Initialize session state
    if "data" not in st.session_state:
        st.session_state.data = load_data()

    data = st.session_state.data

    # Sidebar
    active_inst_id, active_view = render_sidebar(data)

    # Route to view
    if "Dashboard" in active_view:
        render_dashboard(data, active_inst_id)
    elif "Pipeline" in active_view:
        render_pipeline(data, active_inst_id)
    elif "Configurações" in active_view:
        render_configuration(data, active_inst_id)
    elif "Relatório" in active_view:
        render_report(data, active_inst_id)


if __name__ == "__main__":
    main()
