
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="IPL Cricket Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 IPL Cricket Data Analytics Dashboard")
st.caption("Explore IPL seasons, teams, players, wickets and match performance.")

# ==========================================
# 2. LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    matches = pd.read_csv("data/matches.csv")
    deliveries = pd.read_csv("data/deliveries.csv")
    return matches, deliveries

try:
    matches, deliveries = load_data()
except FileNotFoundError:
    st.error(
        "Dataset files nahi mil rahi hain. "
        "Check karo ki matches.csv aur deliveries.csv "
        "dono Project IPL ke data folder mein hain."
    )
    st.stop()

# ==========================================
# 3. SIDEBAR FILTERS
# ==========================================
st.sidebar.header("Dashboard Filters")

seasons = sorted(
    matches["season"].dropna().unique().tolist(),
    reverse=True
)

season_options = ["All Seasons"] + seasons

selected_season = st.sidebar.selectbox(
    "Select IPL Season",
    season_options
)

if selected_season == "All Seasons":
    season_matches = matches.copy()
else:
    season_matches = matches[
        matches["season"] == selected_season
    ].copy()

teams = sorted(
    set(season_matches["team1"].dropna().unique())
    | set(season_matches["team2"].dropna().unique())
)

team_options = ["All Teams"] + teams

selected_team = st.sidebar.selectbox(
    "Select Team",
    team_options
)

# ==========================================
# 4. FILTER MATCHES AND DELIVERIES
# ==========================================
if selected_team == "All Teams":
    filtered_matches = season_matches.copy()
else:
    filtered_matches = season_matches[
        (season_matches["team1"] == selected_team)
        | (season_matches["team2"] == selected_team)
    ].copy()

filtered_deliveries = deliveries[
    deliveries["match_id"].isin(filtered_matches["id"])
].copy()

# Completed matches for win calculations
completed_matches = filtered_matches[
    filtered_matches["winner"].notna()
    & (filtered_matches["result"] != "no result")
].copy()

# ==========================================
# 5. KEY PERFORMANCE INDICATORS
# ==========================================
total_matches = len(filtered_matches)
total_deliveries = len(filtered_deliveries)

if selected_team == "All Teams":
    total_wins = completed_matches["winner"].notna().sum()

    win_rate = (
        total_wins / len(completed_matches) * 100
        if len(completed_matches) > 0
        else 0
    )
else:
    total_wins = (
        completed_matches["winner"] == selected_team
    ).sum()

    win_rate = (
        total_wins / len(completed_matches) * 100
        if len(completed_matches) > 0
        else 0
    )

c1, c2, c3, c4 = st.columns(4)

c1.metric("🏏 Matches Analyzed", f"{total_matches:,}")
c2.metric("🏆 Wins", f"{total_wins:,}")
c3.metric("📈 Win Rate", f"{win_rate:.1f}%")
c4.metric("🎯 Deliveries", f"{total_deliveries:,}")

st.divider()

# ==========================================
# 6. TEAM WINS CHART
# ==========================================
st.subheader("🏆 Team-wise Wins")

team_wins = (
    completed_matches["winner"]
    .value_counts()
    .rename_axis("Team")
    .reset_index(name="Wins")
)

