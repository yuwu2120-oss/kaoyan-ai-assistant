import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS

# --- 页面基础设置 ---
st.set_page_config(page_title="考研复试AI助教", page_icon="🎓", layout="wide")

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.title("⚙️ 系统配置")
    # 建议把Key放在这里输入，或者你可以直接在代码里写死 api_key="sk-xxxx"
    api_key = "sk-443d4d0b2a3a4b45a43a1025eeb226c5"
    st.markdown("---")
    st.info("💡 **使用说明**：\n1. 输入考生简历摘要\n2. 输入报考导师姓名\n3. AI会自动联网搜索导师信息\n4. 生成针对性的“杀手锏”问题")

# --- 核心功能函数 ---

def search_supervisor_info(name, school):
    """
    利用 DuckDuckGo 搜索导师的研究方向
    """
    if not name:
        return "未指定导师，将基于通用专业方向提问。"
    
    query = f"{school} {name} 研究方向 代表作"
    st.toast(f"正在全网搜索 {name} 导师的背景...", icon="🔍")
    
    try:
        # 使用 DDGS 进行搜索
        results = DDGS().text(keywords=query, max_results=5)
        search_summary = ""
        for res in results:
            search_summary += f"- {res['title']}: {res['body']}\n"
        return search_summary
    except Exception as e:
        return f"搜索失败（可能网络波动），仅基于字面信息生成。错误：{e}"

def generate_interview_guide(client, resume, target_info, supervisor_context):
    """
    调用 DeepSeek 生成面试清单
    """
    system_prompt = f"""
    你现在的身份是：一位严厉、挑剔且学术视野开阔的资深研究生导师。
    你的任务是：辅助面试官（在读研究生）对考生进行面试。
    
    【已知信息】
    1. 报考导师/院校情报：
    {supervisor_context}
    
    2. 考生简历摘要：
    {resume}
    
    【任务要求】
    请生成一份《面试提问手卡》，包含以下三个模块：
    
    模块一：简历深挖（找逻辑漏洞）
    - 生成 2 个针对考生项目经历的追问，要求具体、刁钻。
    
    模块二：学术匹配度（导师视角）
    - 基于搜索到的【报考导师情报】，设计 1 个能考察考生是否适合该课题组的深度问题。
    - 既然你知道导师研究什么，就问考生相关的基础概念。
    
    模块三：英语口语（复试高频）
    - 生成 1 个与专业相关的英语问答题。
    
    【输出格式】
    请直接输出问题列表，并在每个问题后附带【参考评分点】，方便学长打分。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请开始生成。"},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"调用大模型出错：{e}"

# --- 主界面布局 ---

st.title("🎓 考研复试·AI 面试官辅助系统")
st.caption("🚀 专为“四对一”模拟面试打造：让学长秒变专家")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 考生档案")
    target_school = st.text_input("报考院校", placeholder="例如：南京大学")
    supervisor_name = st.text_input("报考导师姓名 (重要！)", placeholder="例如：闻海虎")
    resume_text = st.text_area("简历/项目经历摘要", height=200, placeholder="粘贴考生的科研经历、毕设题目或自我介绍...")
    
    start_btn = st.button("开始生成面试题", type="primary", use_container_width=True)

with col2:
    st.subheader("📋 面试官手卡")
    if start_btn:
        if not api_key:
            st.error("请先在左侧侧边栏输入 API Key")
        elif not resume_text:
            st.warning("请至少输入考生的简历信息")
        else:
            # 1. 初始化客户端
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            # 2. 搜索导师信息
            with st.status("正在构建面试题库...", expanded=True) as status:
                st.write("🔍 正在分析考生简历...")
                st.write(f"🌐 正在联网搜索 {supervisor_name} 导师的最近研究...")
                
                supervisor_info = search_supervisor_info(supervisor_name, target_school)
                st.write("✅ 导师情报获取成功！")
                
                st.write("🧠 AI 正在生成刁钻问题...")
                result = generate_interview_guide(client, resume_text, target_school, supervisor_info)
                status.update(label="生成完毕！", state="complete", expanded=False)
            
            # 3. 展示结果
            st.markdown(result)
            st.success("请面试官根据上述问题进行提问，并记录考生反应。")