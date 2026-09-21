import streamlit as st
import pandas as pd


# ==========================================
# 1. 页面基础设置
# ==========================================

st.set_page_config(
    page_title="游戏运营增长分析 Dashboard",
    page_icon="🎮",
    layout="wide"
)


# ==========================================
# 2. 读取数据
# ==========================================

@st.cache_data
def load_data():

    daily_kpis = pd.read_csv(
        "daily_kpis.csv"
    )

    retention = pd.read_csv(
        "retention_summary.csv"
    )

    players = pd.read_csv(
        "demo_players.csv"
    )

    payments = pd.read_csv(
        "demo_payments.csv"
    )

    channel_performance = pd.read_csv(
        "channel_performance_summary.csv"
    )

    liveops = pd.read_csv(
        "liveops_event_uplift.csv"
    )

    insights = pd.read_csv(
        "auto_insights.csv"
    )

    return (
        daily_kpis,
        retention,
        players,
        payments,
        channel_performance,
        liveops,
        insights
    )


(
    daily_kpis,
    retention,
    players,
    payments,
    channel_performance,
    liveops,
    insights
) = load_data()


# 日期格式
daily_kpis["date"] = pd.to_datetime(
    daily_kpis["date"]
)

payments["payment_date"] = pd.to_datetime(
    payments["payment_date"]
)


# ==========================================
# 3. 计算核心指标
# ==========================================

total_users = players[
    "user_id"
].nunique()

total_revenue = payments[
    "amount_usd"
].sum()

paying_users = payments[
    "user_id"
].nunique()

payer_rate = (
    paying_users
    / total_users
    * 100
)

arpu = (
    total_revenue
    / total_users
)

arppu = (
    total_revenue
    / paying_users
)

d30_revenue = payments.loc[
    payments["day_since_install"] <= 30,
    "amount_usd"
].sum()

d30_ltv = (
    d30_revenue
    / total_users
)


# 最新 DAU / MAU
latest_row = (
    daily_kpis
    .sort_values("date")
    .iloc[-1]
)

latest_dau = int(
    latest_row["DAU"]
)

latest_mau = int(
    latest_row["MAU"]
)

latest_stickiness = (
    latest_row["DAU_MAU_pct"]
)


# Retention
retention_dict = dict(
    zip(
        retention["retention_day"],
        retention["retention_pct"]
    )
)

d1 = retention_dict["D1"]
d7 = retention_dict["D7"]
d30 = retention_dict["D30"]


# ==========================================
# 4. 页面标题
# ==========================================

st.title(
    "🎮 游戏运营增长分析 Dashboard"
)

st.caption(
    "模拟游戏数据｜用户、留存、商业化、渠道投放、LiveOps 与自动运营诊断"
)

st.info(
    "说明：本 Dashboard 使用 Synthetic Data（模拟数据）进行功能演示，"
    "不代表《第五人格》或任何真实游戏的内部数据。"
)


# ==========================================
# 5. 页面导航
# ==========================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 总览",
        "👥 留存",
        "💰 商业化",
        "📣 渠道投放",
        "🎮 LiveOps & 运营诊断"
    ]
)


# ==========================================
# 6. 总览
# ==========================================

with tab1:

    st.subheader(
        "核心运营指标"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "最新 DAU",
        f"{latest_dau:,}"
    )

    col2.metric(
        "最新 MAU",
        f"{latest_mau:,}"
    )

    col3.metric(
        "DAU / MAU",
        f"{latest_stickiness:.2f}%"
    )

    col4.metric(
        "总玩家数",
        f"{total_users:,}"
    )


    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Revenue",
        f"${total_revenue:,.0f}"
    )

    col6.metric(
        "付费率",
        f"{payer_rate:.2f}%"
    )

    col7.metric(
        "ARPU",
        f"${arpu:.2f}"
    )

    col8.metric(
        "ARPPU",
        f"${arppu:.2f}"
    )


    st.divider()


    st.subheader(
        "DAU 趋势"
    )

    dau_chart = (
        daily_kpis[
            ["date", "DAU"]
        ]
        .set_index("date")
    )

    st.line_chart(
        dau_chart
    )


    st.subheader(
        "Retention"
    )

    retention_chart = pd.DataFrame({
        "Retention": [
            d1,
            d7,
            d30
        ]
    }, index=[
        "D1",
        "D7",
        "D30"
    ])

    st.bar_chart(
        retention_chart
    )


