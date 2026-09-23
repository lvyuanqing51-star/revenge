import plotly.graph_objects as go

# ---------------- 板块 E：选手六边形战力档案 ----------------
st.markdown("---")
st.subheader("🎯 选手六边形战力档案")

# 筛选出至少出场过 1 次的玩家供选择
active_player_options = sorted(list(df.index), key=lambda x: df.loc[x, "总场次"], reverse=True)

if active_player_options:
    c_sel, _ = st.columns([2, 3])
    with c_sel:
        target_p = st.selectbox("选择要分析的群友档案：", active_player_options, format_func=lambda x: short_name(x))
    
    p_data = df.loc[target_p]
    p_games = int(p_data["总场次"])
    p_wr = float(p_data["胜率_num"])
    p_kd = float(p_data["KD"])
    p_kda = float(p_data["KDA_num"])
    p_kills = float(p_data["场均击杀"])
    p_deaths = float(p_data["死亡"] / p_games) if p_games > 0 else 0.0
    p_assists = float(p_data["助攻"] / p_games) if p_games > 0 else 0.0

    # 归一化计算六边形得分 (0 - 100)
    score_kill = min(100.0, (p_kills / 10.0) * 100.0)
    score_surv = max(10.0, min(100.0, 100.0 - (p_deaths - 2.0) * 11.0)) if p_deaths >= 2 else 100.0
    score_assist = min(100.0, (p_assists / 12.0) * 100.0)
    score_kd = min(100.0, (p_kd / 3.0) * 100.0)
    score_kda = min(100.0, (p_kda / 5.0) * 100.0)
    score_wr = min(100.0, p_wr * 1.0)

    categories = ['击杀爆发', '保命生存', '团队助攻', 'KD压制', '综合KDA', '胜率掌控']
    values = [round(score_kill, 1), round(score_surv, 1), round(score_assist, 1), round(score_kd, 1), round(score_kda, 1), round(score_wr, 1)]
    # 闭合雷达图
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    # 评定等级称号
    avg_score = round(sum(values) / len(values), 1)
    if avg_score >= 85:
        tier_title, tier_badge = "👑 S+ 独断万古通天代", "delta-pink"
    elif avg_score >= 70:
        tier_title, tier_badge = "🔥 A 级 稳健中流砥柱", "delta-gold"
    elif avg_score >= 55:
        tier_title, tier_badge = "🛡️ B 级 团队基石工兵", "delta-blue"
    else:
        tier_title, tier_badge = "🌱 C 级 随缘摸鱼先锋", "delta-gray"

    col_radar, col_detail = st.columns([1.3, 1])

    with col_radar:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            fillcolor='rgba(244, 63, 94, 0.25)',
            line=dict(color='#e11d48', width=2),
            marker=dict(size=5, color='#be185d'),
            name=short_name(target_p)
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], color="#94a3b8", showticklabels=False),
                angularaxis=dict(color="#881337", font=dict(size=12, family="sans-serif", weight="bold"))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=30, b=30),
            height=320,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_detail:
        st.markdown(f"""
            <div class="stat-card" style="margin-top:20px;">
                <div class="stat-card-title">选手能力综合评定</div>
                <div class="stat-card-player">{short_name(target_p)}</div>
                <div class="stat-card-delta {tier_badge}">{tier_title} (综评: {avg_score})</div>
                <div style="font-size:0.85rem;color:#64748b;line-height:1.8;margin-top:10px;">
                    <div>• <b>出场局次</b>: {p_games} 局 (胜率: <span style="color:#e11d48;font-weight:700;">{p_wr}%</span>)</div>
                    <div>• <b>场均数据</b>: {p_kills:.1f} 杀 / {p_deaths:.1f} 亡 / {p_assists:.1f} 助</div>
                    <div>• <b>攻防比率</b>: KD {p_kd:.2f} ｜ KDA {p_kda:.2f}</div>
                    <div>• <b>当前 MMR</b>: <span style="color:#0284c7;font-weight:800;">{p_data['MMR']:.1f} 分</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
