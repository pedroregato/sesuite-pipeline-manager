"""
auth.py — Camada de Autenticação para Business Modeling Studio
Usa: streamlit-authenticator + secrets.toml (Streamlit Community Cloud compatible)
Sem dependências externas além de hashlib (stdlib).
"""
import hashlib
import hmac
import streamlit as st
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────
# UTILITÁRIOS DE SENHA
# ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """SHA-256 com salt fixo por app. Para produção, use bcrypt."""
    salt = st.secrets.get("AUTH_SALT", "bms_poc_salt_2025")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

# ─────────────────────────────────────────────────────────────────
# BASE DE USUÁRIOS — lida do secrets.toml
# Estrutura esperada em .streamlit/secrets.toml:
#
# [users]
# [users.admin]
# name = "Administrador"
# password_hash = "abc123..."   # gerado por hash_password()
# role = "admin"
# email = "admin@empresa.com"
#
# [users.viewer]
# name = "Analista"
# password_hash = "xyz456..."
# role = "viewer"
# email = "analista@empresa.com"
# ─────────────────────────────────────────────────────────────────

def get_users() -> dict:
    """Carrega usuários do secrets.toml. Fallback para demo."""
    try:
        return dict(st.secrets["users"])
    except Exception:
        # ── USUÁRIOS DE DEMO (apenas para POC local) ──────────────
        # Senhas: admin=Admin@2025  |  demo=Demo@2025  |  viewer=View@2025
        salt = "bms_poc_salt_2025"
        def h(p): return hashlib.sha256(f"{salt}{p}".encode()).hexdigest()
        return {
            "admin": {
                "name": "Administrador",
                "password_hash": h("Admin@2025"),
                "role": "admin",
                "email": "admin@empresa.com",
            },
            "demo": {
                "name": "Usuário Demo",
                "password_hash": h("Demo@2025"),
                "role": "editor",
                "email": "demo@empresa.com",
            },
            "viewer": {
                "name": "Analista (Read-Only)",
                "password_hash": h("View@2025"),
                "role": "viewer",
                "email": "viewer@empresa.com",
            },
        }

# ─────────────────────────────────────────────────────────────────
# PAPÉIS E PERMISSÕES
# ─────────────────────────────────────────────────────────────────

ROLE_PERMISSIONS = {
    "admin":  {"can_edit": True,  "can_delete": True,  "can_export": True,  "can_manage_users": True},
    "editor": {"can_edit": True,  "can_delete": False, "can_export": True,  "can_manage_users": False},
    "viewer": {"can_edit": False, "can_delete": False, "can_export": True,  "can_manage_users": False},
}

ROLE_LABELS = {
    "admin":  "👑 Admin",
    "editor": "✏️ Editor",
    "viewer": "👁️ Viewer",
}

def get_permission(permission: str) -> bool:
    role = st.session_state.get("user_role", "viewer")
    return ROLE_PERMISSIONS.get(role, {}).get(permission, False)

# ─────────────────────────────────────────────────────────────────
# ESTADO DE SESSÃO
# ─────────────────────────────────────────────────────────────────

