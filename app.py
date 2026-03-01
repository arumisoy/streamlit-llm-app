import os
import requests
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# ==========================
# Streamlit設定
# ==========================
st.set_page_config(page_title="PubChem Explorer", layout="wide")

st.title("🧪 PubChem Chemical Structure Explorer")

st.markdown("""
### 📘 アプリ概要
このWebアプリは：

1. 入力された化学物質名をPubChemで検索
2. 化学構造式を表示（PubChem公式画像）
3. LangChainを使ってLLMが専門家として解説

### 🧭 操作方法
1. 化学物質名を入力
2. 専門家タイプを選択
3. 「検索」ボタンをクリック
""")

# ==========================
# APIキー取得（Cloud対応）
# ==========================
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEYが設定されていません。Streamlit CloudのSecretsに設定してください。")
    st.stop()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=api_key
)

# ==========================
# PubChem画像URL
# ==========================
def get_structure_image_url(chemical_name):
    return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{chemical_name}/PNG"

# ==========================
# SMILES取得
# ==========================
def get_smiles(chemical_name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{chemical_name}/property/CanonicalSMILES/JSON"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    try:
        return response.json()["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
    except:
        return None

# ==========================
# LLM応答生成関数（指定要件）
# ==========================
def generate_expert_response(input_text, expert_type):
    """
    input_text: 入力テキスト（化学物質名）
    expert_type: ラジオボタンの選択値
    戻り値: LLMの回答
    """

    if expert_type == "医薬品化学者":
        system_message = """
        You are a pharmaceutical chemist.
        Explain the compound focusing on:
        - Drug discovery relevance
        - Mechanism of action
        - Medicinal chemistry insights
        """
    else:
        system_message = """
        You are a toxicology expert.
        Explain the compound focusing on:
        - Toxicity profile
        - Safety considerations
        - Biological and environmental impact
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Explain the chemical compound: {chemical}")
    ])

    chain = prompt | llm
    response = chain.invoke({"chemical": input_text})

    return response.content

# ==========================
# UI入力
# ==========================
chemical_name = st.text_input("🔍 化学物質名を入力してください")

expert_choice = st.radio(
    "👨‍🔬 専門家タイプを選択してください",
    ("医薬品化学者", "毒性学者")
)

# ==========================
# 実行ボタン
# ==========================
if st.button("検索"):
    if chemical_name:

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🧬 化学構造")
            image_url = get_structure_image_url(chemical_name)
            st.image(image_url)

            smiles = get_smiles(chemical_name)
            if smiles:
                st.code(smiles, language="text")
            else:
                st.warning("SMILESが取得できませんでした。")

        with col2:
            st.subheader("🤖 専門家による解説")
            with st.spinner("LLM解析中..."):
                explanation = generate_expert_response(
                    chemical_name,
                    expert_choice
                )
            st.write(explanation)