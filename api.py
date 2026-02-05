"""
Full Out Media - Website Checker API
Flask backend for the website analyzer
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from website_analyzer import WebsiteAnalyzer, generate_audit_report
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


@app.route('/api/analyze', methods=['POST'])
def analyze_website():
    """Analyze a website and return results"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Run analysis
        analyzer = WebsiteAnalyzer(url)
        results = analyzer.run_full_analysis()
        
        # Generate report
        report = generate_audit_report(results)
        results['report'] = report
        
        return jsonify(results)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'Full Out Media Website Checker'})


@app.route('/')
def index():
    """Serve info page"""
    return """
    <html>
    <head><title>Full Out Media - Website Checker API</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>🔍 Website Checker API</h1>
        <p>Full Out Media - Performance Marketing Agency</p>
        <hr>
        <h3>Endpoints:</h3>
        <ul>
            <li><code>POST /api/analyze</code> - Analyze a website</li>
            <li><code>GET /api/health</code> - Health check</li>
        </ul>
        <h3>Example request:</h3>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
POST /api/analyze
Content-Type: application/json

{
    "url": "https://example.ro"
}
        </pre>
        <p><a href="https://fulloutmedia.ro">← Back to Full Out Media</a></p>
    </body>
    </html>
    """


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
