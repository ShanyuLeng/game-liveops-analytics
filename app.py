import streamlit as st
import pandas as pd
import numpy as np


# ==========================================
# 1. 页面设置
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

    players = pd.read_csv(
        "demo_players.csv",
        parse_dates=["install_date"]
    )

    activity = pd.read_csv(
        "demo_daily_activity.csv",
        parse_dates=["date"]
    )

    payments = pd.read_csv(
        "demo_payments.csv",
        parse_dates=["payment_date"]
    )

    marketing = pd.read_csv(
        "demo_marketing.csv",
        parse_dates=["date"]
    )

    liveops = pd.read_csv(
        "liveops_event_uplift.csv"
    )

    insights = pd.read_csv(
        "auto_insights.csv"
    )

    return (
        players,
        activity,
        payments,
        marketing,
        liveops,
        insights
    )


(
    players,
    activity,
    payments,
    marketing,
    liveops,
    insights
) = load_data()


OBSERVATION_END = activity["date"].max()


# ==========================================
# 3. 左侧交互筛选器
# ==========================================

st.sidebar.title(
    "🎛️ 数据筛选"
)

st.sidebar.caption(
    "选择不同玩家群体后，核心指标将自动重新计算。"
)


country_filter = st.sidebar.selectbox(
    "市场",
    [
        "All",
        "JP",
        "US"
    ]
)


platform_filter = st.sidebar.selectbox(
    "平台",
    [
        "All",
        "iOS",
        "Android"
    ]
)


channel_filter = st.sidebar.selectbox(
    "渠道",
    [
        "All",
        "TikTok",
        "Meta",
        "Google",
        "Organic"
    ]
)


# ==========================================
# 4. 根据筛选条件选择玩家
# ==========================================

filtered_players = players.copy()


if country_filter != "All":

    filtered_players = filtered_players[
        filtered_players["country"]
        == country_filter
    ]


if platform_filter != "All":

    filtered_players = filtered_players[
        filtered_players["platform"]
        == platform_filter
    ]


if channel_filter != "All":

    filtered_players = filtered_players[
        filtered_players["channel"]
        == channel_filter
    ]


selected_user_ids = set(
    filtered_players["user_id"]
)


if len(selected_user_ids) == 0:

    st.warning(
        "当前筛选条件下没有玩家数据，请调整筛选条件。"
    )

    st.stop()


# ==========================================
# 5. 同步筛选行为和付费数据
# ==========================================

filtered_activity = activity[
    activity["user_id"].isin(
        selected_user_ids
    )
].copy()


filtered_payments = payments[
    payments["user_id"].isin(
        selected_user_ids
    )
].copy()


# Marketing 数据按相同维度筛选

filtered_marketing = marketing.copy()


if country_filter != "All":

    filtered_marketing = filtered_marketing[
        filtered_marketing["country"]
        == country_filter
    ]


if platform_filter != "All":

    filtered_marketing = filtered_marketing[
        filtered_marketing["platform"]
        == platform_filter
    ]


if channel_filter != "All":

    filtered_marketing = filtered_marketing[
        filtered_marketing["channel"]
        == channel_filter
    ]


# ==========================================
# 6. 计算动态 DAU / MAU
# ==========================================

@st.cache_data
def calculate_daily_kpis(
    activity_data,
    start_date,
    end_date
):

    all_dates = pd.date_range(
        start_date,
        end_date,
        freq="D"
    )


    # DAU
    dau = (
        activity_data
        .groupby("date")["user_id"]
        .nunique()
        .reindex(
            all_dates,
            fill_value=0
        )
    )


    # Rolling 30-Day MAU
    mau_values = []

    for current_date in all_dates:

        window_start = (
            current_date
            - pd.Timedelta(days=29)
        )

        mau_value = (
            activity_data.loc[
                (
                    activity_data["date"]
                    >= window_start
                )
                &
                (
                    activity_data["date"]
                    <= current_date
                ),
                "user_id"
            ]
            .nunique()
        )

        mau_values.append(
            mau_value
        )


    daily_kpis = pd.DataFrame({
        "date": all_dates,
        "DAU": dau.values,
        "MAU": mau_values
    })


    daily_kpis["DAU_MAU_pct"] = np.where(
        daily_kpis["MAU"] > 0,
        (
            daily_kpis["DAU"]
            / daily_kpis["MAU"]
            * 100
        ),
        0
    )


    return daily_kpis


