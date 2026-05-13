import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="서울시 CCTV-범죄 현황 분석", layout="wide")

# --- 데이터베이스 연결 함수 ---
def get_connection():
    db_path = 'seoul_crime_cctv.db'
    
    # 1. 파일 존재 여부 확인 (에러 처리)
    if not os.path.exists(db_path):
        st.error(f"🚨 데이터베이스 파일('{db_path}')을 찾을 수 없습니다!")
        st.info("""
        **💡 해결책:**
        1. `app.py` 파일이 있는 같은 폴더에 `seoul_crime_cctv.db` 파일이 있는지 확인해주세요.
        2. 파일 이름에 오타가 없는지 확인해주세요.
        """)
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        st.error(f"🚨 DB 연결 중 오류가 발생했습니다: {e}")
        return None

# --- 메인 대시보드 화면 ---
st.title("📊 서울시 CCTV와 범죄 발생 현황 분석")
st.markdown("""
### **"CCTV가 많은 지역은 정말로 범죄율이 낮을까?"**
이 질문에 대한 답을 찾기 위해 서울시 공공데이터를 분석해 보았습니다. 
CCTV 설치 수와 인구 대비 범죄 발생 건수 사이의 관계를 확인해 보세요.
""")

conn = get_connection()

if conn:
    try:
        # --- 차트 1: 자치구별 CCTV 개수 (막대 그래프) ---
        st.header("1. 자치구별 CCTV 설치 현황")
        sql1 = "SELECT 자치구, cctv수 FROM cctv ORDER BY cctv수 DESC"
        df1 = pd.read_sql(sql1, conn)
        
        col1_1, col1_2 = st.columns([2, 1])
        with col1_1:
            fig1 = px.bar(df1, x='자치구', y='cctv수', color='cctv수', 
                          title="서울시 자치구별 CCTV 수 (많은 순서)",
                          labels={'cctv수': 'CCTV 개수'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col1_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql1, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 강남구와 관악구 등이 서울 내에서 압도적으로 많은 CCTV를 보유하고 있습니다.
            - 자치구마다 예산과 면적에 따라 CCTV 설치 규모의 차이가 뚜렷하게 나타납니다.
            - 설치 대수가 적은 자치구는 상대적으로 주거 밀집도가 낮거나 면적이 좁을 가능성이 있습니다.
            - 단순 개수보다는 지역적 특성을 고려한 분석의 기초 데이터로 활용됩니다.
            """)

        st.divider()

        # --- 차트 2: 범죄유형 발생 건수 (파이 차트) ---
        st.header("2. 서울시 전체 범죄 유형별 비중")
        sql2 = "SELECT SUM(살인) as 살인, SUM(강도) as 강도, SUM(성범죄) as 성범죄, SUM(절도) as 절도, SUM(폭력) as 폭력 FROM 범죄데이터"
        df2 = pd.read_sql(sql2, conn)
        
        # 데이터 모양 바꾸기 (Wide to Long)
        df2_melted = df2.melt(var_name='범죄유형', value_name='건수')
        
        col2_1, col2_2 = st.columns([2, 1])
        with col2_1:
            fig2 = px.pie(df2_melted, values='건수', names='범죄유형', title="서울시 5대 범죄 발생 비중",
                          hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig2, use_container_width=True)
            
        with col2_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql2, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 서울시 전체 범죄 중 '절도'와 '폭력'이 가장 높은 비중을 차지하고 있습니다.
            - 살인이나 강도와 같은 중범죄는 상대적으로 비중이 낮아 다행스러운 부분입니다.
            - CCTV 설치 목적이 주로 예방에 치중되어야 할 범죄 유형이 무엇인지 시사합니다.
            - 범죄별 발생 건수를 통해 치안 정책의 우선순위를 결정할 수 있습니다.
            """)

        st.divider()

        # --- 차트 3: CCTV 수 vs 범죄율 (산점도) ---
        st.header("3. CCTV 수와 범죄율의 상관관계")
        
        # SQL에서 연산 수행 (총범죄수와 인구 10만명당 범죄율 계산)
        sql3 = """
        SELECT 
            c.자치구, 
            c.cctv수, 
            p.인구수,
            (b.살인 + b.강도 + b.성범죄 + b.절도 + b.폭력) as 총범죄수,
            (CAST(b.살인 + b.강도 + b.성범죄 + b.절도 + b.폭력 AS FLOAT) / p.인구수) * 100000 as 범죄율
        FROM cctv c
        JOIN 서울인구 p ON c.자치구 = p.자치구
        JOIN 범죄데이터 b ON c.자치구 = b.자치구
        """
        df3 = pd.read_sql(sql3, conn)

        col3_1, col3_2 = st.columns([2, 1])
        with col3_1:
            fig3 = px.scatter(df3, x='cctv수', y='범죄율', text='자치구', size='인구수',
                             trendline="ols", title="CCTV 설치 수와 10만명당 범죄율의 상관관계",
                             labels={'cctv수': 'CCTV 설치 수', '범죄율': '범죄율 (인구 10만명당)'},
                             color='범죄율')
            st.plotly_chart(fig3, use_container_width=True)

        with col3_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql3, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 산점도의 추세선(Trendline)을 통해 CCTV와 범죄율의 비례/반비례 관계를 확인합니다.
            - CCTV가 많다고 해서 반드시 범죄율이 낮게 나타나지 않을 수 있습니다(역설적 관계).
            - 이는 보통 범죄가 많이 발생하는 우범 지역에 CCTV를 더 많이 설치하기 때문입니다.
            - 즉, CCTV는 범죄를 낮추는 효과도 있지만, 범죄가 많은 곳에 설치되는 경향이 공존합니다.
            """)

    except Exception as e:
        st.error(f"🚨 시각화 과정에서 문제가 발생했습니다.")
        st.info(f"**상세 에러 내용:** {e}")
        st.markdown("""
        **🛠️ 해결책:**
        1. **데이터베이스 스키마 확인:** SQL 문 내의 컬럼명(`자치구`, `cctv수` 등)이 실제 DB와 똑같은지 확인하세요.
        2. **NULL 데이터:** 데이터베이스 내에 빈 값(NULL)이 있는지 확인하세요.
        3. **타입 에러:** 계산 과정에서 숫자가 아닌 텍스트 데이터가 포함되어 있을 수 있습니다.
        """)
    finally:
        conn.close()