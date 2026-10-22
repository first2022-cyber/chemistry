import html
import json
import urllib.parse

import requests
import streamlit as st
import streamlit.components.v1 as components

# PubChem PUG REST is free to use and does not require an API key.
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 20

st.set_page_config(
    page_title="물질 정보 (화학)",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #fffdf8; color: #3f2b16; }
    .block-container { max-width: 1120px; padding-top: 1.6rem; padding-bottom: 2rem; }
    .hero { text-align: center; padding: 8px 0 24px; }
    .hero-icon { font-size: 42px; line-height: 1.3; }
    .hero h1 { color: #4a3217; font-size: 2.2rem; margin: 8px 0 12px; }
    .pills { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
    .pill { display: inline-block; border-radius: 999px; padding: 7px 16px; font-size: 0.95rem; }
    .pill-chem { color: #a86b00; background: #fff5dc; }
    .pill-free { color: #d63384; background: #fff0f6; }
    .info-card { background: #fff; border: 1px solid #f2d9a8; border-radius: 22px;
                 padding: 24px 28px; margin: 0 0 18px; }
    .intro { border-left: 4px solid #5965ff; background: linear-gradient(90deg,#fffaf1,#fff);
             padding: 16px 20px; line-height: 1.9; font-size: 1.05rem; margin: 14px 0 18px; }
    .data-row { display: grid; grid-template-columns: 132px 1fr; gap: 10px;
                border-bottom: 1px solid #f2d9a8; padding: 10px 4px; line-height: 1.55; }
    .data-label { color: #9c7b4c; font-weight: 600; }
    .source-link { display: inline-block; margin-top: 18px; padding: 12px 18px; border-radius: 12px;
                   color: #a86b00 !important; background: #fff6e2; border: 1px solid #f2d9a8;
                   text-decoration: none !important; font-weight: 600; }
    .small-note { color: #766b5d; font-size: .9rem; }
    code { color: #744600 !important; background: #fff4df !important; }
    @media (max-width: 650px) {
      .info-card { padding: 18px 14px; }
      .data-row { grid-template-columns: 1fr; gap: 2px; }
      .hero h1 { font-size: 1.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-icon">⚗️</div>
      <h1>물질 정보 (화학)</h1>
      <div class="pills">
        <span class="pill pill-chem">화학</span>
        <span class="pill pill-free">🌐 국적 무관</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-card">
      <strong>📋 어떤 데이터인가요?</strong>
      <div class="intro">
        미국 국립보건원(NIH)이 운영하는 세계 최대 화학 백과
        <b>PubChem</b>. <b>1억 종</b>이 넘는 물질의 이름만 넣으면
        분자식·분자량은 물론 <b>구조 그림</b>까지 그려 줍니다.
      </div>
      <div class="data-row"><div class="data-label">무엇</div>
        <div>물질 이름으로 분자식·분자량·구조 그림 (PubChem)</div></div>
      <div class="data-row"><div class="data-label">API 키</div>
        <div><b>필요 없음</b> · 무료</div></div>
      <div class="data-row"><div class="data-label">요청 예</div>
        <div><code>pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/caffeine/property/MolecularWeight/JSON</code></div></div>
      <div class="data-row"><div class="data-label">2D 그림</div>
        <div>같은 주소의 <code>/PNG</code> 로 붙여 분자 구조 이미지를 받습니다.</div></div>
      <div class="data-row"><div class="data-label">3D 구조</div>
        <div>PubChem이 계산한 3D 입체구조 좌표(SDF, <code>record_type=3d</code>)를 받아
        <b>3Dmol.js</b>로 회전 가능한 분자 모형을 그립니다. 데이터는 PubChem이 제공합니다.</div></div>
      <a class="source-link" href="https://pubchem.ncbi.nlm.nih.gov/" target="_blank">
        🔗 원 데이터 출처: PubChem (미국 국립보건원 NIH) ↗
      </a>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def pubchem_get(url: str, params: dict | None = None):
    response = requests.get(
        url,
        params=params,
        timeout=TIMEOUT,
        headers={"User-Agent": "SchoolChemistryExplorer/1.0 (Streamlit educational app)"},
    )
    response.raise_for_status()
    return response


def get_compound_properties(name: str) -> dict:
    encoded_name = urllib.parse.quote(name.strip(), safe="")
    url = f"{PUBCHEM_BASE}/compound/name/{encoded_name}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,IsomericSMILES/JSON"
    response = pubchem_get(url)
    data = response.json()
    properties = data.get("PropertyTable", {}).get("Properties", [])
    if not properties:
        raise ValueError("검색 결과에서 물질 정보를 찾지 못했습니다.")
    return properties[0]


def get_2d_image_url(name: str, width: int = 500, height: int = 380) -> str:
    encoded_name = urllib.parse.quote(name.strip(), safe="")
    return (
        f"{PUBCHEM_BASE}/compound/name/{encoded_name}/PNG"
        f"?image_size={width}x{height}"
    )


def get_3d_sdf(name: str) -> str:
    encoded_name = urllib.parse.quote(name.strip(), safe="")
    url = f"{PUBCHEM_BASE}/compound/name/{encoded_name}/SDF"
    response = pubchem_get(url, params={"record_type": "3d"})
    return response.text


def render_3d_viewer(sdf_text: str, height: int = 480):
    # Embed SDF directly in the page so the viewer does not need another API request.
    safe_sdf = json.dumps(sdf_text)
    html_doc = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
      <style>
        html, body {{ margin: 0; padding: 0; background: #fffdf8; font-family: sans-serif; }}
        #viewer {{ width: 100%; height: {height}px; position: relative; border: 1px solid #f2d9a8;
                   border-radius: 14px; overflow: hidden; }}
        #message {{ padding: 12px; color: #766b5d; }}
      </style>
    </head>
    <body>
      <div id="viewer"><div id="message">3D 분자 모형을 불러오는 중...</div></div>
      <script>
        const sdfData = {safe_sdf};
        const element = document.getElementById('viewer');
        const viewer = $3Dmol.createViewer(element, {{ backgroundColor: '#fffdf8' }});
        viewer.addModel(sdfData, 'sdf');
        viewer.setStyle({{}}, {{stick: {{radius: 0.16}}, sphere: {{scale: 0.24}}}});
        viewer.zoomTo();
        viewer.render();
        viewer.zoom(0.9);
        document.getElementById('message').remove();
        window.addEventListener('resize', () => viewer.resize());
      </script>
    </body>
    </html>
    """
    components.html(html_doc, height=height + 10, scrolling=False)


POPULAR_COMPOUNDS = [
    "caffeine",
    "water",
    "aspirin",
    "glucose",
    "ethanol",
    "sodium chloride",
    "citric acid",
    "acetaminophen",
    "carbon dioxide",
    "nicotine",
    "urea",
    "benzene",
]

st.markdown("### 🔎 물질 검색")
left, right = st.columns([1, 1.5])
with left:
    preset = st.selectbox("인기 물질", ["직접 입력"] + POPULAR_COMPOUNDS, index=1)
with right:
    typed_name = st.text_input(
        "물질 이름 (영어 이름 또는 일반적인 화학명)",
        value="" if preset == "직접 입력" else preset,
        placeholder="예: caffeine, aspirin, glucose",
    )

search_col, tip_col = st.columns([1, 3])
with search_col:
    search_clicked = st.button("물질 정보 검색", type="primary", use_container_width=True)
with tip_col:
    st.markdown(
        '<p class="small-note">검색 예: caffeine(카페인), aspirin(아스피린), glucose(포도당). '
        "물질명은 영어로 입력하면 검색이 더 안정적입니다.</p>",
        unsafe_allow_html=True,
    )

if "last_search_name" not in st.session_state:
    st.session_state.last_search_name = ""

if search_clicked:
    if not typed_name.strip():
        st.warning("검색할 물질 이름을 입력해 주세요.")
    else:
        st.session_state.last_search_name = typed_name.strip()

name = st.session_state.last_search_name
if name:
    try:
        with st.spinner(f"PubChem에서 '{name}' 정보를 가져오는 중입니다..."):
            props = get_compound_properties(name)
        formula = props.get("MolecularFormula", "정보 없음")
        weight = props.get("MolecularWeight", "정보 없음")
        iupac = props.get("IUPACName", "정보 없음")
        cid = props.get("CID")
        smiles = props.get("CanonicalSMILES", "정보 없음")

        st.markdown("---")
        st.subheader(f"🧪 검색 결과: {name}")
        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("분자식", formula)
        metric2.metric("분자량 (g/mol)", str(weight))
        metric3.metric("PubChem CID", str(cid) if cid is not None else "정보 없음")

        tab2d, tab3d, tabinfo = st.tabs(["🖼️ 2D 구조", "🧊 회전 가능한 3D 구조", "📄 상세 정보"])
        with tab2d:
            st.caption("PubChem에서 제공하는 2차원 분자 구조 이미지입니다.")
            image_url = get_2d_image_url(name)
            try:
                image_response = pubchem_get(image_url)
                st.image(image_response.content, caption=f"{name} — 2D 분자 구조", width=500)
            except requests.RequestException:
                st.info("2D 구조 이미지를 불러오지 못했습니다. 물질 이름을 영어로 다시 검색해 보세요.")
            st.markdown(f"[PubChem에서 이 물질 열기](https://pubchem.ncbi.nlm.nih.gov/#query={urllib.parse.quote(name)})")

        with tab3d:
            st.caption("마우스로 드래그하면 회전하고, 휠로 확대·축소할 수 있습니다. 3D 좌표가 제공되는 물질만 표시됩니다.")
            try:
                with st.spinner("3D 입체구조 좌표를 가져오는 중입니다..."):
                    sdf = get_3d_sdf(name)
                if not sdf.strip() or "M  END" not in sdf:
                    st.info("이 물질은 PubChem에서 사용할 수 있는 3D 구조를 제공하지 않는 것 같습니다.")
                else:
                    render_3d_viewer(sdf)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (400, 404):
                    st.info("이 물질의 3D 좌표를 찾을 수 없습니다. 2D 구조와 상세 정보는 확인할 수 있습니다.")
                else:
                    st.error("3D 구조를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            except requests.RequestException:
                st.error("네트워크 문제로 3D 구조를 불러오지 못했습니다.")

        with tabinfo:
            st.write("**IUPAC 이름**")
            st.write(iupac)
            st.write("**Canonical SMILES**")
            st.code(smiles)
            st.write("**PubChem 원본 정보**")
            st.markdown(f"[CID {cid} 페이지 열기](https://pubchem.ncbi.nlm.nih.gov/compound/{cid})" if cid else
                        f"[PubChem에서 검색](https://pubchem.ncbi.nlm.nih.gov/#query={urllib.parse.quote(name)})")

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "알 수 없음"
        if status in (400, 404):
            st.error("물질을 찾지 못했습니다. 영어 이름이나 다른 일반명을 사용해 다시 검색해 주세요.")
        elif status == 429:
            st.warning("PubChem 요청이 잠시 많습니다. 잠시 기다린 뒤 다시 시도해 주세요.")
        else:
            st.error(f"PubChem 서버에서 오류가 발생했습니다 (HTTP {status}). 잠시 후 다시 시도해 주세요.")
    except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
        st.error("정보를 가져오지 못했습니다. 네트워크 상태와 물질 이름을 확인한 뒤 다시 시도해 주세요.")

st.markdown("---")
st.markdown(
    '<p class="small-note">자료 출처: <a href="https://pubchem.ncbi.nlm.nih.gov/" target="_blank">PubChem (NIH)</a> · '
    "분자 3D 뷰어: <a href=\"https://3dmol.org/\" target=\"_blank\">3Dmol.js</a>. "
    "이 앱은 교육·탐구용이며, 네트워크 연결이 필요합니다.</p>",
    unsafe_allow_html=True,
)
