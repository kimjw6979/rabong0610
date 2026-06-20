import streamlit as st
import pandas as pd
import random

# 페이지 설정
st.set_page_config(page_title="🐻곰탱이볼링클럽🎳", layout="wide")

st.title("🐻곰탱이볼링클럽🎳 팀/레인 배정 프로그램")
st.markdown("엑셀 파일을 업로드하고 팀을 구성하세요.")

# 1. 파일 업로드 (사이드바)
with st.sidebar:
    st.header("파일 업로드")
    score_file = st.file_uploader("분기에버.xlsx", type=['xlsx'])
    attend_file = st.file_uploader("참석자명단.xlsx", type=['xlsx'])
    num_teams = st.number_input("나눌 팀 개수(2~3)", min_value=2, max_value=3, value=2)

# 2. 메인 로직 실행
if score_file and attend_file:
    try:
        # 파일 로드
        scores_df = pd.read_excel(score_file, header=6)
        attend_df = pd.read_excel(attend_file)

        # 데이터 전처리 로직
        def parse_name(name):
            name_str = str(name).strip().replace(' ', '')
            is_female = name_str.endswith('W')
            clean_name = name_str[:-1] if is_female else name_str
            return clean_name, is_female

        parsed_data = scores_df['이 름'].apply(parse_name).tolist()
        scores_df['이름_cleaned'] = [x[0] for x in parsed_data]
        scores_df['is_female'] = [x[1] for x in parsed_data]
        attend_df['이름_cleaned'] = attend_df['이름'].astype(str).str.replace(' ', '')
        
        df = pd.merge(scores_df, attend_df, on='이름_cleaned')
        df['참석'] = df['참석'].astype(str).str.strip().str.upper()
        attendees = df[df['참석'] == 'O'].copy()

        if attendees.empty:
            st.error("참석자(O)가 없습니다. 참석자명단.xlsx를 확인해주세요.")
            st.stop()

        if st.button("팀 구성 시작"):
            st.success(f"총 {len(attendees)}명의 참석자가 확인되었습니다.")
            
            # 인원수 맞추기
            remainder = len(attendees) % num_teams
            target_size = len(attendees) // num_teams 
            
            if remainder != 0:
                attendees = attendees.sort_values(by='적용에버', ascending=True)
                excluded_people = attendees.iloc[:remainder]
                st.warning(f"각 팀 인원을 {target_size}명으로 맞추기 위해 가장 점수가 낮은 {remainder}명을 제외합니다.")
                st.write(excluded_people[['이 름', '적용에버']])
                df_for_teams = attendees.iloc[remainder:].copy()
            else:
                df_for_teams = attendees.copy()

            # 팀 나누기 로직
            females = df_for_teams[df_for_teams['is_female'] == True].sort_values(by='적용에버', ascending=False)
            males = df_for_teams[df_for_teams['is_female'] == False].sort_values(by='적용에버', ascending=False)

            teams = [{'members': [], 'sum': 0, 'f_count': 0} for _ in range(num_teams)]

            # 여성 분배
            for _, row in females.iterrows():
                min_f = min(t['f_count'] for t in teams)
                candidate_teams = [t for t in teams if t['f_count'] == min_f]
                target_team = min(candidate_teams, key=lambda x: x['sum'])
                target_team['members'].append(row)
                target_team['sum'] += row['적용에버']
                target_team['f_count'] += 1

            # 남성 분배
            for _, row in males.iterrows():
                candidate_teams = [t for t in teams if len(t['members']) < target_size]
                target_team = min(candidate_teams, key=lambda x: x['sum'])
                target_team['members'].append(row)
                target_team['sum'] += row['적용에버']

            # 결과 출력
            st.subheader("=== 팀 구성 결과 ===")
            cols = st.columns(num_teams)
            for i in range(num_teams):
                with cols[i]:
                    names = [member['이 름'] for member in teams[i]['members']]
                    avg_score = teams[i]['sum'] / len(teams[i]['members']) if len(teams[i]['members']) > 0 else 0
                    st.markdown(f"**[팀 {i+1}]** (인원: {len(names)}명, 여성: {teams[i]['f_count']}명)")
                    st.write(f"구성원: {', '.join(names)}")
                    st.write(f"평균 에버: {avg_score:.2f}")

            # 레인 배정
            active_count = sum(len(t['members']) for t in teams)
            num_lanes = 6 if active_count <= 18 else 8
            lanes = [[] for _ in range(num_lanes)]
            
            # [Case 1 & 2] 레인 배정 로직 (기존 로직 유지)
            if num_teams == 2:
                odd_lane_indices = [idx for idx in range(num_lanes) if idx % 2 == 0]
                even_lane_indices = [idx for idx in range(num_lanes) if idx % 2 != 0]
                even_lane_indices.reverse()
                
                t1_players = [f"[팀1] {m['이 름']}" for m in teams[0]['members']]
                random.shuffle(t1_players)
                for idx, player in enumerate(t1_players):
                    lanes[odd_lane_indices[idx % len(odd_lane_indices)]].append(player)
                
                t2_players = [f"[팀2] {m['이 름']}" for m in teams[1]['members']]
                random.shuffle(t2_players)
                for idx, player in enumerate(t2_players):
                    lanes[even_lane_indices[idx % len(even_lane_indices)]].append(player)
            
            elif num_teams == 3:
                team_lane_map = {0: [], 1: [], 2: []}
                for i in range(num_lanes):
                    team_lane_map[i // 2 if i < 6 else (i-6)].append(i)
                for t_idx in range(3):
                    t_players = [f"[팀{t_idx+1}] {m['이 름']}" for m in teams[t_idx]['members']]
                    random.shuffle(t_players)
                    for idx, player in enumerate(t_players):
                        lanes[team_lane_map[t_idx][idx % len(team_lane_map[t_idx])]].append(player)

            st.subheader("=== 🎲 랜덤 레인 배정 결과 ===")
            for i in range(num_lanes):
                st.write(f"**레인 {i+1}** ({len(lanes[i])}명): {', '.join(lanes[i])}")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 두 개의 엑셀 파일을 업로드해주세요.")