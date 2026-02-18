import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
from datetime import datetime
from fake_useragent import UserAgent
import random
from urllib.parse import urljoin

class JobScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.seen_file = 'seen_jobs.json'
        self.load_seen_jobs()
        
        # Companies to scrape
        self.companies = [
            {
                'name': 'Google',
                'base_url': 'https://careers.google.com',
                'search_url': 'https://careers.google.com/jobs/results/?degree=BACHELORS&employment_type=INTERN&category=SOFTWARE_ENGINEERING&company=Google&hl=en_US&jlo=en_US&location=United%20States&page=1&sort_by=date',
                'type': 'google'
            },
            {
                'name': 'Microsoft',
                'base_url': 'https://careers.microsoft.com',
                'search_url': 'https://careers.microsoft.com/v2/global/en/jobs?pg=1&pgSz=20&o=Relevance&l=en_us&s=Students%20and%20graduates&t=US%20Citizenship%20Requirement%3DNot%20Required%20-%20US%20Citizenship%3DNot%20Required&t=Employment%20Type%3DInternship&f=Internships',
                'type': 'microsoft'
            },
            {
                'name': 'Amazon',
                'base_url': 'https://amazon.jobs',
                'search_url': 'https://amazon.jobs/en/search?base_query=software+engineer+intern&offset=0&category=software-development&loc_query=United%20States&job_type=Internship&sort=recent',
                'type': 'amazon'
            }
        ]
    
    def load_seen_jobs(self):
        """Load previously seen jobs"""
        try:
            with open(self.seen_file, 'r') as f:
                self.seen_jobs = json.load(f)
        except FileNotFoundError:
            self.seen_jobs = {}
        except json.JSONDecodeError:
            self.seen_jobs = {}
    
    def save_seen_jobs(self):
        """Save seen jobs to file"""
        with open(self.seen_file, 'w') as f:
            json.dump(self.seen_jobs, f, indent=2)
    
    def get_job_id(self, job):
        """Create unique ID for job"""
        job_string = f"{job['company']}-{job['title']}-{job['url']}"
        return hashlib.md5(job_string.encode()).hexdigest()
    
    def is_backend_internship(self, job_title):
        """Check if job is relevant backend internship"""
        keywords = [
            'backend', 'back-end', 'java', 'python', 'go', 'golang',
            'node', 'nodejs', 'spring', 'django', 'flask', 'api',
            'microservice', 'database', 'sql', 'nosql', 'aws',
            'azure', 'gcp', 'cloud', 'distributed', 'server',
            'software engineer', 'developer'
        ]
        
        # Must have internship-related terms
        internship_terms = ['intern', 'internship', 'university graduate', 'new grad', 'student']
        
        text = job_title.lower()
        
        has_internship = any(term in text for term in internship_terms)
        has_backend = any(term in text for term in keywords)
        
        return has_internship and has_backend
    
    def scrape_google(self, company):
        """Scrape Google jobs using html.parser"""
        jobs = []
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(company['search_url'], headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')  # Using built-in parser
            
            # Look for job listings - Google's structure
            job_elements = soup.find_all(['div', 'li'], class_=lambda x: x and ('job' in x.lower() or 'card' in x.lower()))
            
            if not job_elements:
                # Try finding all links that might be jobs
                all_links = soup.find_all('a', href=True)
                for link in all_links[:30]:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if text and ('intern' in text.lower() or 'software' in text.lower()):
                        full_url = href if href.startswith('http') else urljoin(company['base_url'], href)
                        
                        job = {
                            'company': company['name'],
                            'title': text[:100],  # Limit length
                            'url': full_url,
                            'location': 'US',
                            'date_found': datetime.now().isoformat()
                        }
                        
                        if self.is_backend_internship(text):
                            jobs.append(job)
                            if len(jobs) >= 10:
                                break
            else:
                for elem in job_elements[:15]:
                    title_elem = elem.find(['h3', 'h4', 'a', 'span'], class_=lambda x: x and ('title' in x.lower() if x else False))
                    link_elem = elem.find('a', href=True)
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        url = urljoin(company['base_url'], link_elem.get('href', ''))
                        
                        job = {
                            'company': company['name'],
                            'title': title,
                            'url': url,
                            'location': 'US',
                            'date_found': datetime.now().isoformat()
                        }
                        
                        if self.is_backend_internship(title):
                            jobs.append(job)
            
            time.sleep(random.uniform(3, 6))
            
        except Exception as e:
            print(f"Error scraping {company['name']}: {e}")
        
        return jobs
    
    def scrape_microsoft(self, company):
        """Scrape Microsoft jobs"""
        jobs = []
        try:
            headers = {'User-Agent': self.ua.random}
            response = requests.get(company['search_url'], headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job listings
            job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('job' in x.lower() or 'card' in x.lower()))
            
            for card in job_cards[:15]:
                link = card.find('a', href=True)
                if link:
                    title = link.get_text().strip()
                    url = urljoin(company['base_url'], link.get('href', ''))
                    
                    job = {
                        'company': company['name'],
                        'title': title,
                        'url': url,
                        'location': 'US',
                        'date_found': datetime.now().isoformat()
                    }
                    
                    if self.is_backend_internship(title):
                        jobs.append(job)
            
            time.sleep(random.uniform(3, 6))
            
        except Exception as e:
            print(f"Error scraping {company['name']}: {e}")
        
        return jobs
    
    def scrape_generic(self, company):
        """Generic scraper for any company"""
        jobs = []
        try:
            headers = {'User-Agent': self.ua.random}
            response = requests.get(company['search_url'], headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links that might be jobs
            all_links = soup.find_all('a', href=True)
            
            for link in all_links[:30]:
                text = link.get_text().strip()
                href = link.get('href', '')
                
                if text and len(text) > 10 and len(text) < 150:  # Reasonable job title length
                    if any(term in text.lower() for term in ['intern', 'software', 'developer', 'engineer']):
                        full_url = href if href.startswith('http') else urljoin(company['base_url'], href)
                        
                        job = {
                            'company': company['name'],
                            'title': text,
                            'url': full_url,
                            'location': 'US',
                            'date_found': datetime.now().isoformat()
                        }
                        
                        if self.is_backend_internship(text):
                            jobs.append(job)
            
            time.sleep(random.uniform(3, 6))
            
        except Exception as e:
            print(f"Error scraping {company['name']}: {e}")
        
        return jobs
    
    def scrape_all(self):
        """Scrape all companies"""
        all_new_jobs = []
        
        print(f"\n[{datetime.now()}] Starting scrape...")
        
        for company in self.companies:
            print(f"Scraping {company['name']}...")
            
            if company['type'] == 'google':
                jobs = self.scrape_google(company)
            elif company['type'] == 'microsoft':
                jobs = self.scrape_microsoft(company)
            else:
                jobs = self.scrape_generic(company)
            
            # Filter out already seen jobs
            for job in jobs:
                job_id = self.get_job_id(job)
                if job_id not in self.seen_jobs:
                    self.seen_jobs[job_id] = job
                    all_new_jobs.append(job)
                    print(f"  ✓ New: {job['title'][:50]}...")
            
            print(f"  Found {len(jobs)} total")
        
        # Save updated seen jobs
        self.save_seen_jobs()
        
        return all_new_jobs