daily_kpis = calculate_daily_kpis(
    filtered_activity,
    activity["date"].min(),
    activity["date"].max()
)


# ==========================================
# 7. 动态 Retention
# ==========================================

def calculate_retention(
    player_data,
    activity_data,
    retention_days=[
        1,
        7,
        30
    ]
):

    results = []


    for day in retention_days:

        eligible_players = (
            player_data[
                player_data["install_date"]
                + pd.Timedelta(days=day)
                <= OBSERVATION_END
            ]
        )


        eligible_ids = set(
            eligible_players["user_id"]
        )


        retained_ids = set(
            activity_data.loc[
                activity_data[
                    "day_since_install"
                ] == day,
                "user_id"
            ]
        )


        retained_count = len(
            eligible_ids
            & retained_ids
        )


        eligible_count = len(
            eligible_ids
        )


        retention_pct = (
            retained_count
            / eligible_count
            * 100
            if eligible_count > 0
            else 0
        )


        results.append({
            "retention_day":
                f"D{day}",

            "eligible_users":
                eligible_count,

            "retained_users":
                retained_count,

            "retention_pct":
                retention_pct
        })


    return pd.DataFrame(
        results
    )


retention = calculate_retention(
    filtered_players,
    filtered_activity
)


retention_dict = dict(
    zip(
        retention["retention_day"],
        retention["retention_pct"]
    )
)


d1 = retention_dict.get(
    "D1",
    0
)

d7 = retention_dict.get(
    "D7",
    0
)

d30 = retention_dict.get(
    "D30",
    0
)


# ==========================================
# 8. 商业化核心指标
# ==========================================

total_users = filtered_players[
    "user_id"
].nunique()


total_revenue = filtered_payments[
    "amount_usd"
].sum()


paying_users = filtered_payments[
    "user_id"
].nunique()


payer_rate = (
    paying_users
    / total_users
    * 100
    if total_users > 0
    else 0
)


arpu = (
    total_revenue
    / total_users
    if total_users > 0
    else 0
)


arppu = (
    total_revenue
    / paying_users
    if paying_users > 0
    else 0
)


d30_revenue = filtered_payments.loc[
    filtered_payments[
        "day_since_install"
    ] <= 30,
    "amount_usd"
].sum()


d30_ltv = (
    d30_revenue
    / total_users
    if total_users > 0
    else 0
)


# ==========================================
# 9. 最新 DAU / MAU
# ==========================================

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
    latest_row[
        "DAU_MAU_pct"
    ]
)


# ==========================================
# 10. 动态渠道 Retention
# ==========================================

def calculate_channel_retention(
    player_data,
    activity_data
):

    results = []


    for (
        channel_name,
        channel_players
    ) in player_data.groupby(
        "channel"
    ):

        channel_user_ids = set(
            channel_players[
                "user_id"
            ]
        )


        channel_activity = (
            activity_data[
                activity_data[
                    "user_id"
                ].isin(
                    channel_user_ids
                )
            ]
        )


        retention_result = (
            calculate_retention(
                channel_players,
                channel_activity
            )
        )


        retention_values = dict(
            zip(
                retention_result[
                    "retention_day"
                ],
                retention_result[
                    "retention_pct"
                ]
            )
        )


        results.append({
            "channel":
                channel_name,

            "D1":
                retention_values.get(
                    "D1",
                    0
                ),

            "D7":
                retention_values.get(
                    "D7",
                    0
                ),

            "D30":
                retention_values.get(
                    "D30",
                    0
                )
        })


    return pd.DataFrame(
        results
    )


channel_retention = (
    calculate_channel_retention(
        filtered_players,
        filtered_activity
    )
)


# ==========================================
# 11. 动态渠道商业化
# ==========================================

channel_monetization_results = []


