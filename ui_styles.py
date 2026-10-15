"""Professional UI styling, design tokens, and HTML components for Local AI Knowledge Assistant."""

CSS_THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base: #090D16;
    --bg-surface: #10172A;
    --bg-surface-elevated: #1E293B;
    --bg-glass: rgba(16, 23, 42, 0.78);
    --bg-glass-card: rgba(30, 41, 59, 0.55);
    --bg-glass-card-hover: rgba(30, 41, 59, 0.85);
    
    --border-subtle: rgba(255, 255, 255, 0.07);
    --border-light: rgba(255, 255, 255, 0.12);
    --border-accent: rgba(99, 102, 241, 0.35);
    
    --primary: #6366F1;
    --primary-light: #818CF8;
    --primary-dark: #4F46E5;
    --cyan: #06B6D4;
    --emerald: #10B981;
    --amber: #F59E0B;
    --rose: #F43F5E;
    
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-tertiary: #64748B;
    
    --grad-primary: linear-gradient(135deg, #6366F1 0%, #3B82F6 50%, #06B6D4 100%);
    --grad-surface: linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.7) 100%);
    --grad-hero: linear-gradient(135deg, #FFFFFF 20%, #CBD5E1 50%, #818CF8 100%);
    --grad-glow: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.25);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.35);
    --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.5);
    --shadow-glow: 0 0 24px -4px rgba(99, 102, 241, 0.3);
}

/* Global Font & Canvas */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.stApp {
    background-color: var(--bg-base);
    background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.08) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(79, 70, 229, 0.05) 0px, transparent 50%);
    background-attachment: fixed;
    color: var(--text-primary);
}

/* Top App Header & Container */
[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1200px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 7rem !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: rgba(13, 19, 33, 0.95) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-subtle) !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border-subtle) !important;
    margin: 1.25rem 0 !important;
}

/* Typography Overrides */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.025em !important;
    font-weight: 700 !important;
}

/* Navigation Navbar */
.top-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.85rem 1.4rem;
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    box-shadow: var(--shadow-md);
    margin-bottom: 1.8rem;
}

.brand-wrapper {
    display: flex;
    align-items: center;
    gap: 0.85rem;
}

.brand-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: var(--grad-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    box-shadow: var(--shadow-glow);
}

.brand-title {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    line-height: 1.2;
}

.brand-tagline {
    font-size: 0.72rem;
    color: var(--text-secondary);
    font-weight: 500;
    letter-spacing: 0.02em;
}

.nav-badges {
    display: flex;
    align-items: center;
    gap: 0.65rem;
}

.pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid var(--border-subtle);
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(10px);
    color: var(--text-secondary);
}

.pill-badge.active-green {
    border-color: rgba(16, 185, 129, 0.35);
    background: rgba(16, 185, 129, 0.1);
    color: #34D399;
}

.pill-badge.active-amber {
    border-color: rgba(245, 158, 11, 0.35);
    background: rgba(245, 158, 11, 0.1);
    color: #FBBF24;
}

.pill-badge.active-indigo {
    border-color: rgba(99, 102, 241, 0.35);
    background: rgba(99, 102, 241, 0.12);
    color: #A5B4FC;
}

.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
    position: relative;
}

.pulse-dot.online {
    background: #10B981;
    box-shadow: 0 0 10px #10B981;
    animation: pulse-green 2s infinite;
}

.pulse-dot.offline {
    background: #F59E0B;
    box-shadow: 0 0 10px #F59E0B;
}

@keyframes pulse-green {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Hero Section */
.hero-container {
    position: relative;
    padding: 2.2rem 2.2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.7) 100%);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-md);
    margin-bottom: 1.8rem;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 380px;
    height: 100%;
    background: radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.18) 0%, transparent 70%);
    pointer-events: none;
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--primary-light);
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: 2.35rem;
    font-weight: 800;
    line-height: 1.18;
    margin-bottom: 0.65rem;
    background: var(--grad-hero);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
}

.hero-description {
    font-size: 1.02rem;
    color: var(--text-secondary);
    line-height: 1.6;
    max-width: 820px;
    margin-bottom: 0;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.8rem;
}

