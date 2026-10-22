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
