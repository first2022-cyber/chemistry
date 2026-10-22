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
