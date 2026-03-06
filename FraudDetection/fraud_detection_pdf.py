import pdfplumber
import re
import numpy as np
from typing import Dict, List, Tuple
from io import BytesIO

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

FRAUD_KEYWORDS = [
    'gian lan', 'thao tung', 'bat thuong', 'can tho', 'chinh sua',
    'dieu chinh', 'phan loai lai', 'yeu kem', 'bat an', 'kho khan',
    'lo lang', 'tai chinh khong on dinh', 'thua lo', 'chi tieu',
    'bao cao sai', 'su co', 'khong chinh xac', 'lui day', 'canh bao',
    'khong hop le', 'vi pham', 'sai pham'
]

POSITIVE_KEYWORDS = [
    'tang truong', 'tang', 'manh me', 'tien bo', 'tich cuc', 'vung chac',
    'phat trien', 'cao', 'tot', 'dung dam'
]

# Fraud Triangle Indicators
PRESSURE_INDICATORS = {
    'financial_distress': [
        'thua lo', 'khó khăn tài chính', 'nợ cao', 'giảm doanh thu',
        'tỷ suất lợi nhuận thấp', 'nợ đến hạn', 'thiếu tiền mặt',
        'không thanh toán được', 'khủng hoảng'
    ],
    'personal_pressure': [
        'cấp bậc thấp', 'mức lương thấp', 'vợ chồng ly dị', 'chi tiêu cao',
        'vay mượn nhiều', 'tài chính cá nhân khó khăn'
    ],
    'external_pressure': [
        'cạnh tranh gay gắt', 'thị trường sụt giảm', 'kỳ vọng cao',
        'lợi nhuận bằng bất kỳ giá nào', 'sức ép từ quản lý'
    ]
}

OPPORTUNITY_INDICATORS = {
    'weak_controls': [
        'kiểm soát nội bộ yếu', 'thiếu giám sát', 'vắng mặt chuyên gia kế toán',
        'không có kiểm toán độc lập', 'quy trình phê duyệt không rõ ràng'
    ],
    'poor_oversight': [
        'hội đồng quản lý yếu', 'thiếu chuyên môn', 'xung đột lợi ích',
        'quản lý cũ, không thay đổi', 'giám sát không hiệu quả'
    ],
    'complex_transactions': [
        'giao dịch phức tạp', 'công ty con quá nhiều', 'khu vực off-shore',
        'thay đổi chính sách kế toán', 'nhân viên IT thiếu'
    ]
}

RATIONALIZATION_INDICATORS = [
    'tạm thời', 'sẽ điều chỉnh lại', 'mọi công ty đều làm vậy',
    'kế toán viên không hiểu', 'chúng tôi không biết', 'đây là cách chuẩn',
    'bạn nên tin tưởng chúng tôi', 'không ai biết được'
]