.metric-card-pro {
    background: var(--bg-glass-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.15rem 1.25rem;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.metric-card-pro:hover {
    transform: translateY(-2px);
    background: var(--bg-glass-card-hover);
    border-color: var(--border-accent);
    box-shadow: var(--shadow-glow);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.45rem;
}

.metric-label-pro {
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
}

.metric-icon-wrap {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-subtle);
}

.metric-value-pro {
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    line-height: 1.15;
}

.metric-subtext-pro {
    font-size: 0.78rem;
    color: var(--text-tertiary);
    margin-top: 0.35rem;
    font-weight: 500;
}

/* Tab Bar Customization */
[data-testid="stTabs"] {
    margin-bottom: 1.5rem;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(16, 23, 42, 0.65) !important;
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
    padding: 0.35rem !important;
    gap: 0.4rem !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 42px !important;
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    border: none !important;
    background: transparent !important;
    padding: 0 1.25rem !important;
    transition: all 0.2s ease !important;
}

[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--bg-surface-elevated) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
}

/* Quick Prompt Suggestions */
.suggestion-heading {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.prompt-card {
    background: var(--bg-glass-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1rem 1.15rem;
    cursor: pointer;
    transition: all 0.2s ease;
    height: 100%;
}

.prompt-card:hover {
    border-color: var(--primary-light);
    transform: translateY(-2px);
    background: var(--bg-glass-card-hover);
    box-shadow: var(--shadow-glow);
}

.prompt-card-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.prompt-card-desc {
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.45;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background: var(--bg-glass-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 16px !important;
    padding: 1.1rem 1.35rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    backdrop-filter: blur(10px) !important;
}

/* Assistant Chat Message Glow */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid var(--primary) !important;
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, rgba(30, 41, 59, 0.6) 100%) !important;
}

/* User Chat Message Tint */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid var(--cyan) !important;
    background: linear-gradient(90deg, rgba(6, 182, 212, 0.08) 0%, rgba(30, 41, 59, 0.6) 100%) !important;
}

/* Chat Input Styling */
[data-testid="stChatInput"] {
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    background: rgba(16, 23, 42, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: 0 10px 35px -5px rgba(0, 0, 0, 0.6), 0 0 20px -3px rgba(99, 102, 241, 0.15) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary-light) !important;
    box-shadow: 0 10px 40px -5px rgba(0, 0, 0, 0.8), 0 0 25px 0 rgba(99, 102, 241, 0.35) !important;
}

/* Buttons */
div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.1rem !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid var(--border-light) !important;
}

div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-sm) !important;
}

div[data-testid="stButton"] > button[kind="primary"] {
    background: var(--grad-primary) !important;
    border: none !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
}

div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
}

div[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.7) !important;
    color: var(--text-primary) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
    background: rgba(20, 29, 47, 0.5) !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 0.75rem !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: var(--text-primary) !important;
    padding: 0.75rem 1rem !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--primary-light) !important;
}

/* Source Citation Card */
.source-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 0.95rem 1.15rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}

.source-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
}

.source-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
}

.source-file-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    font-weight: 700;
    color: #E2E8F0;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 0.2rem 0.65rem;
    border-radius: 6px;
}

.source-match-badge {
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}

.match-high {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}

.match-medium {
    background: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}

.source-content-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    color: #CBD5E1;
    background: rgba(9, 13, 22, 0.6);
    padding: 0.75rem 0.9rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    white-space: pre-wrap;
    word-break: break-word;
}

/* Document Repository Cards */
.doc-item-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    background: var(--bg-glass-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    margin-bottom: 0.65rem;
    transition: all 0.2s ease;
}

.doc-item-card:hover {
    background: var(--bg-glass-card-hover);
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateX(2px);
}

.doc-info-left {
    display: flex;
    align-items: center;
    gap: 0.9rem;
}

.doc-type-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
}

.doc-title-main {
    font-size: 0.94rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
}

.doc-meta-sub {
    font-size: 0.78rem;
    color: var(--text-secondary);
}

/* Architecture Flow Box */
.arch-flow-box {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1rem;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: var(--grad-primary) !important;
}

