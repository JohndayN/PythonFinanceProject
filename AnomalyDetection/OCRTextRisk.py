import pytesseract
import cv2
from transformers import pipeline

# OCR
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text

# NLP Risk classifier
risk_model = pipeline("sentiment-analysis")

def compute_text_risk(text):
    result = risk_model(text[:512])
    
    if result[0]['label'] == 'NEGATIVE':
        return result[0]['score']
    return 0