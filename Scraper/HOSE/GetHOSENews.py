#fetch("https://api.hsx.vn/n/api/v1/1/news?pageIndex=1&pageSize=30&startDate=2025-09-02&endDate=2026-03-02&aliasCate=tin-tuc", {
#  "headers": {
#    "accept": "application/json, text/plain, */*",
#    "accept-language": "en-US,en;q=0.9",
#    "access-control-allow-origin": "*",
#    "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"",
#    "sec-ch-ua-mobile": "?0",
#    "sec-ch-ua-platform": "\"Windows\"",
#    "sec-fetch-dest": "empty",
#    "sec-fetch-mode": "cors",
#    "sec-fetch-site": "same-site",
#    "type": "HJ2HNS3SKICV4FNE"
#  },
#  "referrer": "https://www.hsx.vn/",
#  "body": null,
#  "method": "GET",
#  "mode": "cors",
#  "credentials": "omit"
#});

#fetch("https://api.hsx.vn/m/api/v1/1/mediafiles/1/2441167?pageIndex=1&pageSize=100&year=0", {
#  "headers": {
#    "accept": "application/json, text/plain, */*",
#    "accept-language": "en-US,en;q=0.9",
#    "access-control-allow-origin": "*",
#    "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Microsoft Edge\";v=\"145\", \"Chromium\";v=\"145\"",
#    "sec-ch-ua-mobile": "?0",
#    "sec-ch-ua-platform": "\"Windows\"",
#    "sec-fetch-dest": "empty",
#   "sec-fetch-mode": "cors",
#    "sec-fetch-site": "same-site",
#    "type": "HJ2HNS3SKICV4FNE"
#  },
#  "referrer": "https://www.hsx.vn/",
#  "body": null,
# "method": "GET",
#  "mode": "cors",
#  "credentials": "omit"
#});

#https://staticfile.hsx.vn/Uploads/UploadDocuments/2441234/20260227%20-%20FUEIP100%20-%20CBTT%20thay%20doi%20mau%20con%20dau%20Cong%20ty%20QLQ.pdf

import os
import requests
import io
import time
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from urllib.parse import quote, unquote
import pytesseract
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import re

# VADER Sentiment Analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

start_date = "2025-09-02"
end_date = datetime.now().strftime("%Y-%m-%d")
def fetch_hose_news(pageindex, start_date, end_date):
    url = f"https://api.hsx.vn/n/api/v1/1/news?pageIndex={pageindex}&pageSize=30&startDate={start_date}&endDate={end_date}&aliasCate=tin-tuc"
    try:
        response = requests.get(url)
        response.raise_for_status()
        respond_data = response.json()
        data = respond_data.get("data", {})
        news_list = data.get("list", []) if isinstance(data, dict) else []
        return news_list
    except requests.RequestException as e:
        raise ValueError(f"Error fetching news: {e}")

def fetch_media_page(news_id):
    url = f"https://api.hsx.vn/m/api/v1/1/mediafiles/1/{news_id}?pageIndex=1&pageSize=100&year=0"
    try:
        response = requests.get(url)
        response.raise_for_status()
        respond_data = response.json()
        new_page = respond_data.get("data", {})
        return new_page
    except requests.RequestException as e:
        raise ValueError(f"Error fetching media page: {e}")

def get_pdf_content(file, save_folder=r"C:\Users\Windows 11 Pro\Documents\Đồ án tốt nghiệp\PythonFinanceProject\sampledata\pdfs"):
    file_path = file.get("filePath")

    if not file_path:
        return None

    file_path = file_path.replace("~", "")
    folder, filename = file_path.rsplit("/", 1)
    encoded_filename = quote(filename)

    url = f"https://staticfile.hsx.vn{folder}/{encoded_filename}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        pdf_data = response.content

        os.makedirs(save_folder, exist_ok=True)
        local_filename = unquote(filename)
        save_path = os.path.join(save_folder, local_filename)

        if not os.path.exists(save_path):
            with open(save_path, "wb") as f:
                f.write(pdf_data)
            print(f"Saved: {local_filename}")
        else:
            print(f"Already exists: {local_filename}")

        return io.BytesIO(pdf_data)

    except requests.RequestException as e:
        print(f"Download error: {e}")
        return None