for (
    channel_name,
    channel_players
) in filtered_players.groupby(
    "channel"
):

    channel_ids = set(
        channel_players[
            "user_id"
        ]
    )


    channel_payments = (
        filtered_payments[
            filtered_payments[
                "user_id"
            ].isin(
                channel_ids
            )
        ]
    )


    users = len(
        channel_ids
    )


    revenue = channel_payments[
        "amount_usd"
    ].sum()


    paying_users_channel = (
        channel_payments[
            "user_id"
        ]
        .nunique()
    )


    payer_rate_channel = (
        paying_users_channel
        / users
        * 100
        if users > 0
        else 0
    )


    arpu_channel = (
        revenue
        / users
        if users > 0
        else 0
    )


    arppu_channel = (
        revenue
        / paying_users_channel
        if paying_users_channel > 0
        else 0
    )


    d30_revenue_channel = (
        channel_payments.loc[
            channel_payments[
                "day_since_install"
            ] <= 30,
            "amount_usd"
        ]
        .sum()
    )


    d30_ltv_channel = (
        d30_revenue_channel
        / users
        if users > 0
        else 0
    )


    channel_monetization_results.append({
        "channel":
            channel_name,

        "users":
            users,

        "payer_rate_pct":
            payer_rate_channel,

        "ARPU":
            arpu_channel,

        "ARPPU":
            arppu_channel,

        "D30_LTV":
            d30_ltv_channel
    })


channel_monetization = pd.DataFrame(
    channel_monetization_results
)


# ==========================================
# 12. 动态渠道投放
# ==========================================

if len(filtered_marketing) > 0:

    channel_ua = (
        filtered_marketing
        .groupby("channel")
        .agg(
            spend=(
                "spend",
                "sum"
            ),
            impressions=(
                "impressions",
                "sum"
            ),
            clicks=(
                "clicks",
                "sum"
            ),
            installs=(
                "installs",
                "sum"
            ),
            D30_revenue=(
                "D30_revenue",
                "sum"
            )
        )
        .reset_index()
    )


    channel_ua["CTR_pct"] = (
        channel_ua["clicks"]
        / channel_ua[
            "impressions"
        ]
        * 100
    )


    channel_ua["CPI"] = (
        channel_ua["spend"]
        / channel_ua[
            "installs"
        ]
    )


    channel_ua[
        "D30_ROAS_pct"
    ] = (
        channel_ua[
            "D30_revenue"
        ]
        / channel_ua[
            "spend"
        ]
        * 100
    )

else:

    channel_ua = pd.DataFrame(
        columns=[
            "channel",
            "spend",
            "CTR_pct",
            "CPI",
            "D30_ROAS_pct"
        ]
    )


# ==========================================
# 13. 合并渠道表现
# ==========================================

channel_summary = (
    channel_retention
    .merge(
        channel_monetization,
        on="channel",
        how="left"
    )
    .merge(
        channel_ua[[
            "channel",
            "spend",
            "CTR_pct",
            "CPI",
            "D30_ROAS_pct"
        ]],
        on="channel",
        how="left"
    )
)


# 数字保留两位
numeric_columns = [
    "D1",
    "D7",
    "D30",
    "payer_rate_pct",
    "ARPU",
    "ARPPU",
    "D30_LTV",
    "CTR_pct",
    "CPI",
    "D30_ROAS_pct"
]


for col in numeric_columns:

    if col in channel_summary.columns:

        channel_summary[col] = (
            channel_summary[col]
            .round(2)
        )


# ==========================================
# 14. Dashboard 标题
# ==========================================

st.title(
    "🎮 游戏运营增长分析 Dashboard"
)


st.caption(
    "模拟游戏数据｜用户、留存、商业化、"
    "渠道投放、LiveOps 与自动运营诊断"
)


st.info(
    "说明：本 Dashboard 使用 Synthetic Data（模拟数据）"
    "进行功能演示，不代表《第五人格》"
    "或任何真实游戏的内部数据。"
)


# ==========================================
# 15. 显示当前筛选条件
# ==========================================

filter_text = (
    f"市场：{country_filter} ｜ "
    f"平台：{platform_filter} ｜ "
    f"渠道：{channel_filter}"
)


st.sidebar.divider()


st.sidebar.markdown(
    "**当前样本**"
)


st.sidebar.metric(
    "玩家数",
    f"{total_users:,}"
)


st.caption(
    f"当前筛选：**{filter_text}**"
)


# ==========================================
# 16. 页面导航
# ==========================================

tab1, tab2, tab3, tab4, tab5 = (
    st.tabs(
        [
            "📊 总览",
            "👥 留存",
            "💰 商业化",
            "📣 渠道投放",
            "🎮 LiveOps & 运营诊断"
        ]
    )
)


# ==========================================
# 17. 总览
# ==========================================