CAPABILITY_INDICATORS = {
    'executive_position': ['ceo', 'cfo', 'giám đốc tài chính', 'chủ tịch hội đồng'],
    'technical_skills': ['lập trình', 'công nghệ', 'hệ thống', 'it', 'database'],
    'prior_violations': ['phạt trước', 'vi phạm trước', 'cảnh cáo trước'],
    'manipulative_behavior': ['thao túng', 'bóp méo', 'giấu diếu', 'gian dối']
}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        text = ""
        pdf_file = BytesIO(pdf_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {str(e)}")
        return ""

def extract_numbers(text: str) -> List[float]:
    try:
        numbers = re.findall(r"\d+\.?\d*(?:[Ee][+-]?\d+)?", text)
        return [float(n) for n in numbers]
    except Exception as e:
        print(f"Error extracting numbers: {str(e)}")
        return []

def analyze_fraud_triangle(text: str) -> Dict[str, float]:
    text_lower = text.lower()
    
    triangle_scores = {
        'pressure': 0.0,
        'opportunity': 0.0,
        'rationalization': 0.0,
        'fraud_triangle_risk': 0.0,
        'details': {}
    }
    
    # Score PRESSURE (financial distress + personal pressure)
    pressure_count = 0
    found_pressures = []
    for category, keywords in PRESSURE_INDICATORS.items():
        for keyword in keywords:
            if keyword in text_lower:
                pressure_count += 1
                found_pressures.append(keyword)
    
    triangle_scores['pressure'] = min(1.0, pressure_count * 0.15)
    triangle_scores['details']['pressure_signals'] = found_pressures
    
    # Score OPPORTUNITY (weak controls, poor oversight)
    opportunity_count = 0
    found_opportunities = []
    for category, keywords in OPPORTUNITY_INDICATORS.items():
        for keyword in keywords:
            if keyword in text_lower:
                opportunity_count += 1
                found_opportunities.append(keyword)
    
    triangle_scores['opportunity'] = min(1.0, opportunity_count * 0.15)
    triangle_scores['details']['opportunity_signals'] = found_opportunities
    
    # Score RATIONALIZATION (self-justifying language)
    rationalization_count = 0
    found_rationalizations = []
    for keyword in RATIONALIZATION_INDICATORS:
        if keyword in text_lower:
            rationalization_count += 1
            found_rationalizations.append(keyword)
    
    triangle_scores['rationalization'] = min(1.0, rationalization_count * 0.25)
    triangle_scores['details']['rationalization_signals'] = found_rationalizations
    
    # Overall fraud triangle risk (all three must be present for high risk)
    if (triangle_scores['pressure'] > 0.3 and 
        triangle_scores['opportunity'] > 0.3 and 
        triangle_scores['rationalization'] > 0.2):
        triangle_scores['fraud_triangle_risk'] = 0.85
    elif (triangle_scores['pressure'] > 0.2 and 
            triangle_scores['opportunity'] > 0.2):
        triangle_scores['fraud_triangle_risk'] = 0.6
    else:
        triangle_scores['fraud_triangle_risk'] = min(1.0, 
            (triangle_scores['pressure'] + triangle_scores['opportunity'] 
            + triangle_scores['rationalization']) / 3)
    
    return triangle_scores

def analyze_fraud_diamond(text: str) -> Dict[str, float]:
    # Get triangle scores first
    diamond_scores = analyze_fraud_triangle(text)
    
    text_lower = text.lower()
    
    # Score CAPABILITY (ability to carry out fraud)
    capability_score = 0.0
    found_capabilities = []
    
    # Executive capability
    for keyword in CAPABILITY_INDICATORS['executive_position']:
        if keyword in text_lower:
            capability_score += 0.2
            found_capabilities.append(f"Executive: {keyword}")
    
    # Technical capability
    for keyword in CAPABILITY_INDICATORS['technical_skills']:
        if keyword in text_lower:
            capability_score += 0.15
            found_capabilities.append(f"Technical: {keyword}")
    
    # Prior violations
    for keyword in CAPABILITY_INDICATORS['prior_violations']:
        if keyword in text_lower:
            capability_score += 0.25
            found_capabilities.append(f"Prior violation: {keyword}")
    
    # Manipulative behavior patterns
    for keyword in CAPABILITY_INDICATORS['manipulative_behavior']:
        if keyword in text_lower:
            capability_score += 0.2
            found_capabilities.append(f"Manipulation: {keyword}")
    
    diamond_scores['capability'] = min(1.0, capability_score)
    diamond_scores['details']['capability_signals'] = found_capabilities
    
    # Update overall risk with capability factor
    if (diamond_scores['pressure'] > 0.3 and 
        diamond_scores['opportunity'] > 0.3 and 
        diamond_scores['rationalization'] > 0.2 and
        diamond_scores['capability'] > 0.2):
        diamond_scores['fraud_diamond_risk'] = 0.92  # All four elements = highest risk
    else:
        diamond_scores['fraud_diamond_risk'] = min(1.0, diamond_scores['fraud_triangle_risk'] * (1 + diamond_scores['capability'] * 0.5))
    
    return diamond_scores

def analyze_financial_metrics(numbers: List[float]) -> Dict[str, float]:
    if not numbers:
        return {"error": "No numbers found"}
    
    indicators = {}
    
    # Check for unusual patterns
    indicators['number_of_values'] = len(numbers)
    indicators['has_extreme_values'] = any(n > 1e10 for n in numbers)
    indicators['has_zero_values'] = sum(1 for n in numbers if n == 0)
    indicators['sum_to_zero'] = sum(numbers) == 0
    
    # Check for suspiciously round numbers (sign of manipulation)
    round_numbers = sum(1 for n in numbers if n == int(n) and len(str(int(n))) >= 6)
    indicators['suspiciously_round'] = round_numbers / len(numbers) if numbers else 0
    
    # Check for unusual variance
    if len(numbers) > 1:
        indicators['variance'] = float(np.var(numbers))
        indicators['std_dev'] = float(np.std(numbers))
    
    return indicators

def analyze_text_for_fraud(text: str) -> Dict[str, any]:
    text_lower = text.lower()
    
    analysis = {
        'fraud_keywords_count': 0,
        'fraud_keywords': [],
        'positive_keywords_count': 0,
        'keyword_ratio': 0.0,
        'suspicious': False
    }
    
    # Count fraud keywords
    for keyword in FRAUD_KEYWORDS:
        count = len(re.findall(rf'\b{keyword}\b', text_lower))
        if count > 0:
            analysis['fraud_keywords_count'] += count
            analysis['fraud_keywords'].append(keyword)
    
    # Count positive keywords
    for keyword in POSITIVE_KEYWORDS:
        count = len(re.findall(rf'\b{keyword}\b', text_lower))
        analysis['positive_keywords_count'] += count
    
    # Calculate keyword ratio
    total_words = len(text.split())
    if total_words > 0:
        analysis['keyword_ratio'] = analysis['fraud_keywords_count'] / total_words
    
    # Determine if suspicious
    analysis['suspicious'] = analysis['fraud_keywords_count'] > 5 or analysis['keyword_ratio'] > 0.01
    
    # Sentiment analysis if available
    if VADER_AVAILABLE:
        try:
            analyzer = SentimentIntensityAnalyzer()
            sentiment = analyzer.polarity_scores(text[:1000])  # Analyze first 1000 chars
            analysis['sentiment'] = float(sentiment['compound'])
            analysis['tone_suspicious'] = sentiment['compound'] < -0.3
        except:
            pass
    
    return analysis

def detect_fraud_pdf(pdf_bytes: bytes) -> Dict:
    try:
        results = {
            "fraud_probability": 0.0,
            "fraud_diamond_probability": 0.0,
            "fraud_risk_level": "LOW",
            "risk_factors": {
                "fraud_triangle": {},
                "fraud_diamond": {},
                "financial_metrics": {},
                "text_analysis": {}
            },
            "extracted_text": "",
            "status": "success"
        }
        
        # Extract text
        extracted_text = extract_text_from_pdf(pdf_bytes)
        results['extracted_text'] = extracted_text[:500]  # First 500 chars for display
        
        if not extracted_text:
            results['fraud_probability'] = 0.1
            results['fraud_diamond_probability'] = 0.1
            results['status'] = 'warning'
            return results
        
        # 1. FRAUD TRIANGLE ANALYSIS
        triangle_analysis = analyze_fraud_triangle(extracted_text)
        results['risk_factors']['fraud_triangle'] = triangle_analysis
        
        # 2. FRAUD DIAMOND ANALYSIS (includes triangle + capability)
        diamond_analysis = analyze_fraud_diamond(extracted_text)
        results['risk_factors']['fraud_diamond'] = diamond_analysis
        
        # 3. Extract and analyze numbers
        numbers = extract_numbers(extracted_text)
        financial_metrics = analyze_financial_metrics(numbers)
        results['risk_factors']['financial_metrics'] = financial_metrics
        
        # 4. Analyze text for fraud keywords
        text_analysis = analyze_text_for_fraud(extracted_text)
        results['risk_factors']['text_analysis'] = text_analysis
        
        # ===== CALCULATE COMPREHENSIVE FRAUD RISK =====
        
        # METHOD 1: Traditional Scoring (Keyword-based)
        fraud_score_traditional = 0
        max_score = 0
        
        # Score 1: Financial metrics (0-30 points)
        if financial_metrics.get('has_extreme_values'):
            fraud_score_traditional += 10
        max_score += 10
        
        if financial_metrics.get('suspiciously_round', 0) > 0.3:
            fraud_score_traditional += 10
        max_score += 10
        
        if financial_metrics.get('sum_to_zero'):
            fraud_score_traditional += 10
        max_score += 10
        
        # Score 2: Fraud keywords (0-40 points)
        keyword_count = text_analysis.get('fraud_keywords_count', 0)
        fraud_score_traditional += min(40, keyword_count * 5)
        max_score += 40
        
        # Score 3: Keyword ratio (0-20 points)
        keyword_ratio = text_analysis.get('keyword_ratio', 0)
        fraud_score_traditional += min(20, keyword_ratio * 200)
        max_score += 20
        
        # Score 4: Sentiment (0-10 points)
        if text_analysis.get('tone_suspicious', False):
            fraud_score_traditional += 10
        max_score += 10
        
        # Normalize traditional method
        fraud_probability_traditional = fraud_score_traditional / max_score if max_score > 0 else 0
        
        # METHOD 2: Fraud Triangle + Diamond Integrated
        # Weight: 60% Diamond (advanced), 40% Traditional (keyword-based)
        fraud_probability_diamond = diamond_analysis.get('fraud_diamond_risk', 0.5)
        fraud_probability_triangle = triangle_analysis.get('fraud_triangle_risk', 0.5)
        
        # Combine methods: Triangle 30%, Diamond 40%, Traditional 30%
        results['fraud_probability'] = (
            fraud_probability_traditional * 0.3 +
            fraud_probability_triangle * 0.3 +
            fraud_probability_diamond * 0.4
        )
        
        results['fraud_diamond_probability'] = fraud_probability_diamond
        
        # Determine comprehensive risk level
        if results['fraud_diamond_probability'] > 0.75:
            results['fraud_risk_level'] = 'CRITICAL'  # All four diamond elements present
        elif results['fraud_probability'] > 0.7:
            results['fraud_risk_level'] = 'HIGH'
        elif results['fraud_probability'] > 0.4:
            results['fraud_risk_level'] = 'MEDIUM'
        else:
            results['fraud_risk_level'] = 'LOW'
        
        return results
        
    except Exception as e:
        return {
            "error": str(e),
            "fraud_probability": 0.0,
            "fraud_diamond_probability": 0.0,
            "status": "error"
        }

def detect_comprehensive_fraud(pdf_bytes: bytes, ticker: str = None, news_data: Dict = None) -> Dict:
    # Start with PDF-based analysis
    pdf_results = detect_fraud_pdf(pdf_bytes)
    
    comprehensive_results = {
        "pdf_fraud_analysis": pdf_results,
        "news_fraud_analysis": None,
        "combined_fraud_risk": pdf_results['fraud_probability'],
        "overall_risk_level": pdf_results['fraud_risk_level'],
        "risk_components": {
            "pdf_risk": pdf_results['fraud_probability'],
            "news_risk": 0.0,
            "combined_risk": 0.0
        },
        "fraud_indicators_summary": {
            "pressure": 0.0,
            "opportunity": 0.0,
            "rationalization": 0.0,
            "capability": 0.0
        },
        "status": "partial"  # Partial if only PDF analyzed
    }
    
    # Extract triangle/diamond components from PDF analysis
    triangle_data = pdf_results['risk_factors'].get('fraud_triangle', {})
    diamond_data = pdf_results['risk_factors'].get('fraud_diamond', {})
    
    comprehensive_results['fraud_indicators_summary']['pressure'] = triangle_data.get('pressure', 0.0)
    comprehensive_results['fraud_indicators_summary']['opportunity'] = triangle_data.get('opportunity', 0.0)
    comprehensive_results['fraud_indicators_summary']['rationalization'] = triangle_data.get('rationalization', 0.0)
    comprehensive_results['fraud_indicators_summary']['capability'] = diamond_data.get('capability', 0.0)
    
    # Add news analysis if available
    if news_data:
        comprehensive_results['news_fraud_analysis'] = news_data
        
        # Integrate news pressure score
        news_pressure = news_data.get('fraud_pressure_score', 0.0)
        news_sentiment = news_data.get('average_sentiment', 0.0)
        
        # Negative news = higher fraud pressure indicator
        news_fraud_risk = news_pressure * 0.7 + (1 - (news_sentiment + 1) / 2) * 0.3
        comprehensive_results['risk_components']['news_risk'] = news_fraud_risk
        
        # Combine: PDF fraud analysis (60%) + News pressure (40%)
        combined_risk = (
            pdf_results['fraud_diamond_probability'] * 0.6 +
            news_fraud_risk * 0.4
        )
        comprehensive_results['combined_fraud_risk'] = combined_risk
        comprehensive_results['risk_components']['combined_risk'] = combined_risk
        comprehensive_results['status'] = 'complete'
        
        # Update overall risk level based on combined assessment
        if combined_risk > 0.8:
            comprehensive_results['overall_risk_level'] = 'CRITICAL'
        elif combined_risk > 0.7:
            comprehensive_results['overall_risk_level'] = 'HIGH'
        elif combined_risk > 0.4:
            comprehensive_results['overall_risk_level'] = 'MEDIUM'
        else:
            comprehensive_results['overall_risk_level'] = 'LOW'
    
    return comprehensive_results