def extract_pdf_text(pdf_buffer):
    pdf_buffer.seek(0)

    reader = PdfReader(pdf_buffer)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted

    if len(text.strip()) < 50:
        print("Using OCR fallback (page by page)...")
        pdf_buffer.seek(0)

        images = convert_from_bytes(
            pdf_buffer.read(),
            dpi=300
        )

        text = ""
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang="vie")
            text += page_text + "\n"

    return text

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text

RISK_KEYWORDS = [
    "kiểm toán ngoại trừ",
    "ý kiến ngoại trừ",
    "điều chỉnh hồi tố",
    "phạt",
    "vi phạm",
    "truy thu",
    "sai sót",
    "lỗ lũy kế"
]

PRESSURE_KEYWORDS = [
    "thua lo", "khó khăn", "áp lực", "gấp rút", "khủng hoảng",
    "nợ đến hạn", "thiếu tiền", "giảm doanh thu", "giảm lợi nhuận",
    "mất thị trường", "cạnh tranh gay gắt", "chi phí tăng"
]

OPPORTUNITY_KEYWORDS = [
    "kiểm soát nội bộ yếu", "thiếu kiểm toán", "quản lý tài chính lỏng lẻo",
    "vắng mặt giám độc", "quy trình không rõ ràng", "giao dịch bất thường",
    "thay đổi chính sách kế toán", "quản lý kém"
]

def detect_risk_keywords(text):
    """Detect audit risk keywords"""
    found = []
    text_lower = text.lower()
    for kw in RISK_KEYWORDS:
        if kw in text_lower:
            found.append(kw)
    return found

def analyze_news_sentiment(title: str, content: str = "") -> Dict:
    """
    Analyze news sentiment using VADER for fraud pressure indicators
    
    Returns:
        Dictionary with sentiment scores and pressure indicators
    """
    analysis = {
        'title_sentiment': 0.0,
        'content_sentiment': 0.0,
        'combined_sentiment': 0.0,
        'is_negative': False,
        'pressure_signals': [],
        'opportunity_signals': [],
        'risk_level': 'LOW'
    }
    
    if not VADER_AVAILABLE:
        return analysis
    
    try:
        analyzer = SentimentIntensityAnalyzer()
        
        # Analyze title
        title_scores = analyzer.polarity_scores(title)
        analysis['title_sentiment'] = float(title_scores['compound'])
        
        # Analyze content
        if content:
            content_scores = analyzer.polarity_scores(content[:2000])  # First 2000 chars
            analysis['content_sentiment'] = float(content_scores['compound'])
        
        # Combined sentiment
        analysis['combined_sentiment'] = (analysis['title_sentiment'] + analysis['content_sentiment']) / 2
        
        # Check for pressure signals
        combined_text = (title + " " + content).lower()
        for signal in PRESSURE_KEYWORDS:
            if signal in combined_text:
                analysis['pressure_signals'].append(signal)
        
        for signal in OPPORTUNITY_KEYWORDS:
            if signal in combined_text:
                analysis['opportunity_signals'].append(signal)
        
        # Determine if negative (fraud pressure indicator)
        if analysis['combined_sentiment'] < -0.3:
            analysis['is_negative'] = True
        
        # Risk level based on signals
        signal_count = len(analysis['pressure_signals']) + len(analysis['opportunity_signals'])
        if signal_count >= 3:
            analysis['risk_level'] = 'HIGH'
        elif signal_count >= 1:
            analysis['risk_level'] = 'MEDIUM'
        
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
    
    return analysis

def extract_company_mentions(text: str) -> List[str]:
    """
    Extract company symbols/names mentioned in news for cross-reference
    
    Returns:
        List of potential stock symbols mentioned
    """
    # Match 3-4 letter uppercase sequences (typical Vietnamese stock symbols)
    symbols = re.findall(r'\b[A-Z]{3,4}\b', text)
    # Filter to likely symbols (remove common words)
    common_words = {'CÓ', 'NĂM', 'MỤC', 'VẫN', 'VIỆT', 'CÔNG', 'CÔNG', 'CÁC'}
    return list(set([s for s in symbols if s not in common_words]))

