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
# UI 样式优化
# ==========================================

st.markdown(
    """
    <style>

    /* 页面最大宽度 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* KPI 指标卡 */
    div[data-testid="stMetric"] {
        background-color: #f7f8fa;
        border: 1px solid #e5e7eb;
        padding: 16px 18px;
        border-radius: 12px;
    }

    /* 指标标题 */
    div[data-testid="stMetricLabel"] {
        font-size: 0.88rem;
        color: #60646c;
    }

    /* 指标数字 */
    div[data-testid="stMetricValue"] {
        font-size: 1.9rem;
        font-weight: 650;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    /* 缩小表格与标题之间距离 */
    h2, h3 {
        margin-top: 1.2rem;
    }

    </style>
    """,
    unsafe_allow_html=True
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

# ==========================================
# 数据来源选择
# ==========================================

st.sidebar.title(
    "📂 数据来源"
)

data_source = st.sidebar.radio(
    "选择分析数据",
    [
        "使用内置模拟数据",
        "上传自己的 CSV"
    ]
)

st.sidebar.divider()

# ==========================================
# CSV 上传
# ==========================================

uploaded_players = None
uploaded_activity = None
uploaded_payments = None
uploaded_marketing = None
uploaded_liveops = None


if data_source == "上传自己的 CSV":

    st.sidebar.subheader(
        "上传数据文件"
    )

    uploaded_players = st.sidebar.file_uploader(
        "① 玩家基础数据 players.csv",
        type=["csv"],
        key="players_upload"
    )

    uploaded_activity = st.sidebar.file_uploader(
        "② 每日活跃数据 daily_activity.csv",
        type=["csv"],
        key="activity_upload"
    )

    uploaded_payments = st.sidebar.file_uploader(
        "③ 付费数据 payments.csv",
        type=["csv"],
        key="payments_upload"
    )

    uploaded_marketing = st.sidebar.file_uploader(
        "④ 广告投放数据 marketing.csv（可选）",
        type=["csv"],
        key="marketing_upload"
    )

    uploaded_liveops = st.sidebar.file_uploader(
        "⑤ LiveOps 活动数据（可选）",
        type=["csv"],
        key="liveops_upload"
    )

# ==========================================
# 读取用户上传的数据
# ==========================================

if data_source == "上传自己的 CSV":

    # 三个核心文件必须全部上传
    if (
    uploaded_players is None
    or uploaded_activity is None
    or uploaded_payments is None
):

        st.info(
            "👈 请先在左侧上传 players、daily_activity "
            "和 payments 三个核心 CSV 文件。"
        )

        st.stop()


    try:

        # ------------------------------
        # 1. 读取玩家数据
        # ------------------------------

        uploaded_players_df = pd.read_csv(
            uploaded_players
        )

        required_player_cols = {
            "user_id",
            "install_date",
            "country",
            "platform",
            "channel"
        }

        missing_player_cols = (
            required_player_cols
            - set(uploaded_players_df.columns)
        )

        if missing_player_cols:

            st.error(
                "players.csv 缺少字段："
                + ", ".join(missing_player_cols)
            )

            st.stop()


        uploaded_players_df[
            "install_date"
        ] = pd.to_datetime(
            uploaded_players_df[
                "install_date"
            ]
        )


        # ------------------------------
        # 2. 读取活跃数据
        # ------------------------------

        uploaded_activity_df = pd.read_csv(
            uploaded_activity
        )

        required_activity_cols = {
            "user_id",
            "date",
            "day_since_install"
        }

        missing_activity_cols = (
            required_activity_cols
            - set(uploaded_activity_df.columns)
        )

        if missing_activity_cols:

            st.error(
                "daily_activity.csv 缺少字段："
                + ", ".join(
                    missing_activity_cols
                )
            )

            st.stop()


        uploaded_activity_df[
            "date"
        ] = pd.to_datetime(
            uploaded_activity_df["date"]
        )


        # ------------------------------
        # 3. 读取付费数据
        # ------------------------------

        uploaded_payments_df = pd.read_csv(
            uploaded_payments
        )

        required_payment_cols = {
            "user_id",
            "payment_date",
            "day_since_install",
            "amount_usd"
        }

        missing_payment_cols = (
            required_payment_cols
            - set(uploaded_payments_df.columns)
        )

        if missing_payment_cols:

            st.error(
                "payments.csv 缺少字段："
                + ", ".join(
                    missing_payment_cols
                )
            )

            st.stop()


        uploaded_payments_df[
            "payment_date"
        ] = pd.to_datetime(
            uploaded_payments_df[
                "payment_date"
            ]
        )


        # ------------------------------
        # 4. 用上传数据覆盖内置模拟数据
        # ------------------------------

        players = uploaded_players_df
        activity = uploaded_activity_df
        payments = uploaded_payments_df


        # ------------------------------
        # 5. 广告投放数据（可选）
        # ------------------------------

        if uploaded_marketing is not None:

            uploaded_marketing_df = pd.read_csv(
                uploaded_marketing
            )

            required_marketing_cols = {
                "date",
                "country",
                "platform",
                "channel",
                "spend",
                "impressions",
                "clicks",
                "installs"
            }

            missing_marketing_cols = (
                required_marketing_cols
                - set(
                    uploaded_marketing_df.columns
                )
            )

            if missing_marketing_cols:

                st.error(
                    "marketing.csv 缺少字段："
                    + ", ".join(
                        missing_marketing_cols
                    )
                )

                st.stop()


            uploaded_marketing_df[
                "date"
            ] = pd.to_datetime(
                uploaded_marketing_df["date"]
            )


            # 如果用户数据里没有 D30_revenue，
            # 根据玩家来源和30天付费自动计算

            if (
                "D30_revenue"
                not in uploaded_marketing_df.columns
            ):

                payment_attribution = (
                    payments.merge(
                        players[[
                            "user_id",
                            "install_date",
                            "country",
                            "platform",
                            "channel"
                        ]],
                        on="user_id",
                        how="left"
                    )
                )


                d30_revenue_by_cohort = (
                    payment_attribution[
                        payment_attribution[
                            "day_since_install"
                        ] <= 30
                    ]
                    .groupby([
                        "install_date",
                        "country",
                        "platform",
                        "channel"
                    ])["amount_usd"]
                    .sum()
                    .reset_index(
                        name="D30_revenue"
                    )
                )


                uploaded_marketing_df = (
                    uploaded_marketing_df.merge(
                        d30_revenue_by_cohort,
                        left_on=[
                            "date",
                            "country",
                            "platform",
                            "channel"
                        ],
                        right_on=[
                            "install_date",
                            "country",
                            "platform",
                            "channel"
                        ],
                        how="left"
                    )
                )


                uploaded_marketing_df.drop(
                    columns=["install_date"],
                    inplace=True
                )


                uploaded_marketing_df[
                    "D30_revenue"
                ] = (
                    uploaded_marketing_df[
                        "D30_revenue"
                    ]
                    .fillna(0)
                )


            marketing = uploaded_marketing_df


        else:

            # 没上传 marketing 时创建空表
            marketing = pd.DataFrame(
                columns=[
                    "date",
                    "country",
                    "platform",
                    "channel",
                    "spend",
                    "impressions",
                    "clicks",
                    "installs",
                    "D30_revenue"
                ]
            )


        # ------------------------------
        # 6. 更新观察截止日期
        # ------------------------------

        OBSERVATION_END = (
            activity["date"].max()
        )


        st.sidebar.success(
            "✅ 已切换为上传数据"
        )


    except Exception as e:

        st.error(
            f"读取 CSV 时出现错误：{e}"
        )

        st.stop()

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


if data_source == "使用内置模拟数据":

    st.info(
        "说明：本 Dashboard 使用 Synthetic Data（模拟数据）"
        "进行功能演示，不代表《第五人格》"
        "或任何真实游戏的内部数据。"
    )

else:

    st.success(
        "当前正在分析用户上传的 CSV 数据。"
        "所有指标均根据本次上传文件动态计算。"
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
# 当前样本概览
# ==========================================

sample_start = filtered_players[
    "install_date"
].min()

sample_end = filtered_players[
    "install_date"
].max()


overview_col1, overview_col2, overview_col3 = st.columns(
    [1.3, 1, 1]
)


with overview_col1:

    st.caption("当前分析人群")

    st.markdown(
        f"**{country_filter} / "
        f"{platform_filter} / "
        f"{channel_filter}**"
    )


with overview_col2:

    st.caption("安装日期范围")

    st.markdown(
        f"**{sample_start.strftime('%Y-%m-%d')} "
        f"至 {sample_end.strftime('%Y-%m-%d')}**"
    )


with overview_col3:

    st.caption("样本量")

    st.markdown(
        f"**{total_users:,} 名玩家**"
    )


st.divider()

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

    # ==========================================
# 当前样本快速解读
# ==========================================

st.markdown(
    "### 当前样本快速解读"
)


insight_messages = []


# 留存
if d7 >= 22:

    insight_messages.append(
        f"✅ D7 Retention 为 {d7:.2f}%，"
        "在当前模拟样本中表现相对较强。"
    )

elif d7 < 18:

    insight_messages.append(
        f"⚠️ D7 Retention 为 {d7:.2f}%，"
        "建议进一步检查 Day 2–7 的内容承接和活动节奏。"
    )

else:

    insight_messages.append(
        f"ℹ️ D7 Retention 为 {d7:.2f}%，"
        "目前处于中等水平，可继续结合渠道和市场拆分观察。"
    )


# 付费
if payer_rate >= 10:

    insight_messages.append(
        f"✅ 付费率为 {payer_rate:.2f}%，"
        "该玩家群体的付费转化相对较好。"
    )

elif payer_rate < 7:

    insight_messages.append(
        f"⚠️ 付费率为 {payer_rate:.2f}%，"
        "建议关注首充、礼包设计和早期付费触点。"
    )

else:

    insight_messages.append(
        f"ℹ️ 付费率为 {payer_rate:.2f}%，"
        "可进一步结合 ARPPU 判断问题更偏付费转化还是付费深度。"
    )


# ARPU
insight_messages.append(
    f"💰 当前 ARPU 为 ${arpu:.2f}，"
    f"ARPPU 为 ${arppu:.2f}。"
)


for message in insight_messages:

    st.write(
        message
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
