# gold_email_alert.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 네이버 금융에서 국내 금 시세 가져오기
def get_domestic_gold_price():
    url = "https://finance.naver.com/marketindex/goldDetail.naver?marketindexCd=CMDT_GLDKRW"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    price_tag = soup.select_one("p.no_today span.blind")
    if price_tag:
        domestic_price = float(price_tag.text.replace(",", ""))
        return domestic_price
    else:
        raise ValueError("국내 금 시세를 찾을 수 없습니다.")

# 2. 네이버 금융에서 국제 금 시세 (달러 기준) 가져오기
def get_international_gold_price():
    url = "https://finance.naver.com/marketindex/worldGoldDetail.naver?marketindexCd=CMDT_GLD"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    price_tag = soup.select_one("p.no_today span.blind")
    if price_tag:
        international_price = float(price_tag.text.replace(",", ""))
        return international_price
    else:
        raise ValueError("국제 금 시세를 찾을 수 없습니다.")

# ========== [3] 환율 정보 가져오기 ==========
def get_usd_krw_rate():
    url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    rate_tag = soup.select_one("p.no_today span.blind")
    if rate_tag:
        usd_krw = float(rate_tag.text.replace(",", ""))
        return usd_krw
    else:
        raise ValueError("환율 정보를 찾을 수 없습니다.")

# ========== [4] 계산 ==========
def calculate_gap():
    domestic = get_domestic_gold_price()         # 원화 단위
    international_usd = get_international_gold_price()  # 달러 단위
    usd_krw = get_usd_krw_rate()                # 환율 (KRW/USD)

    # 국제 금 시세를 원화로 변환
    international_krw = international_usd * usd_krw

    # 괴리율 계산
    gap_rate = ((domestic - international_krw) / international_krw) * 100

    return domestic, international_krw, usd_krw, gap_rate

# ========== [5] 이메일 전송 ==========
def send_email(domestic, international, usd_krw, gap_rate):
    Gold_Email_sender = 
    Gold_Email_receiver = 
    password =   # Gmail 앱 비밀번호 사용

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"[금 시세 알림] {now}"
    body = f"""
    📊 금 시세 알림 ({now})

    국내 금 시세 : {domestic:,.2f} 원
    국제 금 시세 (원화 환산) : {international:,.2f} 원
    현재 환율 (USD/KRW) : {usd_krw:,.2f} 원
    괴리율 : {gap_rate:.2f} %

    - 데이터 출처 : 네이버 금융
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = Gold_Email_sender
    msg["To"] = Gold_Email_receiver

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(Gold_Email_sender, password)
        smtp.send_message(msg)

    print("✅ 이메일 전송 완료")

# ========== [6] 메인 실행 ==========
if __name__ == "__main__":
    domestic, international, usd_krw, gap_rate = calculate_gap()
    print(f"국내 금 시세: {domestic:,.2f} 원")
    print(f"국제 금 시세 (원화 환산): {international:,.2f} 원")
    print(f"환율 (USD/KRW): {usd_krw:,.2f} 원")
    print(f"괴리율: {gap_rate:.2f} %")

    # 이메일 전송
    send_email(domestic, international, usd_krw, gap_rate)