def get_company_news(ticker: str = None, days: int = 30) -> Dict:
    """
    Fetch and analyze latest HOSE news
    
    Args:
        ticker: Stock symbol (currently not used, kept for API compatibility)
        days: Number of days to look back
        
    Returns:
        Dictionary with news analysis data
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    result = {
        'ticker': ticker or 'HOSE_MARKET',
        'news_type': 'market_news',
        'news_count': 0,
        'average_sentiment': 0.0,
        'fraud_pressure_score': 0.0,
        'average_risk_level': 'LOW',
        'news_articles': [],
        'risk_signals': [],
        'status': 'pending'
    }
    
    try:
        # Fetch news
        news_list = fetch_hose_news(1, start_date, end_date)
        
        if not news_list:
            result['status'] = 'no_news'
            return result
        
        sentiments = []
        risk_scores = []
        risk_levels = []
        
        # Get latest 30 articles
        for news in news_list[:30]:
            try:
                title = news.get('title', '')
                content = news.get('content', '') or news.get('description', '')
                news_id = news.get('id', '')
                
                # Analyze sentiment
                sentiment_analysis = analyze_news_sentiment(title, content)
                sentiments.append(sentiment_analysis['combined_sentiment'])
                risk_levels.append(sentiment_analysis['risk_level'])
                
                # Try to fetch attachments/PDFs for this news
                attachments = []
                try:
                    if news_id:
                        media_page = fetch_media_page(news_id)
                        if media_page and isinstance(media_page, dict):
                            file_list = media_page.get('list', [])
                            if file_list:
                                for file_item in file_list[:3]:  # Limit to 3 PDFs per article
                                    file_path = file_item.get('filePath', '')
                                    file_name = file_item.get('fileName', 'document.pdf')
                                    if file_path and file_path.endswith('.pdf'):
                                        attachments.append({
                                            'name': file_name,
                                            'path': file_path,
                                            'url': f"https://staticfile.hsx.vn{file_path.replace('~', '')}"
                                        })
                except Exception as e:
                    print(f"Could not fetch attachments for news {news_id}: {str(e)}")
                
                article_data = {
                    'date': news.get('createdDate', ''),
                    'title': title,
                    'content': content[:200] if content else '',
                    'sentiment': sentiment_analysis['combined_sentiment'],
                    'pressure_signals': sentiment_analysis['pressure_signals'],
                    'opportunity_signals': sentiment_analysis['opportunity_signals'],
                    'risk_level': sentiment_analysis['risk_level'],
                    'attachments': attachments
                }
                
                result['news_articles'].append(article_data)
                
                # Accumulate risk signals
                if sentiment_analysis['pressure_signals']:
                    result['risk_signals'].extend(sentiment_analysis['pressure_signals'])
                if sentiment_analysis['opportunity_signals']:
                    result['risk_signals'].extend(sentiment_analysis['opportunity_signals'])
                
                # Score: negative sentiment = higher fraud pressure
                if sentiment_analysis['combined_sentiment'] < -0.3:
                    risk_scores.append(0.8)
                elif sentiment_analysis['combined_sentiment'] < 0:
                    risk_scores.append(0.5)
                else:
                    risk_scores.append(0.2)
                
            except Exception as e:
                print(f"Error processing news article: {str(e)}")
                continue
        
        result['news_count'] = len(result['news_articles'])
        
        if sentiments:
            result['average_sentiment'] = float(np.mean(sentiments))
        
        if risk_scores:
            result['fraud_pressure_score'] = float(np.mean(risk_scores))
        
        # Determine overall risk level
        if risk_levels:
            high_count = risk_levels.count('HIGH')
            medium_count = risk_levels.count('MEDIUM')
            if high_count > len(risk_levels) * 0.3:
                result['average_risk_level'] = 'HIGH'
            elif medium_count > len(risk_levels) * 0.3:
                result['average_risk_level'] = 'MEDIUM'
            else:
                result['average_risk_level'] = 'LOW'
        
        result['status'] = 'success'
        
    except Exception as e:
        result['status'] = f"error: {str(e)}"
    
    return result