with tab1:

    st.subheader(
        "核心运营指标"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


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
        "玩家数",
        f"{total_users:,}"
    )


    col5, col6, col7, col8 = (
        st.columns(4)
    )


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
            [
                "date",
                "DAU"
            ]
        ]
        .set_index(
            "date"
        )
    )


    st.line_chart(
        dau_chart
    )


    st.subheader(
        "Retention"
    )


    retention_chart = pd.DataFrame(
        {
            "Retention": [
                d1,
                d7,
                d30
            ]
        },
        index=[
            "D1",
            "D7",
            "D30"
        ]
    )


    st.bar_chart(
        retention_chart
    )


# ==========================================
# 18. 留存页
# ==========================================

with tab2:

    st.subheader(
        "核心 Retention"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


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
        .set_index(
            "date"
        )
    )


    st.line_chart(
        stickiness_chart
    )


    st.caption(
        "注意：观察期前30天的 MAU 窗口尚未完全形成，"
        "因此早期 DAU / MAU 不宜直接作为稳定期判断依据。"
    )


# ==========================================
# 19. 商业化页
# ==========================================

with tab3:

    st.subheader(
        "商业化核心指标"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


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


    monetization_display = (
        channel_summary[[
            "channel",
            "users",
            "payer_rate_pct",
            "ARPU",
            "ARPPU",
            "D30_LTV"
        ]]
        .rename(
            columns={
                "channel":
                    "渠道",

                "users":
                    "用户数",

                "payer_rate_pct":
                    "付费率 (%)",

                "D30_LTV":
                    "D30 LTV"
            }
        )
    )


    st.dataframe(
        monetization_display,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 20. 渠道投放页
# ==========================================

with tab4:

    st.subheader(
        "付费渠道综合表现"
    )


    paid_channels = (
        channel_summary[
            channel_summary[
                "channel"
            ] != "Organic"
        ]
        .copy()
    )


    if len(
        paid_channels
    ) == 0:

        st.info(
            "当前筛选为 Organic（自然量），"
            "不存在广告 Spend、CPI 和 ROAS。"
        )


    else:

        channel_display = (
            paid_channels[[
                "channel",
                "D7",
                "D30",
                "payer_rate_pct",
                "D30_LTV",
                "CTR_pct",
                "CPI",
                "D30_ROAS_pct"
            ]]
            .rename(
                columns={
                    "channel":
                        "渠道",

                    "D7":
                        "D7 Retention (%)",

                    "D30":
                        "D30 Retention (%)",

                    "payer_rate_pct":
                        "付费率 (%)",

                    "D30_LTV":
                        "D30 LTV",

                    "CTR_pct":
                        "CTR (%)",

                    "CPI":
                        "CPI",

                    "D30_ROAS_pct":
                        "D30 ROAS (%)"
                }
            )
        )


        st.dataframe(
            channel_display,
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
            .set_index(
                "channel"
            )
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
            f"当前筛选条件下，"
            f"{best_channel['channel']} "
            f"的 D30 ROAS 最高，为 "
            f"{best_channel['D30_ROAS_pct']:.2f}%。"
        )


# ==========================================
# 21. LiveOps + 自动诊断
# ==========================================

with tab5:

    st.warning(
        "当前版本的 LiveOps Uplift 和自动运营诊断"
        "基于全量模拟数据，因此暂不随左侧筛选器动态变化。"
        "后续版本将加入动态诊断。"
    )


    st.subheader(
        "LiveOps 活动增量表现"
    )


    liveops_display = (
        liveops.rename(
            columns={
                "event_name":
                    "活动",

                "baseline_avg_DAU":
                    "基线平均 DAU",

                "liveops_avg_DAU":
                    "活动平均 DAU",

                "DAU_uplift_pct":
                    "DAU Uplift (%)",

                "baseline_avg_revenue":
                    "基线平均 Revenue",

                "liveops_avg_revenue":
                    "活动平均 Revenue",

                "Revenue_uplift_pct":
                    "Revenue Uplift (%)"
            }
        )
    )


    st.dataframe(
        liveops_display,
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
        .set_index(
            "event_name"
        )
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
            f"{row['category']} ｜ "
            f"{row['target']} ｜ "
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
# 22. 页脚
# ==========================================

st.divider()


st.caption(
    "Game LiveOps Analytics Project ｜ "
    "用于展示游戏运营、商业化、渠道与数据分析能力"
)
