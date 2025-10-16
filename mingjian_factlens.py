# -*- coding: utf-8 -*-
"""
明鉴 FactLens – 事实观点分析工具
v1.0.0  2024-10
"""

import streamlit as st
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import time

# -------------------- 页面配置 --------------------
st.set_page_config(
    page_title="明鉴 FactLens - 事实观点分析",
    page_icon="🔍",
    layout="wide"
)

# -------------------- 样式 --------------------
st.markdown("""
<style>
    .brand-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .lens-fact {
        background-color: #e6f7ff !important;
        border-left: 4px solid #1890ff !important;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .lens-opinion {
        background-color: #fff7e6 !important;
        border-left: 4px solid #ffa940 !important;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .lens-mixed {
        background-color: #f6ffed !important;
        border-left: 4px solid #52c41a !important;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; }
        .brand-header h1 { font-size: 24px !important; }
        .brand-header h3 { font-size: 18px !important; }
    }
</style>
""", unsafe_allow_html=True)

# -------------------- 品牌头部 --------------------
st.markdown("""
<div class="brand-header">
    <h1>🔍 明鉴 FactLens</h1>
    <h3>明鉴事实，洞见观点</h3>
    <p>AI驱动的新闻内容智能分析工具</p>
</div>
""", unsafe_allow_html=True)

# -------------------- 输入 --------------------
st.header("📰 新闻分析")
url = st.text_input("请输入新闻网址：", placeholder="https://example.com/news/ ...")

# -------------------- 规则引擎 --------------------
def simple_analyze(sentence: str):
    sentence_lower = sentence.lower()
    fact_kw = ['数据', '统计', '报告', '显示', '表示', '证实', '据', '研究',
               '调查', '结果', '百分比', '增长', '下降', '日期', '时间', '地点']
    opinion_kw = ['认为', '觉得', '应该', '可能', '或许', '相信', '建议', '我',
                  '我们', '必须', '一定', '肯定', '显然', '毫无疑问', '美好', '糟糕']
    fact_score = sum(sentence_lower.count(w) for w in fact_kw)
    opinion_score = sum(sentence_lower.count(w) for w in opinion_kw)

    if fact_score > opinion_score:
        return "事实", 0.7 + fact_score * 0.1
    elif opinion_score > fact_score:
        return "观点", 0.7 + opinion_score * 0.1
    else:
        return "混合", 0.6

# -------------------- 内容提取 --------------------
def extract_article(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求失败：{e}")
        return None

    soup = BeautifulSoup(resp.content, 'html.parser')
    article = type('MockArticle', (), {})()
    article.title = soup.title.text if soup.title else "无标题"

    body_text = []
    selectors = ['article', '.article-content', '.content', 'main',
                 'div.article-body', '.post-content', '.story-content']
    for sel in selectors:
        if els := soup.select(sel):
            body_text = [el.get_text(' ', strip=True) for el in els]
            break
    if not body_text:
        body_text = [p.get_text(' ', strip=True) for p in soup.find_all('p')]
    article.text = "\n\n".join(body_text)
    article.authors = []
    article.publish_date = None
    return article

# -------------------- 分析主流程 --------------------
if st.button("开始分析", type="primary") or url:
    if not url:
        st.warning("请输入新闻网址后再点击分析")
        st.stop()
    if not url.startswith(('http://', 'https://')):
        st.warning("网址需以 http:// 或 https:// 开头")
        st.stop()

    with st.spinner('🔍 明鉴正在分析中...'):
        article = extract_article(url)
        if not article or len(article.text.strip()) < 50:
            st.error("无法解析该网址，请尝试其他新闻网站")
            st.info("💡 提示：建议使用主流新闻网站，如新浪、网易、人民网等")
            st.stop()

        st.success(f"✅ 成功获取内容：{article.title}")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**作者：** {', '.join(article.authors) if article.authors else '未知'}")
        with col2:
            st.write(f"**发布时间：** {article.publish_date or '未知'}")

        sentences = re.split(r'[。！？!?\.]', article.text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            st.warning("未提取到足够内容进行分析，请尝试其他网址")
            st.stop()

        total_sentences = min(50, len(sentences))
        results = []
        progress = st.progress(0)
        for i, sent in enumerate(sentences[:total_sentences]):
            label, conf = simple_analyze(sent)
            results.append({
                '序号': i + 1,
                '内容': sent,
                '类型': label,
                '置信度': f"{conf:.2f}"
            })
            progress.progress((i + 1) / total_sentences)
        progress.empty()

        # 统计
        st.subheader("📊 分析概览")
        fact_cnt = sum(1 for r in results if r['类型'] == '事实')
        opinion_cnt = sum(1 for r in results if r['类型'] == '观点')
        mixed_cnt = sum(1 for r in results if r['类型'] == '混合')
        total_cnt = len(results)
        c1, c2, c3 = st.columns(3)
        c1.metric("事实陈述", f"{fact_cnt}条", f"{fact_cnt / total_cnt * 100:.1f}%")
        c2.metric("观点表达", f"{opinion_cnt}条", f"{opinion_cnt / total_cnt * 100:.1f}%")
        c3.metric("混合内容", f"{mixed_cnt}条", f"{mixed_cnt / total_cnt * 100:.1f}%")

        # 详情
        st.subheader("🔍 详细分析")
        for r in results:
            label_emoji = {"事实": "✅", "观点": "💬", "混合": "🔀"}
            card_class = {"事实": "lens-fact", "观点": "lens-opinion", "混合": "lens-mixed"}
            st.markdown(f"""
            <div class="{card_class[r['类型']]}">
                <strong>{label_emoji[r['类型']]} {r['类型']}</strong>
                <span style="float:right; color:#666">置信度: {r['置信度']}</span><br>
                {r['内容']}
            </div>
            """, unsafe_allow_html=True)

        # 下载
        st.subheader("📥 导出结果")
        csv = pd.DataFrame(results).to_csv(index=False).encode('utf-8-sig')
        st.download_button("下载分析结果(CSV)", csv, "明鉴分析结果.csv", "text/csv")

# -------------------- 侧边栏 --------------------
with st.sidebar:
    st.header("ℹ️ 关于明鉴")
    st.markdown("""
    **明鉴 FactLens** 是AI驱动的新闻内容分析工具，  
    帮助用户快速区分新闻中的事实陈述与观点表达。
    
    ### 使用场景
    - 信息真实性验证  
    - 媒体素养教育  
    - 内容分析研究  
    - 个人阅读辅助  
    """)

    st.divider()
    st.header("🎯 使用指南")
    st.markdown("""
    1. 复制新闻网址  
    2. 粘贴到输入框  
    3. 点击「开始分析」  
    4. 查看分析结果  
    5. 可下载详细数据  
    """)

    st.divider()
    st.header("🌐 推荐网站")
    st.markdown("""
    以下网站兼容性较好：  
    - [新浪新闻](https://news.sina.com.cn)  
    - [网易新闻](https://news.163.com)  
    - [腾讯新闻](https://news.qq.com)  
    - [人民网](http://people.com.cn)  
    - [新华网](http://www.xinhuanet.com)  
    """)

# -------------------- 页脚 --------------------
st.divider()
st.caption("© 2024 明鉴 FactLens - v1.0.0 - 明鉴事实，洞见观点")