def init_auth_state():
    defaults = {
        "authenticated": False,
        "username": "",
        "user_name": "",
        "user_role": "",
        "user_email": "",
        "login_time": None,
        "login_attempts": 0,
        "lockout_until": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def logout():
    keys_to_clear = [
        "authenticated","username","user_name","user_role",
        "user_email","login_time","login_attempts","lockout_until"
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ─────────────────────────────────────────────────────────────────
# TELA DE LOGIN
# ─────────────────────────────────────────────────────────────────

def render_login_page():
    """Renderiza a tela de login. Retorna True se autenticado."""

    # Bloqueia por tentativas excessivas
    if st.session_state.lockout_until:
        remaining = (st.session_state.lockout_until - datetime.now()).seconds
        if datetime.now() < st.session_state.lockout_until:
            st.error(f"🔒 Muitas tentativas. Aguarde {remaining}s para tentar novamente.")
            st.stop()
        else:
            st.session_state.lockout_until = None
            st.session_state.login_attempts = 0

    # ── Layout da tela de login ──────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Outfit:wght@300;400;500;600&display=swap');

    /* ── Full-page dark background ── */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse 80% 50% at 50% -5%, rgba(201,168,76,0.10) 0%, transparent 55%),
            radial-gradient(ellipse 40% 40% at 90% 90%, rgba(77,217,192,0.06) 0%, transparent 50%),
            linear-gradient(160deg, #07101f 0%, #0b1a30 45%, #0a1825 100%);
        min-height: 100vh;
    }
    /* Grid overlay */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(201,168,76,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(201,168,76,0.03) 1px, transparent 1px);
        background-size: 56px 56px;
        pointer-events: none;
        z-index: 0;
    }
    [data-testid="stHeader"]  { background: transparent !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .block-container { padding-top: 4vh !important; position: relative; z-index: 1; }

    /* ── Wordmark ── */
    .bv-wordmark {
        font-family: 'Cormorant Garamond', serif;
        font-size: 3rem;
        font-weight: 300;
        color: #f5f0e8;
        text-align: center;
        line-height: 1;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }
    .bv-wordmark .b   { color: #c9a84c; font-weight: 600; font-style: italic; }
    .bv-wordmark .ai  { font-family: 'Outfit', sans-serif; font-size: 0.38em;
                        color: #4dd9c0; vertical-align: super; font-weight: 500; letter-spacing: 1px; }
    .bv-tagline {
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-size: 0.72rem;
        letter-spacing: 3.5px;
        text-transform: uppercase;
        color: rgba(184,200,216,0.5);
        margin-bottom: 0.5rem;
    }
    .bv-sub {
        text-align: center;
        font-family: 'Cormorant Garamond', serif;
        font-style: italic;
        font-size: 1rem;
        color: rgba(201,168,76,0.6);
        margin-bottom: 2.5rem;
    }

    /* ── Login card ── */
    .bv-card {
        background: rgba(11,26,48,0.7);
        border: 1px solid rgba(201,168,76,0.18);
        border-radius: 18px;
        padding: 2rem 2rem 1.5rem;
        backdrop-filter: blur(20px);
        box-shadow: 0 32px 80px rgba(0,0,0,0.5),
                    inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }
    .bv-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #c9a84c, #4dd9c0, transparent);
        opacity: 0.7;
    }
    .bv-card-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.5rem;
        font-weight: 300;
        color: #f5f0e8;
        margin-bottom: 0.2rem;
    }
    .bv-card-sub {
        font-size: 0.78rem;
        color: rgba(184,200,216,0.5);
        margin-bottom: 1.6rem;
        font-family: 'Outfit', sans-serif;
    }

    /* ── Streamlit input overrides ── */
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(201,168,76,0.18) !important;
        border-radius: 10px !important;
        color: #f5f0e8 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }
    .stTextInput input:focus {
        border-color: rgba(201,168,76,0.5) !important;
        background: rgba(201,168,76,0.04) !important;
        box-shadow: 0 0 0 3px rgba(201,168,76,0.08) !important;
    }
    .stTextInput input::placeholder { color: rgba(184,200,216,0.25) !important; }
    .stTextInput label {
        color: rgba(184,200,216,0.5) !important;
        font-size: 0.7rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* ── Submit button ── */
    div[data-testid="stForm"] { background: transparent !important; border: none !important; }
    .stButton > button {
        background: linear-gradient(135deg, #a07828, #c9a84c, #e2c97e) !important;
        background-size: 200% !important;
        color: #07101f !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        letter-spacing: 1px !important;
        padding: 0.7rem !important;
        width: 100% !important;
        box-shadow: 0 4px 20px rgba(201,168,76,0.3) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(201,168,76,0.45) !important;
    }

    /* ── AI hint ── */
    .bv-ai-hint {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.7rem 0.9rem;
        border-radius: 9px;
        background: rgba(77,217,192,0.05);
        border: 1px solid rgba(77,217,192,0.15);
        margin-top: 1.2rem;
    }
    .bv-ai-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #4dd9c0;
        box-shadow: 0 0 8px #4dd9c0;
        flex-shrink: 0;
        animation: bvPulse 2s ease-in-out infinite;
    }
    @keyframes bvPulse {
        0%,100% { opacity:1; transform:scale(1); }
        50%      { opacity:0.4; transform:scale(1.4); }
    }
    .bv-ai-text {
        font-size: 0.73rem;
        color: rgba(77,217,192,0.7);
        font-family: 'Outfit', sans-serif;
        line-height: 1.4;
    }

    /* ── Demo box ── */
    .bv-demo {
        background: rgba(201,168,76,0.05);
        border: 1px solid rgba(201,168,76,0.15);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-top: 1.2rem;
        font-family: 'Outfit', sans-serif;
        font-size: 0.78rem;
        color: rgba(184,200,216,0.6);
        line-height: 1.8;
    }
    .bv-demo strong { color: rgba(201,168,76,0.8); }

    /* ── Footer ── */
    .bv-footer {
        text-align: center;
        margin-top: 1.5rem;
        font-family: 'Outfit', sans-serif;
        font-size: 0.65rem;
        color: rgba(184,200,216,0.22);
        letter-spacing: 0.5px;
        line-height: 1.8;
    }
    </style>
    """, unsafe_allow_html=True)

    # Container centralizado
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="bv-wordmark">
            <span class="b">b</span>Valor<span class="ai">.ai</span>
        </div>
        <div class="bv-tagline">Business Modeling · Strategy · Intelligence</div>
        <div class="bv-sub">"Model your business. Realize your value."</div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div class="bv-card">
                <div class="bv-card-title">Bem-vindo de volta</div>
                <div class="bv-card-sub">Acesse sua plataforma de modelagem estratégica</div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Usuário", placeholder="seu.usuario")
            password = st.text_input("Senha", type="password", placeholder="••••••••••")
            submitted = st.form_submit_button("Acessar plataforma →", use_container_width=True)

        if submitted:
            users = get_users()
            user_data = users.get(username.strip().lower())

            if user_data and verify_password(password, user_data["password_hash"]):
                # ✅ Autenticação bem-sucedida
                st.session_state.authenticated = True
                st.session_state.username = username.strip().lower()
                st.session_state.user_name = user_data["name"]
                st.session_state.user_role = user_data["role"]
                st.session_state.user_email = user_data.get("email", "")
                st.session_state.login_time = datetime.now()
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                # ❌ Falha
                st.session_state.login_attempts += 1
                attempts = st.session_state.login_attempts
                remaining = max(0, 5 - attempts)

                if attempts >= 5:
                    st.session_state.lockout_until = datetime.now() + timedelta(minutes=5)
                    st.error("🔒 Conta bloqueada por 5 minutos após 5 tentativas.")
                else:
                    st.error(f"❌ Usuário ou senha incorretos. {remaining} tentativa(s) restante(s).")

        # AI hint
        st.markdown("""
        <div class="bv-ai-hint">
            <div class="bv-ai-dot"></div>
            <div class="bv-ai-text">
                <strong style="color:#4dd9c0;">IA Advisory</strong> em breve —
                análise inteligente do seu modelo de negócio com Claude AI.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Demo credentials
        st.markdown("""
        <div class="bv-demo">
            <strong>Credenciais de demonstração:</strong><br>
            👑 admin &nbsp;/ Admin@2025 &nbsp;— Acesso total<br>
            ✏️ demo &nbsp;&nbsp;/ Demo@2025 &nbsp;— Editor<br>
            👁️ viewer / View@2025 &nbsp;&nbsp;— Somente leitura
        </div>
        <div class="bv-footer">
            bValor.ai · Business Modeling Studio<br>
            BMM 1.3 · BPMN 2.0.2 · SBVR 1.5 · DMN 1.5 · ArchiMate 3.2<br>
            Baseado em Bridgeland &amp; Zahavi (2009)
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# BARRA SUPERIOR DO USUÁRIO LOGADO
# ─────────────────────────────────────────────────────────────────

def render_user_bar():
    """Exibe info do usuário logado + botão logout na sidebar."""
    role = st.session_state.get("user_role", "viewer")
    name = st.session_state.get("user_name", "")
    login_time = st.session_state.get("login_time")
    role_label = ROLE_LABELS.get(role, role)

    with st.sidebar:
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,400&family=Outfit:wght@300;400;500;600&display=swap');
        [data-testid="stSidebar"] {{
            background: #0b1a30 !important;
            border-right: 1px solid rgba(201,168,76,0.1) !important;
        }}
        [data-testid="stSidebar"] * {{ font-family: 'Outfit', sans-serif; }}
        [data-testid="stSidebar"] .stButton > button {{
            background: rgba(255,255,255,0.04) !important;
            color: rgba(184,200,216,0.7) !important;
            border: 1px solid rgba(255,255,255,0.07) !important;
            border-radius: 8px !important;
            font-size: 0.82rem !important;
            font-weight: 400 !important;
            box-shadow: none !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(201,168,76,0.08) !important;
            color: #e2c97e !important;
            border-color: rgba(201,168,76,0.2) !important;
            transform: none !important;
        }}
        </style>
        <div style="
            background: linear-gradient(135deg, #07101f, #112240);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            border: 1px solid rgba(201,168,76,0.18);
            margin-bottom: 0.8rem;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position:absolute; top:0; left:0; right:0; height:2px;
                background: linear-gradient(90deg, transparent, #c9a84c, #4dd9c0, transparent);
                opacity:0.6;
            "></div>
            <div style="color:rgba(184,200,216,0.4); font-size:0.65rem; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:0.3rem;">Conectado como</div>
            <div style="color:#f5f0e8; font-weight:600; font-size:0.92rem;">{name}</div>
            <div style="color:#c9a84c; font-size:0.75rem; margin-top:0.1rem;">{role_label}</div>
            {f'<div style="color:rgba(184,200,216,0.3); font-size:0.68rem; margin-top:0.3rem;">desde {login_time.strftime("%H:%M")}</div>' if login_time else ""}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Sair", use_container_width=True, type="secondary"):
            logout()

# ─────────────────────────────────────────────────────────────────
# GUARD — ponto de entrada principal
# ─────────────────────────────────────────────────────────────────

def require_auth() -> bool:
    """
    Chame isso no topo do app.py.
    Retorna True se autenticado, False (e renderiza login) caso contrário.
    """
    init_auth_state()
    if not st.session_state.authenticated:
        render_login_page()
        st.stop()
    return True
