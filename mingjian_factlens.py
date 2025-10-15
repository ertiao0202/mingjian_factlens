import streamlit as st
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import time

# 设置页面 - 使用品牌标识
st.set_page_config(
    page_title="明鉴 FactLens - 事实观点分析",
    page_icon="🔍",
    layout="wide"
)

# 品牌头部的样式
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
    .fact-card { 
        background-color: #e6f7ff !important; 
        border-left: 4px solid #1890ff !important;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .opinion-card { 
        background-color: #fff7e6 !important; 
        border-left: 4px solid #ffa940 !important;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .mixed-card { 
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

# 品牌头部
st.markdown("""
<div class="brand-header">
    <h1>🔍 明鉴 FactLens</h1>
    <h3>明鉴事实，洞见观点</h3>
    <p>AI驱动的新闻内容智能分析工具</p>
</div>
""", unsafe_allow_html=True)

# 主要功能区域
st.header("📰 新闻分析")

# 输入网址
url = st.text_input("请输入新闻网址：", placeholder="https://example.com/news/...")

# 规则引擎函数
def simple_analyze(sentence):
    """简单规则分析事实 vs 观点"""
    sentence_lower = sentence.lower()
    
    # 事实特征
    fact_indicators = ['数据', '统计', '报告', '显示', '表示', '证实', '据', '研究', 
                      '调查', '结果', '百分比', '增长', '下降', '日期', '时间', '地点']
    
    # 观点特征  
    opinion_indicators = ['认为', '觉得', '应该', '可能', '或许', '相信', '建议', '我',
                         '我们', '必须', '一定', '肯定', '显然', '毫无疑问', '美好', '糟糕']
    
    fact_score = sum(1 for word in fact_indicators if word in sentence_lower)
    opinion_score = sum(1 for word in opinion_indicators if word in sentence_lower)
    
    if fact_score > opinion_score:
        return "事实", 0.7 + fact_score * 0.1
    elif opinion_score > fact_score:
        return "观点", 0.7 + opinion_score * 0.1
    else:
        return "混合", 0.6

# 使用BeautifulSoup的内容提取函数
def extract_article(url):
    """使用 BeautifulSoup 提取新闻内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 创建模拟的 article 对象
        class MockArticle:
            pass
        
        article = MockArticle()
        article.title = soup.title.text if soup.title else "无标题"
        
        # 提取正文 - 常见新闻网站选择器
        body_text = []
        selectors = [
            'article', 
            '.article-content', 
            '.content', 
            'div.content', 
            'main', 
            'div.article-body',
            '.post-content',
            '.story-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                body_text = [elem.get_text().strip() for elem in elements]
                break
        
        # 如果没有找到，尝试提取所有段落
        if not body_text:
            paragraphs = soup.find_all('p')
            if paragraphs:
                body_text = [p.get_text().strip() for p in paragraphs]
        
        article.text = "\n\n".join(body_text)
        article.authors = []
        article.publish_date = None
        return article
    except Exception as e:
        st.error(f"内容提取失败: {str(e)}")
        return None

if st.button("开始分析", type="primary") or url:
    if url and url.startswith('http'):
        with st.spinner('🔍 明鉴正在分析中...'):
            try:
                # 获取新闻内容
                article = extract_article(url)
                
                if not article or not hasattr(article, 'text') or len(article.text.strip()) < 50:
                    st.error("无法解析该网址内容，请尝试其他新闻网站")
                    st.info("💡 提示：建议使用主流新闻网站，如新浪、网易、人民网等")
                    st.stop()
                
                st.success(f"✅ 成功获取内容：{article.title}")
                
                # 显示文章信息
                col1, col2 = st.columns(2)
                with col1:
                    if hasattr(article, 'authors') and article.authors:
                        st.write(f"**作者：** {', '.join(article.authors)}")
                    else:
                        st.write("**作者：** 未知")
                with col2:
                    if hasattr(article, 'publish_date') and article.publish_date:
                        st.write(f"**发布时间：** {article.publish_date}")
                    else:
                        st.write("**发布时间：** 未知")
                
                # 分析内容
                sentences = re.split(r'[。！？!?]', article.text)
                sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
                
                if not sentences:
                    st.warning("未提取到足够内容进行分析，请尝试其他网址")
                    st.stop()
                
                results = []
                total_sentences = min(50, len(sentences))
                
                # 创建进度条
                progress_bar = st.progress(0)
                
                for i, sentence in enumerate(sentences[:total_sentences]):
                    label, confidence = simple_analyze(sentence)
                    results.append({
                        '序号': i+1,
                        '内容': sentence,
                        '类型': label,
                        '置信度': f"{confidence:.2f}"
                    })
                    # 更新进度
                    progress_bar.progress((i + 1) / total_sentences)
                
                # 完成进度条
                progress_bar.empty()
                
                # 显示统计结果
                st.subheader("📊 分析概览")
                fact_count = sum(1 for r in results if r['类型'] == '事实')
                opinion_count = sum(1 for r in results if r['类型'] == '观点')
                mixed_count = sum(1 for r in results if r['类型'] == '混合')
                total_count = len(results)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("事实陈述", f"{fact_count}条", f"{(fact_count/total_count*100):.1f}%")
                with col2:
                    st.metric("观点表达", f"{opinion_count}条", f"{(opinion_count/total_count*100):.1f}%")
                with col3:
                    st.metric("混合内容", f"{mixed_count}条", f"{(mixed_count/total_count*100):.1f}%")
                
                # 详细分析结果
                st.subheader("🔍 详细分析")
                
                for result in results:
                    if result['类型'] == '事实':
                        st.markdown(f"""
                        <div class="fact-card">
                            <strong>✅ 事实</strong> <span style="float:right; color:#666">置信度: {result['置信度']}</span><br>
                            {result['内容']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif result['类型'] == '观点':
                        st.markdown(f"""
                        <div class="opinion-card">
                            <strong>💬 观点</strong> <span style="float:right; color:#666">置信度: {result['置信度']}</span><br>
                            {result['内容']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="mixed-card">
                            <strong>🔀 混合</strong> <span style="float:right; color:#666">置信度: {result['置信度']}</span><br>
                            {result['内容']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # 下载功能
                st.subheader("📥 导出结果")
                df = pd.DataFrame(results)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="下载分析结果(CSV)",
                    data=csv,
                    file_name="明鉴分析结果.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"分析失败：{str(e)}")
                st.info("💡 提示：请确保网址可公开访问，或尝试其他新闻网站")
    else:
        st.warning("请输入有效的网址（以http://或https://开头）")

# 侧边栏信息
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
    st.header("🚀 技术特性")
    st.markdown("""
    - 🔍 智能内容提取
    - 📊 多维度分析
    - 📱 响应式设计
    - 🔄 实时处理
    - 💾 数据导出
    """)
    
    st.divider()
    st.header("🌐 推荐网站")
    st.markdown("""
    以下网站兼容性较好：
    - 新浪新闻 (news.sina.com.cn)
    - 网易新闻 (news.163.com)
    - 腾讯新闻 (news.qq.com)
    - 人民网 (people.com.cn)
    - 新华网 (xinhuanet.com)
    """)

# 页脚
st.divider()
st.caption("© 2024 明鉴 FactLens - 明鉴事实，洞见观点")