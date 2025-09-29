from flask import Flask, render_template, request
from detector import analyze

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_email():
    raw_email = request.form['raw_email']
    if not raw_email:
        return "Please paste the raw email source.", 400
    
    results = analyze(raw_email)
    return render_template('result.html', results=results)

if __name__ == '__main__':
    # Important: Use a production-ready server like Gunicorn for deployment
    app.run(debug=True, port=5001)