/* Inputs & Selectboxes */
div[data-baseweb="input"], div[data-baseweb="select"] {
    background-color: rgba(16, 23, 42, 0.8) !important;
    border-color: var(--border-light) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

/* File Uploader */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border-light) !important;
    border-radius: 16px !important;
    background: rgba(16, 23, 42, 0.4) !important;
    padding: 1rem !important;
    transition: all 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--primary) !important;
    background: rgba(99, 102, 241, 0.04) !important;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
::-webkit-scrollbar-track {
    background: rgba(9, 13, 22, 0.8);
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.4);
}

@media(max-width: 900px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .top-navbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.8rem;
    }
    .hero-title {
        font-size: 1.85rem;
    }
}
</style>
"""


def render_navbar(ollama_ready: bool, gen_model: str, embed_model: str, doc_count: int) -> str:
    status_class = "active-green" if ollama_ready else "active-amber"
    status_dot = "online" if ollama_ready else "offline"
    status_label = "Engine Active" if ollama_ready else "Engine Offline"
    return f"""
    <div class="top-navbar">
        <div class="brand-wrapper">
            <div class="brand-icon">⚡</div>
            <div>
                <div class="brand-title">AuraLocal AI Studio</div>
                <div class="brand-tagline">Private Autonomous Document Intelligence</div>
            </div>
        </div>
        <div class="nav-badges">
            <div class="pill-badge {status_class}">
                <span class="pulse-dot {status_dot}"></span>
                <span>{status_label}</span>
            </div>
            <div class="pill-badge active-indigo">
                <span>🤖 {gen_model}</span>
                <span style="color:var(--text-tertiary)">•</span>
                <span>📐 {embed_model}</span>
            </div>
            <div class="pill-badge">
                <span>🛡️ 100% On-Device Airgap</span>
            </div>
        </div>
    </div>
    """


def render_hero() -> str:
    return """
    <div class="hero-container">
        <div class="hero-eyebrow">
            <span>✦ Sovereign Neural RAG Engine</span>
        </div>
        <div class="hero-title">Synthesize answers from your private knowledge.</div>
        <div class="hero-description">
            Ask complex questions across your confidential PDFs, technical guides, and documents.
            Every claim is cross-verified with precision citations and vector-grounded context — completely local, with zero cloud dependency.
        </div>
    </div>
    """


def render_metrics_cards(doc_count: int, chunk_count: int, ollama_ready: bool, active_model: str) -> str:
    status_text = "Ollama Localhost" if ollama_ready else "Waiting for Ollama"
    status_color = "#34D399" if ollama_ready else "#FBBF24"
    status_icon = "🟢" if ollama_ready else "🟡"
    
    return f"""
    <div class="metric-grid">
        <div class="metric-card-pro">
            <div class="metric-header">
                <span class="metric-label-pro">Repository Files</span>
                <div class="metric-icon-wrap">📚</div>
            </div>
            <div class="metric-value-pro">{doc_count}</div>
            <div class="metric-subtext-pro">Active indexed documents</div>
        </div>
        <div class="metric-card-pro">
            <div class="metric-header">
                <span class="metric-label-pro">Indexed Passages</span>
                <div class="metric-icon-wrap">🧩</div>
            </div>
            <div class="metric-value-pro">{chunk_count}</div>
            <div class="metric-subtext-pro">Searchable vector chunks</div>
        </div>
        <div class="metric-card-pro">
            <div class="metric-header">
                <span class="metric-label-pro">Active LLM</span>
                <div class="metric-icon-wrap">⚡</div>
            </div>
            <div class="metric-value-pro" style="font-size:1.25rem; font-family:'JetBrains Mono',monospace;">{active_model}</div>
            <div class="metric-subtext-pro" style="color:{status_color}; font-weight:600;">{status_icon} {status_text}</div>
        </div>
        <div class="metric-card-pro">
            <div class="metric-header">
                <span class="metric-label-pro">Privacy & Storage</span>
                <div class="metric-icon-wrap">🔒</div>
            </div>
            <div class="metric-value-pro" style="font-size:1.25rem;">Cosine HNSW</div>
            <div class="metric-subtext-pro">Isolated local ChromaDB</div>
        </div>
    </div>
    """