if not team_wins.empty:
    fig = px.bar(
        team_wins,
        x="Team",
        y="Wins",
        color="Wins",
        title="Matches Won by Each Team",
        text="Wins"
    )

    fig.update_layout(
        xaxis_title="Team",
        yaxis_title="Total Wins",
        xaxis_tickangle=-35
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No completed matches found for these filters.")

st.divider()

# ==========================================
# 7. PLAYER OF THE MATCH AWARDS
# ==========================================
st.subheader("🌟 Top Players by Player of the Match Awards")

player_awards = (
    filtered_matches["player_of_match"]
    .dropna()
    .value_counts()
    .head(10)
    .rename_axis("Player")
    .reset_index(name="Awards")
)

if not player_awards.empty:
    fig = px.bar(
        player_awards,
        x="Player",
        y="Awards",
        color="Awards",
        text="Awards",
        title="Top 10 Player of the Match Award Winners"
    )

    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No player awards found for these filters.")

st.divider()

# ==========================================
# 8. TOP 10 BATTERS BY RUNS
# ==========================================
st.subheader("🏏 Top 10 Batters by Runs")

if selected_team == "All Teams":
    batting_data = filtered_deliveries.copy()
else:
    batting_data = filtered_deliveries[
        filtered_deliveries["batting_team"] == selected_team
    ].copy()

batters = (
    batting_data.groupby("batter")["batsman_runs"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

batters.columns = ["Batter", "Runs"]

if not batters.empty:
    fig = px.bar(
        batters,
        x="Batter",
        y="Runs",
        color="Runs",
        text="Runs",
        title="Top 10 Batters by Total Runs"
    )

    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No batting data found for these filters.")

st.divider()

# ==========================================
# 9. TOP 10 BOWLERS BY WICKETS
# ==========================================
st.subheader("🎯 Top 10 Bowlers by Wickets")

if selected_team == "All Teams":
    team_bowling = filtered_deliveries.copy()
else:
    team_bowling = filtered_deliveries[
        filtered_deliveries["bowling_team"] == selected_team
    ].copy()

# Only dismissals credited to the bowler
valid_dismissals = [
    "caught",
    "bowled",
    "lbw",
    "stumped",
    "caught and bowled",
    "hit wicket"
]

wickets_all = (
    team_bowling[
        team_bowling["dismissal_kind"].isin(valid_dismissals)
    ]
    .groupby("bowler")["is_wicket"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

wickets_all.columns = ["Bowler", "Wickets"]

# Keep only bowlers who have at least one credited wicket
wickets_all = wickets_all[
    wickets_all["Wickets"] > 0
].copy()

wickets = wickets_all.head(10)

if not wickets.empty:
    fig = px.bar(
        wickets,
        x="Bowler",
        y="Wickets",
        color="Wickets",
        text="Wickets",
        title="Top 10 Bowlers by Wickets"
    )

    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No credited bowling wickets found for these filters.")

st.divider()

# ==========================================
# 10. TEAM PERFORMANCE ANALYSIS
# ==========================================
st.subheader("📊 Team Performance Analysis")

if selected_team != "All Teams":

    played = filtered_matches.copy()

    completed = played[
        played["winner"].notna()
        & (played["result"] != "no result")
    ].copy()

    wins = (completed["winner"] == selected_team).sum()

    losses = (
        completed["winner"].notna()
        & (completed["winner"] != selected_team)
    ).sum()

    no_result = (
        played["winner"].isna()
        | (played["result"] == "no result")
    ).sum()

    team_win_rate = (
        wins / len(completed) * 100
        if len(completed) > 0
        else 0
    )

    p1, p2, p3, p4 = st.columns(4)

    p1.metric("Matches Played", len(played))
    p2.metric("Wins", int(wins))
    p3.metric("Losses", int(losses))
    p4.metric("Win Percentage", f"{team_win_rate:.1f}%")

    performance = pd.DataFrame({
        "Result": ["Wins", "Losses", "No Result"],
        "Matches": [int(wins), int(losses), int(no_result)]
    })

    fig = px.bar(
        performance,
        x="Result",
        y="Matches",
        color="Result",
        text="Matches",
        title=f"{selected_team} - Performance Summary"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Select a specific team from the sidebar to view its performance.")

st.divider()

# ==========================================
# 11. TOSS ANALYSIS
# ==========================================
st.subheader("🪙 Toss Winner vs Match Winner")

toss_matches = filtered_matches[
    filtered_matches["toss_winner"].notna()
    & filtered_matches["winner"].notna()
    & (filtered_matches["result"] != "no result")
].copy()

if not toss_matches.empty:

    toss_matches["Toss and Match Won"] = (
        toss_matches["toss_winner"] == toss_matches["winner"]
    )

    toss_wins = int(toss_matches["Toss and Match Won"].sum())
    toss_total = len(toss_matches)

    toss_win_rate = (
        toss_wins / toss_total * 100
        if toss_total > 0
        else 0
    )

    t1, t2, t3 = st.columns(3)

    t1.metric("Completed Matches", toss_total)
    t2.metric("Toss + Match Won", toss_wins)
    t3.metric("Match Win Rate After Winning Toss", f"{toss_win_rate:.1f}%")

    toss_summary = pd.DataFrame({
        "Outcome": ["Won Toss & Match", "Won Toss, Lost Match"],
        "Matches": [
            toss_wins,
            toss_total - toss_wins
        ]
    })

    fig = px.bar(
        toss_summary,
        x="Outcome",
        y="Matches",
        color="Outcome",
        text="Matches",
        title="Did Winning the Toss Also Mean Winning the Match?"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No toss analysis data available for these filters.")

# ==========================================
# 12. FOOTER
# ==========================================
st.divider()
st.caption("IPL Cricket Data Analytics | Built with Python, Pandas, Plotly and Streamlit")
