
import streamlit as st
import pandas as pd
import plotly.express as px

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="건물 냉방 에너지 부하 예측",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 건물 냉방 에너지 부하 예측")
st.write(
    "건물의 구조적 특성을 이용하여 냉방 에너지 부하를 예측하는 웹앱입니다."
)

# 엑셀 파일 경로
DATA_FILE = Path(__file__).parent / "ENB2012-data.xlsx"

# 입력 데이터 열 이름
FEATURES = [
    "X1", "X2", "X3", "X4",
    "X5", "X6", "X7", "X8"
]

# 전체 데이터 열 이름
ALL_COLUMNS = FEATURES + ["Y1", "Y2"]

# 데이터 열의 한글 이름
DISPLAY_NAMES = {
    "X1": "상대적 밀집도 (X1)",
    "X2": "표면적 (X2)",
    "X3": "벽 면적 (X3)",
    "X4": "지붕 면적 (X4)",
    "X5": "건물 높이 (X5)",
    "X6": "건물 방향 코드 (X6)",
    "X7": "창문 면적 비율 (X7)",
    "X8": "창문 분포 코드 (X8)",
    "Y1": "난방 에너지 부하 (Y1)",
    "Y2": "냉방 에너지 부하 (Y2)"
}


# --------------------------------------------------
# 2. 엑셀 데이터 불러오기
# --------------------------------------------------

@st.cache_data
def load_data(file_mtime):

    # 엑셀 파일 읽기
    raw = pd.read_excel(DATA_FILE, engine="openpyxl")

    # 열 이름 확인
    normalized_columns = [
        str(col).strip().upper()
        for col in raw.columns
    ]

    # 엑셀에 열 이름이 이미 있는 경우
    if set(ALL_COLUMNS).issubset(set(normalized_columns)):

        raw.columns = normalized_columns
        df = raw[ALL_COLUMNS].copy()

    # 열 이름이 없는 엑셀 파일인 경우
    else:

        raw = pd.read_excel(
            DATA_FILE,
            header=None,
            engine="openpyxl"
        )

        if raw.shape[1] < len(ALL_COLUMNS):
            raise ValueError(
                "엑셀 파일에 필요한 데이터 열이 부족합니다."
            )

        raw = raw.iloc[:, :len(ALL_COLUMNS)].copy()

        # 첫 행이 열 이름인지 확인
        first_row = [
            str(value).strip().upper()
            for value in raw.iloc[0].tolist()
        ]

        if any(value in ALL_COLUMNS for value in first_row):
            raw = raw.iloc[1:].reset_index(drop=True)

        raw.columns = ALL_COLUMNS
        df = raw

    # 모든 데이터를 숫자형으로 변환
    for col in ALL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 필요한 데이터가 없는 행 제거
    df = df.dropna(
        subset=FEATURES + ["Y2"]
    ).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "사용할 수 있는 데이터가 없습니다. 엑셀 파일을 확인해 주세요."
        )

    return df


# 엑셀 파일 존재 여부 확인
if not DATA_FILE.exists():

    st.error("엑셀 파일을 찾을 수 없습니다.")

    st.info(
        "GitHub 저장소에 ENB2012-data.xlsx 파일을 "
        "app.py와 같은 위치에 올려 주세요."
    )

    st.stop()


# 엑셀 데이터 불러오기
try:

    file_mtime = DATA_FILE.stat().st_mtime
    df = load_data(file_mtime)

except Exception as e:

    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 3. 데이터 표 표시
# --------------------------------------------------

st.header("1. 건물 에너지 데이터")

st.write(
    "엑셀 파일에 저장된 건물의 구조적 특성과 "
    "에너지 부하 데이터를 확인할 수 있습니다."
)

st.metric(
    "전체 데이터 개수",
    f"{len(df)}개"
)

# 한글 열 이름으로 변경
display_df = df.rename(columns=DISPLAY_NAMES)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 4. 창문 면적 비율과 냉방 에너지 부하 그래프
# --------------------------------------------------

st.header("2. 창문 면적과 냉방 에너지 부하의 관계")

st.write(
    "창문 면적 비율이 달라질 때 냉방 에너지 부하가 "
    "어떻게 변하는지 확인합니다."
)

fig_window = px.scatter(
    df,
    x="X7",
    y="Y2",
    labels={
        "X7": "창문 면적 비율 (X7)",
        "Y2": "냉방 에너지 부하 (kWh/m²)"
    },
    title="창문 면적 비율과 냉방 에너지 부하"
)

fig_window.update_traces(
    marker=dict(size=7, opacity=0.65)
)

st.plotly_chart(
    fig_window,
    use_container_width=True
)

st.info(
    "이 그래프를 통해 창문 면적 비율에 따라 "
    "냉방 에너지 부하가 어떻게 달라지는지 살펴볼 수 있습니다."
)

st.caption(
    "참고: 데이터의 X7은 실제 창문 면적(m²)이 아니라 "
    "창문 면적 비율을 나타냅니다."
)


# --------------------------------------------------
# 5. 건물 높이와 냉방 에너지 부하 그래프
# --------------------------------------------------

st.header("3. 건물 높이와 냉방 에너지 부하의 관계")

st.write(
    "건물 높이에 따른 냉방 에너지 부하의 분포를 확인합니다."
)

# 건물 높이를 그룹으로 표시하기 위해 문자열로 변환
height_df = df.copy()

height_df["건물 높이"] = height_df["X5"].map(
    lambda value: f"{value:g}"
)

fig_height = px.box(
    height_df,
    x="건물 높이",
    y="Y2",
    points="all",
    labels={
        "건물 높이": "건물 높이 (X5)",
        "Y2": "냉방 에너지 부하 (kWh/m²)"
    },
    title="건물 높이별 냉방 에너지 부하"
)

