import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import re 

# goldkimp.com URL 및 헤더
BASE_URL = "https://goldkimp.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# 데이터에서 숫자만 추출하는 헬퍼 함수
def extract_float(tag, label="Data"):
    """태그에서 쉼표나 기타 문자를 제거하고 float 형태로 숫자를 추출합니다."""
    if not tag:
        print(f"❌ {label} 태그를 찾을 수 없습니다.")
        return None
    
    # 텍스트를 정리하고 숫자, 소수점, 쉼표가 포함된 문자열을 검색
    text = tag.text.strip()
    match = re.search(r'[\d.,]+', text)
    
    if match:
        try:
            # 쉼표를 제거하고 float으로 변환
            return float(match.group(0).replace(',', ''))
        except ValueError:
            print(f"❌ {label} 추출된 값 '{match.group(0)}'을 숫자로 변환할 수 없습니다.")
            return None
    else:
        print(f"❌ {label} 데이터 '{text}'에서 숫자를 추출하지 못했습니다.")
        return None

# 1. goldkimp.com에서 모든 데이터를 한 번에 스크래핑
def get_goldkimp_data():
    try:
        res = requests.get(BASE_URL, headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # --- 사용자 제공 ID 선택자 적용 ---
        domestic_tag = soup.select_one("#krx-price")      # 국내 금 시세 (KRW)
        international_krw_tag = soup.select_one("#xau-price-krw") # 국제 금 시세 (원화 환산)
        usd_krw_tag = soup.select_one("#exchange-rate")    # 환율 (USD/KRW)
        gap_rate_tag = soup.select_one("#premium-pct")     # 괴리율 (%)

        
        # 참고: #xau-price-krw는 국제 금 시세의 원화 환산 가격이므로,
        # 국제 금 시세(USD) 대신 이 값을 바로 사용합니다.
        
        domestic = extract_float(domestic_tag, "국내 금 시세")
        international_krw = extract_float(international_krw_tag, "국제 금 시세(원화)")
        usd_krw = extract_float(usd_krw_tag, "환율")
        gap_rate = extract_float(gap_rate_tag, "괴리율")

        # 국제 금 시세 (USD)는 #xau-price-krw가 원화 환산 가격이므로, 
        # 메일 내용의 일관성을 위해 역산하거나, 원화 환산 가격을 국제 시세로 간주합니다.
        # 여기서는 메일 내용에 필요한 원화 기준 국제 시세를 그대로 사용하고, 
        # 국제 금 시세(USD)는 출력하지 않습니다.
        
        return domestic, international_krw, usd_krw, gap_rate

    except requests.RequestException as e:
        print(f"❌ 웹페이지 요청 실패: {e}")
        # 실패 시 4개의 None을 반환하여 이후 단계에서 오류를 발생시킴
        return None, None, None, None
    except Exception as e:
        print(f"❌ 데이터 처리 중 예상치 못한 오류 발생: {e}")
        return None, None, None, None


# 2. 계산 및 출력 (goldkimp.com 데이터 사용)
def calculate_and_report_gap():
    # goldkimp.com에서 국내/국제 시세(원화), 환율, 괴리율을 직접 가져옴
    domestic, international_krw, usd_krw, gap_rate_scraped = get_goldkimp_data()
    
    if None in [domestic, international_krw, usd_krw, gap_rate_scraped]:
        raise ValueError("❌ 시세 스크래핑 실패. 일부 값이 누락되었습니다.")

    # 괴리율은 이미 스크래핑되었으므로 재계산 불필요
    
    print(f"✅ Domestic Gold (KRW): {domestic:,.2f}")
    print(f"✅ International Gold (KRW): {international_krw:,.2f} (원화 환산)")
    print(f"✅ USD/KRW Rate: {usd_krw:,.2f}")
    print(f"✅ Gap Rate (Scraped): {gap_rate_scraped:.2f} %")

    # 국제 금 시세(원화 환산)를 international 변수로 반환
    return domestic, international_krw, usd_krw, gap_rate_scraped


# 3. 이메일 발송 (출처 및 내용 수정)
def send_email(domestic, international, usd_krw, gap_rate):
    # 환경 변수가 설정되어 있어야 합니다.
    Gold_Email_sender = os.environ.get("Gold_Email_sender")
    Gold_Email_receiver = os.environ.get("Gold_Email_receiver")
    password = os.environ.get("password")  

    if not all([Gold_Email_sender, Gold_Email_receiver, password]):
        print("❌ 환경 변수(Gold_Email_sender, Gold_Email_receiver, password)를 설정해야 합니다.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"[금 시세 알림 - GoldKimp] {now}"
    body = f"""
    📊 금 시세 알림 ({now})

    국내 금 시세 : {domestic:,.2f} 원
    국제 금 시세 (원화 환산) : {international:,.2f} 원
    현재 환율 (USD/KRW) : {usd_krw:,.2f} 원
    괴리율 : {gap_rate:.2f} %

    """
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = Gold_Email_sender
    msg["To"] = Gold_Email_receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(Gold_Email_sender, password)
            smtp.send_message(msg)
        print("✅ 이메일 전송 완료")
    except Exception as e:
        print(f"❌ 이메일 전송 실패. (환경변수 또는 Gmail 앱 비밀번호 확인 필요): {e}")


# 4. 실행
if __name__ == "__main__":
    try:
        domestic, international, usd_krw, gap_rate = calculate_and_report_gap()
        
        print("\n--- 최종 결과 ---")
        print(f"국내 금 시세: {domestic:,.2f} 원")
        print(f"국제 금 시세 (원화 환산): {international:,.2f} 원")
        print(f"환율 (USD/KRW): {usd_krw:,.2f} 원")
        print(f"괴리율: {gap_rate:.2f} %")

        send_email(domestic, international, usd_krw, gap_rate)
        
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"실행 중 치명적인 오류 발생: {e}")
