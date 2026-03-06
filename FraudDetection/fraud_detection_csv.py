import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def calculate_beneish_m_score(df: pd.DataFrame) -> Dict[str, float]:
    try:
        required_cols = ['revenue', 'receivables', 'inventory', 'depreciation', 
                        'sga', 'assets', 'current_assets', 'cogs']
        
        # Check if required columns exist (case-insensitive)
        df_cols = {col.lower(): col for col in df.columns}
        available_cols = {req: df_cols.get(req.lower()) for req in required_cols}
        
        if None in available_cols.values():
            return {"m_score": 0, "indicators": {}, "error": "Missing required financial data"}
        
        # Extract required columns
        revenue = df[available_cols['revenue']].astype(float)
        receivables = df[available_cols['receivables']].astype(float)
        inventory = df[available_cols['inventory']].astype(float)
        depreciation = df[available_cols['depreciation']].astype(float)
        sga = df[available_cols['sga']].astype(float)
        assets = df[available_cols['assets']].astype(float)
        cogs = df[available_cols['cogs']].astype(float)
        
        # Calculate M-Score components
        # 1. DSI - Days Sales in Receivables Index
        receivables_pct = receivables / revenue
        dsi = receivables_pct.iloc[-1] / receivables_pct.iloc[0] if len(receivables_pct) > 1 else 1.0
        
        # 2. GMI - Gross Margin Index
        gm = (revenue - cogs) / revenue
        gmi = gm.iloc[0] / gm.iloc[-1] if len(gm) > 1 and gm.iloc[-1] != 0 else 1.0
        
        # 3. AQI - Asset Quality Index
        noncurrent_assets = assets - df[available_cols['current_assets']].astype(float)
        aqi = (1 - (df[available_cols['current_assets']].astype(float) + noncurrent_assets) / assets).iloc[-1]
        aqi = max(0, aqi)
        
        # 4. SGI - Sales Growth Index
        sgi = revenue.iloc[-1] / revenue.iloc[0] if len(revenue) > 1 else 1.0
        
        # 5. DEPI - Depreciation Index
        depi = depreciation.iloc[0] / (depreciation.iloc[0] + cogs.iloc[0]) if len(depreciation) > 1 else 1.0
        
        # 6. SGAI - SG&A Index
        sgai = sga.iloc[-1] / sga.iloc[0] if len(sga) > 1 else 1.0
        
        # Calculate M-Score
        m_score = (-4.404 + 
                  (-0.920 * dsi) + 
                  (0.528 * gmi) + 
                  (-0.404 * aqi) + 
                  (0.892 * sgi) +
                  (-0.080 * depi) +
                  (-0.061 * sgai))
        
        return {
            "m_score": float(m_score),
            "fraud_threshold": -1.46,
            "is_fraud": float(m_score) > -1.46,
            "confidence": min(1.0, abs(m_score + 1.46) / 3.0),
            "indicators": {
                "dsi": float(dsi),
                "gmi": float(gmi),
                "aqi": float(aqi),
                "sgi": float(sgi),
                "depi": float(depi),
                "sgai": float(sgai)
            }
        }
    except Exception as e:
        return {"m_score": 0, "error": str(e), "indicators": {}}

def detect_anomalies(df: pd.DataFrame) -> Dict[str, any]:
    try:
        anomalies = {}
        
        # Check for unusual revenue growth
        if 'revenue' in df.columns:
            revenue = pd.to_numeric(df['revenue'], errors='coerce')
            growth = revenue.pct_change()
            anomalies['unusual_revenue_growth'] = growth.abs().max() > 1.0  # >100% growth
            anomalies['revenue_volatility'] = float(growth.std())
        
        # Check for unusual expense ratios
        if 'expenses' in df.columns and 'revenue' in df.columns:
            expense_ratio = pd.to_numeric(df['expenses'], errors='coerce') / pd.to_numeric(df['revenue'], errors='coerce')
            anomalies['unusual_expense_ratio'] = (expense_ratio > 0.9).any()  # >90% expenses
            anomalies['expense_ratio_mean'] = float(expense_ratio.mean())
        
        return anomalies
    except Exception as e:
        return {"error": str(e)}

def detect_fraud_csv(df: pd.DataFrame) -> Dict:
    try:
        results = {
            "fraud_probability": 0.0,
            "indicators": {},
            "anomalies": {},
            "total_records": len(df)
        }
        
        # Calculate Beneish M-Score if suitable data exists
        if len(df) > 0:
            m_score_result = calculate_beneish_m_score(df)
            results['m_score'] = m_score_result.get('m_score', 0)
            results['indicators'].update(m_score_result.get('indicators', {}))
            results['is_fraud_m_score'] = m_score_result.get('is_fraud', False)
        
        # Detect anomalies
        anomalies = detect_anomalies(df)
        results['anomalies'] = anomalies
        
        # Calculate overall fraud probability
        fraud_signals = 0
        total_signals = 2
        
        if results.get('is_fraud_m_score', False):
            fraud_signals += 1
        
        if anomalies.get('unusual_revenue_growth', False):
            fraud_signals += 0.5
        
        results['fraud_probability'] = fraud_signals / total_signals
        results['fraud_risk_level'] = 'HIGH' if results['fraud_probability'] > 0.6 else 'MEDIUM' if results['fraud_probability'] > 0.3 else 'LOW'
        results['status'] = 'success'
        
        return results
        
    except Exception as e:
        return {
            "error": str(e),
            "fraud_probability": 0.0,
            "indicators": {},
            "status": "error"
        }

# Test function
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'revenue': [1000, 1100, 1050, 1200, 1300],
        'receivables': [200, 250, 300, 350, 400],
        'inventory': [100, 110, 120, 130, 140],
        'depreciation': [50, 50, 50, 50, 50],
        'sga': [200, 210, 220, 230, 240],
        'assets': [2000, 2100, 2200, 2300, 2400],
        'current_assets': [600, 650, 700, 750, 800],
        'cogs': [600, 660, 630, 720, 780]
    })
    
    result = detect_fraud_csv(sample_data)
    print("Fraud Detection Results:")
    print(f"Fraud Probability: {result['fraud_probability']:.2%}")
    print(f"Risk Level: {result['fraud_risk_level']}")
    print(f"Indicators: {result['indicators']}")
