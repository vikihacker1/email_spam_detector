import email
from email.policy import default
import dns.resolver
import dkim
from joblib import load
import re
from nltk.corpus import stopwords

# Load the trained model
try:
    model = load('model/spam_classifier.joblib')
except FileNotFoundError:
    print("Model file not found. Please run train_model.py first.")
    model = None

def clean_text_for_prediction(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = ' '.join([word for word in text.split() if word not in stopwords.words('english')])
    return text

def analyze_email_content(msg):
    if not model:
        return 'MODEL NOT TRAINED', 0.0

    content = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                content += str(part.get_payload(decode=True), 'latin-1', 'ignore')
    else:
        content = str(msg.get_payload(decode=True), 'latin-1', 'ignore')

    if not content:
        return 'NO TEXT CONTENT', 0.0

    cleaned_content = clean_text_for_prediction(content)
    prediction = model.predict([cleaned_content])[0]
    probability = model.predict_proba([cleaned_content])[0]
    confidence = max(probability)

    result = "SPAM" if prediction == 1 else "LEGITIMATE"
    return result, confidence

def get_domain_from_header(header):
    if not header:
        return None
    match = re.search(r'@([\w.-]+)', header)
    return match.group(1).strip('>') if match else None

def analyze(raw_email):
    msg = email.message_from_string(raw_email, policy=default)
    
    # --- Critical Information Extraction ---
    from_header = msg.get('From', '')
    from_domain = get_domain_from_header(from_header)
    
    # Check for Authentication-Results header, which is more reliable
    auth_results_header = msg.get('Authentication-Results', '')

    # --- 1. Authentication Analysis ---
    spf_result = "NEUTRAL"
    dkim_result = "NEUTRAL"
    dkim_domain = None
    
    # Prioritize the Authentication-Results header
    if 'spf=pass' in auth_results_header:
        spf_result = "PASS"
    elif 'spf=fail' in auth_results_header:
        spf_result = "FAIL"
        
    if 'dkim=pass' in auth_results_header:
        dkim_result = "PASS"
        # Extract the domain that passed DKIM
        match = re.search(r'header.d=([\w.-]+)', auth_results_header)
        if match:
            dkim_domain = match.group(1)
    elif 'dkim=fail' in auth_results_header:
        dkim_result = "FAIL"

    # --- 2. DMARC Alignment Check (The Crucial Fix) ---
    alignment = {
        'spf_aligned': False,
        'dkim_aligned': False,
        'result': "FAIL"
    }
    # For DKIM, the signed domain must match the From: domain
    if dkim_result == "PASS" and dkim_domain and dkim_domain.lower() == from_domain.lower():
        alignment['dkim_aligned'] = True

    # Note: A true SPF alignment check is more complex, but DKIM is key for this scenario.
    if alignment['dkim_aligned']: # Simplified: if DKIM aligns, we consider it aligned.
        alignment['result'] = "PASS"

    # --- 3. Content Analysis ---
    content_result, confidence = analyze_email_content(msg)
    
    # --- 4. Final Scoring ---
    risk_score = 0
    verdict = "LEGITIMATE"
    
    if dkim_result == "FAIL":
        risk_score += 40
    if alignment['result'] == "FAIL" and from_domain: # HUGE penalty for misalignment
        risk_score += 50
    if spf_result == "FAIL":
        risk_score += 20
    if content_result == "SPAM":
        risk_score += int(30 * confidence)

    risk_score = min(risk_score, 100) # Cap score at 100

    if risk_score >= 70:
        verdict = "HIGH RISK - LIKELY SPOOFED OR PHISHING"
    elif risk_score >= 40:
        verdict = "SUSPICIOUS"
    
    return {
        'verdict': verdict,
        'risk_score': risk_score,
        'auth': {
            'SPF': spf_result,
            'DKIM': f"{dkim_result} (domain: {dkim_domain or 'N/A'})",
        },
        'alignment': alignment,
        'headers': {'From': from_header, 'From Domain': from_domain},
        'content': {
            'result': content_result,
            'confidence': f"{confidence:.2%}"
        }
    }