st.plotly_chart(
    fig_height,
    use_container_width=True
)

st.info(
    "건물 높이별 냉방 에너지 부하의 분포와 "
    "차이를 비교할 수 있습니다."
)


# --------------------------------------------------
# 6. RandomForestRegressor 모델 학습
# --------------------------------------------------

@st.cache_resource
def train_model(file_mtime):

    # 입력 데이터와 정답 데이터 분리
    X = df[FEATURES]
    y = df["Y2"]

    # 학습 데이터 80%, 테스트 데이터 20%
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    # 랜덤 포레스트 회귀 모델 생성
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )

    # 모델 학습
    model.fit(X_train, y_train)

    # 테스트 데이터 예측
    predictions = model.predict(X_test)

    # 평균 절대 오차 계산
    mae = mean_absolute_error(
        y_test,
        predictions
    )

    return model, y_test, predictions, mae


# 모델 학습 및 평가
try:

    model, y_test, predictions, mae = train_model(file_mtime)

except Exception as e:

    st.error(f"모델 학습 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 7. 모델 평가 결과 표시
# --------------------------------------------------

st.header("4. Random Forest 냉방 에너지 부하 예측")

st.write(
    "RandomForestRegressor 모델을 이용하여 "
    "건물의 구조적 특성으로 냉방 에너지 부하를 예측합니다."
)

st.subheader("모델 평가 결과")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "평균 절대 오차 (MAE)",
        f"{mae:.2f} kWh/m²"
    )

with col2:

    st.metric(
        "테스트 데이터 개수",
        f"{len(y_test)}개"
    )

st.caption(
    "MAE는 학습에 사용하지 않은 테스트 데이터 20%에 대해 "
    "실제값과 예측값의 평균적인 차이를 계산한 값입니다. "
    "MAE가 낮을수록 예측 오차가 작습니다."
)


# 테스트 데이터의 실제값과 예측값 비교
result_df = pd.DataFrame({

    "실제 냉방 에너지 부하": y_test.to_numpy(),

    "예측 냉방 에너지 부하": predictions,

    "절대 오차": abs(
        y_test.to_numpy() - predictions
    )

})

st.subheader("실제값과 예측값 비교")

st.dataframe(
    result_df.round(2).head(15),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "위 표는 테스트 데이터 중 15개의 결과를 보여 줍니다."
)


# --------------------------------------------------
# 8. 사용자가 직접 건물 정보를 입력하여 예측하기
# --------------------------------------------------

st.header("5. 직접 입력하여 냉방 에너지 부하 예측하기")

st.write(
    "건물의 구조적 특성을 입력하면 "
    "AI 모델이 냉방 에너지 부하를 예측합니다."
)

st.info(
    "입력 가능한 범위는 엑셀 데이터에 있는 최솟값과 "
    "최댓값을 기준으로 설정됩니다."
)

with st.form("prediction_form"):

    col1, col2 = st.columns(2)

    with col1:

        x1 = st.number_input(
            "상대적 밀집도 (X1)",
            min_value=float(df["X1"].min()),
            max_value=float(df["X1"].max()),
            value=float(df["X1"].median()),
            step=0.01
        )

        x2 = st.number_input(
            "표면적 (X2)",
            min_value=float(df["X2"].min()),
            max_value=float(df["X2"].max()),
            value=float(df["X2"].median()),
            step=1.0
        )

        x3 = st.number_input(
            "벽 면적 (X3)",
            min_value=float(df["X3"].min()),
            max_value=float(df["X3"].max()),
            value=float(df["X3"].median()),
            step=1.0
        )

        x4 = st.number_input(
            "지붕 면적 (X4)",
            min_value=float(df["X4"].min()),
            max_value=float(df["X4"].max()),
            value=float(df["X4"].median()),
            step=1.0
        )

    with col2:

        x5 = st.number_input(
            "건물 높이 (X5)",
            min_value=float(df["X5"].min()),
            max_value=float(df["X5"].max()),
            value=float(df["X5"].median()),
            step=0.5
        )

        orientation_values = sorted(
            df["X6"].dropna().unique().tolist()
        )

        x6 = st.selectbox(
            "건물 방향 코드 (X6)",
            options=orientation_values
        )

        x7 = st.number_input(
            "창문 면적 비율 (X7)",
            min_value=float(df["X7"].min()),
            max_value=float(df["X7"].max()),
            value=float(df["X7"].median()),
            step=0.01
        )

        distribution_values = sorted(
            df["X8"].dropna().unique().tolist()
        )

        x8 = st.selectbox(
            "창문 분포 코드 (X8)",
            options=distribution_values
        )

    submitted = st.form_submit_button(
        "냉방 에너지 부하 예측하기"
    )


# 예측 버튼을 눌렀을 때 실행
if submitted:

    # 입력한 건물 정보 저장
    input_data = pd.DataFrame(
        [[x1, x2, x3, x4, x5, x6, x7, x8]],
        columns=FEATURES
    )

    # 냉방 에너지 부하 예측
    predicted_load = model.predict(input_data)[0]

    st.subheader("예측 결과")

    st.success("냉방 에너지 부하 예측이 완료되었습니다.")

    st.metric(
        "예측 냉방 에너지 부하",
        f"{predicted_load:.2f} kWh/m²"
    )

    st.write("입력한 건물 정보")

    st.dataframe(
        input_data.rename(columns=DISPLAY_NAMES),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 9. 마무리 안내
# --------------------------------------------------

st.divider()

st.caption(
    "본 웹앱은 ENB2012 건물 에너지 효율 데이터를 이용하여 "
    "RandomForestRegressor 모델로 냉방 에너지 부하를 예측합니다."
)
