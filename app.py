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
    if not os.path.exists(db_path):
        st.error(f"🚨 에러: '{db_path}' 파일을 찾을 수 없습니다!")
        st.info("💡 해결책: 데이터베이스 파일이 app.py와 같은 폴더에 있는지 확인해주세요.")
        return None
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        st.error(f"🚨 DB 연결 중 오류 발생: {e}")
        return None

# --- 메인 화면 ---
st.title("📊 서울시 CCTV와 범죄 발생 현황 분석")
st.markdown("""
이 대시보드는 **"CCTV가 많은 지역은 정말로 범죄율이 낮을까?"**라는 의문을 풀기 위해 제작되었습니다. 
자치구별 CCTV 수, 범죄 발생 건수, 인구수 데이터를 결합하여 분석합니다.
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
                          title="서울시 자치구별 CCTV 수", labels={'cctv수': 'CCTV 개수'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col1_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql1, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 강남구, 관악구 등 특정 구의 CCTV 설치 수가 압도적으로 높음을 알 수 있습니다.
            - 자치구 간 CCTV 설치 대수 차이가 최대 3~4배까지 벌어지고 있습니다.
            - 이는 자치구의 예산 규모나 주거 밀집도와 관련이 있을 것으로 추정됩니다.
            - 단순히 대수만 비교하기보다 면적이나 인구 대비 비율도 고려해볼 필요가 있습니다.
            """)

        st.divider()

        # --- 차트 2: 범죄유형 발생 건수 (파이 차트) ---
        st.header("2. 서울시 전체 범죄 유형별 비중")
        sql2 = "SELECT SUM(살인) as 살인, SUM(강도) as 강도, SUM(성범죄) as 성범죄, SUM(절도) as 절도, SUM(폭력) as 폭력 FROM 범죄데이터"
        df2 = pd.read_sql(sql2, conn)
        
        # 파이 차트를 위해 데이터 재구조화 (Wide to Long)
        df2_melted = df2.melt(var_name='범죄유형', value_name='건수')
        
        col2_1, col2_2 = st.columns([2, 1])
        with col2_1:
            fig2 = px.pie(df2_melted, values='건수', names='범죄유형', title="서울시 5대 범죄 발생 비중",
                          hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig2, use_container_width=True)
            
        with col2_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql2, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 전체 범죄 중 '절도'와 '폭력'이 차지하는 비중이 매우 높음을 확인할 수 있습니다.
            - 살인이나 강도와 같은 중범죄의 절대적인 건수는 상대적으로 적습니다.
            - 생활 범죄 예방을 위한 CCTV 활용이 중요함을 시사합니다.
            - 성범죄 비중 또한 적지 않아 이에 대한 집중적인 관리가 필요해 보입니다.
            """)

        st.divider()

        # --- 차트 3: CCTV 수 vs 범죄율 (산점도) ---
        st.header("3. CCTV 설치 수와 범죄율의 상관관계")
        
        # 3개 테이블 조인 및 범죄율 계산 SQL
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
                             trendline="ols", title="CCTV 수와 인구 10만명당 범죄율 관계",
                             labels={'cctv수': 'CCTV 설치 수', '범죄율': '범죄율 (인구 10만명당)'})
            st.plotly_chart(fig3, use_container_width=True)

        with col3_2:
            st.subheader("🔍 사용한 SQL")
            st.code(sql3, language='sql')
            st.subheader("💡 인사이트")
            st.write("""
            - 추세선(Trendline)을 통해 CCTV 수와 범죄율 간의 경향성을 확인합니다.
            - 단순 상관관계만 보면 CCTV가 많을수록 범죄 발생이 많은 것처럼 보일 수 있습니다(역설).
            - 이는 범죄가 많이 발생하는 곳에 CCTV를 더 많이 설치했기 때문일 수 있습니다(인과관계 주의).
            - 따라서 "CCTV가 범죄를 억제한다"는 결론을 내리려면 시간대별 변화 등 추가 분석이 필요합니다.
            """)

    except Exception as e:
        st.error(f"🚨 쿼리 실행 또는 시각화 중 오류가 발생했습니다.")
        st.info(f"**상세 오류 내용:** {e}")
        st.markdown("""
        ### 🛠️ 해결책:
        1. **컬럼명 확인:** DB의 테이블 컬럼명이 `자치구`, `cctv수`, `인구수` 등이 맞는지 확인하세요.
        2. **데이터 타입:** 숫자 데이터에 문자열이 포함되어 있는지 확인하세요.
        3. **테이블명:** `cctv`, `범죄데이터`, `서울인구` 테이블이 존재하는지 확인하세요.
        """)
    finally:
        conn.close()