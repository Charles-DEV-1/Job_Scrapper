from flask import Flask, render_template_string, jsonify
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging
from datetime import datetime
from config import Config
from scrapper import JobScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Mail
mail = Mail(app)

# Initialize scraper
scraper = JobScraper()

# Store last results
last_results = {
    'jobs': [],
    'last_check': None,
    'total_found': 0
}

def send_alert_email(jobs):
    """Send email alert for new jobs"""
    if not jobs:
        return
    
    try:
        # Create email body
        body = "🚀 New Backend Internships Found!\n\n"
        
        for job in jobs:
            body += f"Company: {job['company']}\n"
            body += f"Position: {job['title']}\n"
            body += f"Link: {job['url']}\n"
            body += f"Found: {job['date_found']}\n"
            body += "-" * 40 + "\n\n"
        
        body += f"\nTotal new opportunities: {len(jobs)}"
        
        # Create message
        msg = Message(
            subject=f"🔥 {len(jobs)} New Backend Internships Available!",
            recipients=[app.config['ALERT_EMAIL']],
            body=body  # Remove the asterisks for plain text
        )
        
        # Send email
        mail.send(msg)
        logger.info(f"Email alert sent for {len(jobs)} jobs")
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

def check_jobs():
    """Job checking function to run periodically"""
    global last_results
    
    logger.info("Running scheduled job check...")
    
    try:
        # Scrape for new jobs
        new_jobs = scraper.scrape_all()
        
        if new_jobs:
            logger.info(f"Found {len(new_jobs)} new jobs!")
            last_results['jobs'] = new_jobs
            last_results['last_check'] = datetime.now().isoformat()
            last_results['total_found'] += len(new_jobs)
            
            # Send email alert
            send_alert_email(new_jobs)
        else:
            logger.info("No new jobs found")
            last_results['last_check'] = datetime.now().isoformat()
            
    except Exception as e:
        logger.error(f"Error in job check: {e}")

# HTML template for dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Scraper Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .job-card { 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px;
            background: #f9f9f9;
        }
        .job-title { color: #0066cc; font-size: 1.2em; }
        .job-company { color: #28a745; font-weight: bold; }
        .job-link { color: #0066cc; text-decoration: none; }
        .job-link:hover { text-decoration: underline; }
        .stats { 
            background: #e9ecef; 
            padding: 20px; 
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .stat-item { margin: 5px 0; }
        .success { color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🔍 Backend Internship Scraper Monitor</h1>
    
    <div class="stats">
        <h2>Statistics</h2>
        <div class="stat-item">Last Check: <span class="success">{{ last_check or 'Never' }}</span></div>
        <div class="stat-item">Total Jobs Found: <span class="success">{{ total_found }}</span></div>
        <div class="stat-item">Currently Showing: <span class="success">{{ jobs|length }} latest jobs</span></div>
    </div>
    
    <h2>Latest Jobs Found</h2>
    {% if jobs %}
        {% for job in jobs %}
        <div class="job-card">
            <div class="job-title">{{ job.title }}</div>
            <div class="job-company">{{ job.company }}</div>
            <div class="job-date">Found: {{ job.date_found }}</div>
            <a href="{{ job.url }}" target="_blank" class="job-link">View Job →</a>
        </div>
        {% endfor %}
    {% else %}
        <p>No jobs found yet. Check back soon!</p>
    {% endif %}
    
    <div style="margin-top: 30px; color: #666; font-size: 0.9em;">
        <p>Scraper runs every {{ interval }} hours. Last run: {{ last_check }}</p>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template_string(
        DASHBOARD_HTML,
        jobs=last_results['jobs'][-10:],  # Last 10 jobs
        last_check=last_results['last_check'],
        total_found=last_results['total_found'],
        interval=Config.CHECK_INTERVAL_HOURS
    )

@app.route('/api/jobs')
def api_jobs():
    """API endpoint for jobs"""
    return jsonify({
        'jobs': last_results['jobs'],
        'last_check': last_results['last_check'],
        'total_found': last_results['total_found']
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()})

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_jobs,
    trigger=IntervalTrigger(hours=Config.CHECK_INTERVAL_HOURS),
    id='job_checker',
    name='Check for new jobs every few hours',
    replace_existing=True
)
scheduler.start()

# Run once immediately on startup
with app.app_context():
    check_jobs()

# Shut down scheduler when exiting
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=False)