# ==========================================
# 7. 留存
# ==========================================

with tab2:

    st.subheader(
        "核心 Retention"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "D1 Retention",
        f"{d1:.2f}%"
    )

    col2.metric(
        "D7 Retention",
        f"{d7:.2f}%"
    )

    col3.metric(
        "D30 Retention",
        f"{d30:.2f}%"
    )


    st.subheader(
        "DAU / MAU Stickiness 趋势"
    )

    stickiness_chart = (
        daily_kpis[
            [
                "date",
                "DAU_MAU_pct"
            ]
        ]
        .set_index("date")
    )

    st.line_chart(
        stickiness_chart
    )


    st.caption(
        "注意：观察期前30天的 MAU 窗口尚未完全形成，"
        "因此早期 DAU / MAU 不宜直接作为稳定期判断依据。"
    )


# ==========================================
# 8. 商业化
# ==========================================

with tab3:

    st.subheader(
        "商业化核心指标"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Revenue",
        f"${total_revenue:,.2f}"
    )

    col2.metric(
        "付费率",
        f"{payer_rate:.2f}%"
    )

    col3.metric(
        "ARPU",
        f"${arpu:.2f}"
    )

    col4.metric(
        "ARPPU",
        f"${arppu:.2f}"
    )


    st.metric(
        "D30 LTV",
        f"${d30_ltv:.2f}"
    )


    st.subheader(
        "渠道用户商业化表现"
    )

    monetization_table = (
        channel_performance[[
            "channel",
            "payer_rate_pct",
            "ARPU",
            "ARPPU",
            "D30_LTV"
        ]]
    )

    st.dataframe(
        monetization_table,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 9. 渠道投放
# ==========================================

with tab4:

    st.subheader(
        "付费渠道综合表现"
    )

    paid_channels = (
        channel_performance[
            channel_performance[
                "channel"
            ] != "Organic"
        ]
        .copy()
    )


    st.dataframe(
        paid_channels[[
            "channel",
            "D7",
            "D30",
            "payer_rate_pct",
            "D30_LTV",
            "CTR_pct",
            "CPI",
            "D30_ROAS_pct"
        ]],
        use_container_width=True,
        hide_index=True
    )


    st.subheader(
        "D30 ROAS"
    )

    roas_chart = (
        paid_channels[
            [
                "channel",
                "D30_ROAS_pct"
            ]
        ]
        .set_index("channel")
    )

    st.bar_chart(
        roas_chart
    )


    best_channel = (
        paid_channels
        .sort_values(
            "D30_ROAS_pct",
            ascending=False
        )
        .iloc[0]
    )


    st.success(
        f"当前模拟数据中，{best_channel['channel']} "
        f"的 D30 ROAS 最高，为 "
        f"{best_channel['D30_ROAS_pct']:.2f}%。"
    )


# ==========================================
# 10. LiveOps + 自动诊断
# ==========================================

with tab5:

    st.subheader(
        "LiveOps 活动增量表现"
    )

    st.dataframe(
        liveops,
        use_container_width=True,
        hide_index=True
    )


    st.subheader(
        "活动 Revenue Uplift"
    )

    liveops_chart = (
        liveops[
            [
                "event_name",
                "Revenue_uplift_pct"
            ]
        ]
        .set_index("event_name")
    )

    st.bar_chart(
        liveops_chart
    )


    st.divider()


    st.subheader(
        "自动运营诊断"
    )

    for _, row in insights.iterrows():

        with st.expander(
            f"{row['category']}｜"
            f"{row['target']}｜"
            f"{row['signal']}"
        ):

            st.write(
                "**诊断：**",
                row["diagnosis"]
            )

            st.write(
                "**建议：**",
                row["recommendation"]
            )


# ==========================================
# 11. 页脚
# ==========================================

st.divider()

st.caption(
    "Game LiveOps Analytics Project｜"
    "用于展示游戏运营、商业化、渠道与数据分析能力"
)
