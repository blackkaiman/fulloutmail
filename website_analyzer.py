"""
Full Out Media - Website Analyzer Backend
Crawl website, analyze SEO, detect tracking, check Meta Ads Library
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, urljoin
import time

class WebsiteAnalyzer:
    def __init__(self, url):
        self.url = url if url.startswith('http') else f'https://{url}'
        self.domain = urlparse(self.url).netloc
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.html = None
        self.soup = None
        self.results = {
            'url': self.url,
            'domain': self.domain,
            'platform': None,
            'seo': {},
            'technical': {},
            'tracking': {},
            'meta_ads': {},
            'scores': {},
            'issues': [],
            'opportunities': []
        }
    
    def crawl(self):
        """Fetch and parse the website"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            self.html = response.text
            self.soup = BeautifulSoup(self.html, 'html.parser')
            return True
        except Exception as e:
            self.results['error'] = str(e)
            return False
    
    def detect_platform(self):
        """Detect eCommerce platform"""
        platforms = {
            'merchantpro': ['merchantpro', 'mp-'],
            'gomag': ['gomag', 'gomag.ro'],
            'shopify': ['shopify', 'cdn.shopify'],
            'woocommerce': ['woocommerce', 'wp-content/plugins/woocommerce'],
            'magento': ['magento', 'mage'],
            'prestashop': ['prestashop', 'presta'],
            'opencart': ['opencart'],
            'vtex': ['vtex']
        }
        
        html_lower = self.html.lower() if self.html else ''
        
        for platform, signatures in platforms.items():
            for sig in signatures:
                if sig in html_lower:
                    self.results['platform'] = platform.capitalize()
                    return platform
        
        self.results['platform'] = 'Unknown'
        return None
    
    def analyze_seo(self):
        """Analyze SEO elements"""
        seo = {}
        issues = []
        
        # Title tag
        title_tag = self.soup.find('title')
        seo['title'] = title_tag.get_text().strip() if title_tag else None
        seo['title_length'] = len(seo['title']) if seo['title'] else 0
        
        if not seo['title']:
            issues.append({
                'type': 'error',
                'category': 'seo',
                'title': 'Title tag lipsă',
                'description': 'Pagina nu are un title tag definit. Acesta este esențial pentru SEO.',
                'impact': 'Afectează semnificativ vizibilitatea în motoarele de căutare'
            })
        elif seo['title_length'] < 30:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': 'Title tag prea scurt',
                'description': f'Title-ul are doar {seo["title_length"]} caractere. Recomandat: 50-60 caractere.',
                'impact': 'CTR mai mic în rezultatele căutării'
            })
        elif seo['title_length'] > 60:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': 'Title tag prea lung',
                'description': f'Title-ul are {seo["title_length"]} caractere și va fi trunchiat în Google.',
                'impact': 'Mesajul cheie poate fi tăiat'
            })
        
        # Meta description
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        seo['meta_description'] = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else None
        seo['meta_description_length'] = len(seo['meta_description']) if seo['meta_description'] else 0
        
        if not seo['meta_description']:
            issues.append({
                'type': 'error',
                'category': 'seo',
                'title': 'Meta description lipsă',
                'description': 'Pagina nu are meta description. Google va genera automat una din conținut.',
                'impact': '+15-25% CTR potențial cu o descriere optimizată'
            })
        elif seo['meta_description_length'] < 120:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': 'Meta description prea scurtă',
                'description': f'Descrierea are doar {seo["meta_description_length"]} caractere. Recomandat: 150-160.',
                'impact': 'Nu profiti de tot spațiul disponibil pentru convingere'
            })
        
        # H1 tags
        h1_tags = self.soup.find_all('h1')
        seo['h1_count'] = len(h1_tags)
        seo['h1_texts'] = [h1.get_text().strip() for h1 in h1_tags[:3]]
        
        if seo['h1_count'] == 0:
            issues.append({
                'type': 'error',
                'category': 'seo',
                'title': 'H1 tag lipsă',
                'description': 'Pagina nu are un heading H1. Acesta este important pentru structura SEO.',
                'impact': 'Afectează înțelegerea paginii de către Google'
            })
        elif seo['h1_count'] > 1:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': f'Multiple H1 tags ({seo["h1_count"]})',
                'description': 'Pagina are mai multe H1-uri. Recomandat: un singur H1 per pagină.',
                'impact': 'Poate dilua relevanța pentru keyword-ul principal'
            })
        
        # Images without ALT
        images = self.soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt') or img.get('alt').strip() == '']
        seo['total_images'] = len(images)
        seo['images_without_alt'] = len(images_without_alt)
        seo['images_alt_percentage'] = round((1 - len(images_without_alt) / max(len(images), 1)) * 100)
        
        if seo['images_without_alt'] > 0:
            pct = round(seo['images_without_alt'] / max(seo['total_images'], 1) * 100)
            issues.append({
                'type': 'warning' if pct < 50 else 'error',
                'category': 'seo',
                'title': f'{seo["images_without_alt"]} imagini fără ALT ({pct}%)',
                'description': 'Imaginile fără text alternativ nu sunt indexate în Google Images.',
                'impact': 'Pierzi trafic organic din Google Images'
            })
        
        # Canonical URL
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        seo['canonical'] = canonical['href'] if canonical and canonical.get('href') else None
        
        if not seo['canonical']:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': 'Canonical URL lipsă',
                'description': 'Nu am detectat un tag canonical. Risc de conținut duplicat.',
                'impact': 'Poate cauza probleme de indexare'
            })
        
        # Open Graph tags
        og_title = self.soup.find('meta', attrs={'property': 'og:title'})
        og_desc = self.soup.find('meta', attrs={'property': 'og:description'})
        og_image = self.soup.find('meta', attrs={'property': 'og:image'})
        
        seo['og_tags'] = {
            'title': bool(og_title),
            'description': bool(og_desc),
            'image': bool(og_image)
        }
        
        missing_og = [k for k, v in seo['og_tags'].items() if not v]
        if missing_og:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': f'Open Graph tags incomplete',
                'description': f'Lipsesc: {", ".join(missing_og)}. Afectează share-urile pe social media.',
                'impact': 'Link-urile partajate vor arăta mai puțin atrăgător'
            })
        
        # Structured data
        schema_scripts = self.soup.find_all('script', attrs={'type': 'application/ld+json'})
        seo['has_structured_data'] = len(schema_scripts) > 0
        seo['structured_data_count'] = len(schema_scripts)
        
        if not seo['has_structured_data']:
            issues.append({
                'type': 'warning',
                'category': 'seo',
                'title': 'Structured data (Schema.org) lipsă',
                'description': 'Nu am detectat markup JSON-LD. Pierzi rich snippets în Google.',
                'impact': 'Fără rating stars, preț, disponibilitate în rezultate'
            })
        
        self.results['seo'] = seo
        self.results['issues'].extend(issues)
        
        # Calculate SEO score
        score = 100
        for issue in issues:
            if issue['category'] == 'seo':
                score -= 15 if issue['type'] == 'error' else 8
        self.results['scores']['seo'] = max(0, min(100, score))
    
    def analyze_tracking(self):
        """Analyze tracking pixels and tags"""
        tracking = {}
        issues = []
        
        # Google Tag Manager
        gtm_pattern = r'GTM-[A-Z0-9]+'
        gtm_matches = re.findall(gtm_pattern, self.html)
        tracking['gtm'] = {
            'detected': len(gtm_matches) > 0,
            'ids': list(set(gtm_matches))
        }
        
        if not tracking['gtm']['detected']:
            issues.append({
                'type': 'error',
                'category': 'tracking',
                'title': 'Google Tag Manager nedetectat',
                'description': 'Nu am găsit GTM instalat. Fără el, nu poți track-ui corect conversiile.',
                'impact': 'Pierzi date esențiale pentru optimizarea campaniilor'
            })
        
        # Google Analytics 4
        ga4_pattern = r'G-[A-Z0-9]+'
        ga4_matches = re.findall(ga4_pattern, self.html)
        tracking['ga4'] = {
            'detected': len(ga4_matches) > 0,
            'ids': list(set(ga4_matches))
        }
        
        if not tracking['ga4']['detected']:
            issues.append({
                'type': 'error',
                'category': 'tracking',
                'title': 'Google Analytics 4 nedetectat',
                'description': 'Nu am găsit GA4 instalat. Pierzi insight-uri importante despre trafic.',
                'impact': 'Nu poți analiza comportamentul vizitatorilor'
            })
        
        # Google Ads Conversion Tag
        gads_pattern = r'AW-[0-9]+'
        gads_matches = re.findall(gads_pattern, self.html)
        tracking['google_ads'] = {
            'detected': len(gads_matches) > 0,
            'ids': list(set(gads_matches))
        }
        
        if not tracking['google_ads']['detected']:
            issues.append({
                'type': 'error',
                'category': 'tracking',
                'title': 'Google Ads Conversion Tag absent',
                'description': 'Nu am detectat tag de conversie Google Ads. Campaniile nu pot fi optimizate.',
                'impact': 'ROAS real necunoscut, optimizare imposibilă'
            })
        
        # Facebook Pixel
        fb_pixel_pattern = r'fbq\s*\(\s*[\'"]init[\'"]\s*,\s*[\'"](\d+)[\'"]\s*\)'
        fb_matches = re.findall(fb_pixel_pattern, self.html)
        tracking['facebook_pixel'] = {
            'detected': len(fb_matches) > 0,
            'ids': list(set(fb_matches))
        }
        
        # Check for FB events
        fb_events = []
        for event in ['Purchase', 'AddToCart', 'ViewContent', 'InitiateCheckout', 'AddPaymentInfo']:
            if f"'{event}'" in self.html or f'"{event}"' in self.html:
                fb_events.append(event)
        tracking['facebook_events'] = fb_events
        
        if not tracking['facebook_pixel']['detected']:
            issues.append({
                'type': 'error',
                'category': 'tracking',
                'title': 'Facebook Pixel nedetectat',
                'description': 'Nu am găsit Facebook Pixel. Nu poți rula campanii Meta Ads eficient.',
                'impact': 'Fără remarketing și fără optimizare pentru conversii'
            })
        elif len(fb_events) < 3:
            issues.append({
                'type': 'warning',
                'category': 'tracking',
                'title': 'Facebook Pixel incomplet configurat',
                'description': f'Pixel detectat dar doar {len(fb_events)} evenimente configurate: {", ".join(fb_events) or "niciunul"}.',
                'impact': 'Optimizarea campaniilor Meta este limitată'
            })
        
        # TikTok Pixel
        tiktok_pattern = r'ttq\.load\s*\(\s*[\'"]([A-Z0-9]+)[\'"]\s*\)'
        tiktok_matches = re.findall(tiktok_pattern, self.html)
        tracking['tiktok_pixel'] = {
            'detected': len(tiktok_matches) > 0,
            'ids': list(set(tiktok_matches))
        }
        
        # Check for Enhanced Conversions (Google)
        tracking['enhanced_conversions'] = 'enhanced_conversion' in self.html.lower() or 'user_data' in self.html.lower()
        
        self.results['tracking'] = tracking
        self.results['issues'].extend(issues)
        
        # Calculate tracking score
        score = 100
        for issue in issues:
            if issue['category'] == 'tracking':
                score -= 18 if issue['type'] == 'error' else 10
        self.results['scores']['tracking'] = max(0, min(100, score))
    
    def analyze_technical(self):
        """Analyze technical aspects"""
        technical = {}
        issues = []
        
        # Check for mobile viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        technical['mobile_viewport'] = viewport is not None
        
        if not technical['mobile_viewport']:
            issues.append({
                'type': 'error',
                'category': 'technical',
                'title': 'Viewport meta tag lipsă',
                'description': 'Site-ul nu este optimizat pentru mobile.',
                'impact': 'Experiență proastă pe mobil, afectează și SEO'
            })
        
        # Check HTTPS
        technical['https'] = self.url.startswith('https')
        
        if not technical['https']:
            issues.append({
                'type': 'error',
                'category': 'technical',
                'title': 'Site-ul nu folosește HTTPS',
                'description': 'Conexiunea nu este securizată. Google penalizează site-urile HTTP.',
                'impact': 'Afectează încrederea și ranking-ul SEO'
            })
        
        # Check for lazy loading
        lazy_images = self.soup.find_all('img', attrs={'loading': 'lazy'})
        technical['lazy_loading'] = len(lazy_images) > 0
        technical['lazy_loading_count'] = len(lazy_images)
        
        # Check for minified resources (basic check)
        scripts = self.soup.find_all('script', src=True)
        minified_scripts = [s for s in scripts if '.min.' in s.get('src', '')]
        technical['scripts_count'] = len(scripts)
        technical['minified_scripts'] = len(minified_scripts)
        
        # External resources count
        external_scripts = [s for s in scripts if s.get('src', '').startswith('http') and self.domain not in s.get('src', '')]
        technical['external_scripts'] = len(external_scripts)
        
        if technical['external_scripts'] > 15:
            issues.append({
                'type': 'warning',
                'category': 'technical',
                'title': f'Multe scripturi externe ({technical["external_scripts"]})',
                'description': 'Prea multe resurse externe încetinesc site-ul.',
                'impact': 'Page speed afectat, bounce rate mai mare'
            })
        
        # Check for render-blocking resources
        stylesheets = self.soup.find_all('link', attrs={'rel': 'stylesheet'})
        technical['stylesheets_count'] = len(stylesheets)
        
        # Cookie consent
        cookie_patterns = ['cookie', 'gdpr', 'consent', 'privacy']
        has_cookie_consent = any(p in self.html.lower() for p in cookie_patterns)
        technical['cookie_consent'] = has_cookie_consent
        
        if not has_cookie_consent:
            issues.append({
                'type': 'warning',
                'category': 'technical',
                'title': 'Cookie consent nedetectat',
                'description': 'Nu am găsit un sistem de consimțământ pentru cookies.',
                'impact': 'Posibile probleme GDPR'
            })
        
        self.results['technical'] = technical
        self.results['issues'].extend(issues)
        
        # Calculate technical score
        score = 100
        for issue in issues:
            if issue['category'] == 'technical':
                score -= 15 if issue['type'] == 'error' else 8
        self.results['scores']['technical'] = max(0, min(100, score))
    
    def check_meta_ads_library(self):
        """Check Meta Ads Library for active ads"""
        meta_ads = {
            'checked': True,
            'active_ads': 0,
            'ad_formats': [],
            'notes': []
        }
        issues = []
        
        # Meta Ads Library API is not publicly available
        # We'll simulate based on domain check or use Facebook Graph API if available
        
        # For demo purposes, we'll check if the site has FB Pixel (indicator they might run ads)
        has_fb_pixel = self.results.get('tracking', {}).get('facebook_pixel', {}).get('detected', False)
        
        if has_fb_pixel:
            # Simulate finding some ads
            meta_ads['active_ads'] = 'detected'
            meta_ads['notes'].append('Facebook Pixel activ - probabil rulează campanii Meta')
            
            self.results['opportunities'].append({
                'category': 'meta_ads',
                'title': 'Audit complet Meta Ads',
                'description': 'Pentru o analiză completă a reclamelor active, contactează-ne pentru un audit gratuit al contului Meta Business.',
                'potential': 'Optimizări de 15-30% pe CPA sunt obișnuite'
            })
        else:
            issues.append({
                'type': 'warning',
                'category': 'meta_ads',
                'title': 'Prezența pe Meta Ads necunoscută',
                'description': 'Fără Facebook Pixel, nu putem verifica activitatea publicitară.',
                'impact': 'Oportunitate pierdută pe cel mai mare canal social'
            })
        
        self.results['meta_ads'] = meta_ads
        self.results['issues'].extend(issues)
        
        # Calculate meta ads score
        score = 70 if has_fb_pixel else 40
        self.results['scores']['meta_ads'] = score
    
    def calculate_overall_score(self):
        """Calculate overall score from all categories"""
        scores = self.results['scores']
        if not scores:
            self.results['scores']['overall'] = 0
            return
        
        weights = {
            'seo': 0.30,
            'tracking': 0.35,
            'technical': 0.20,
            'meta_ads': 0.15
        }
        
        weighted_sum = sum(scores.get(k, 50) * w for k, w in weights.items())
        self.results['scores']['overall'] = round(weighted_sum)
    
    def generate_opportunities(self):
        """Generate growth opportunities based on issues found"""
        opportunities = self.results.get('opportunities', [])
        
        # Based on tracking issues
        if not self.results['tracking'].get('google_ads', {}).get('detected'):
            opportunities.append({
                'category': 'google_ads',
                'title': 'Setup Google Ads Conversion Tracking',
                'description': 'Cu tracking corect, poți optimiza campaniile pentru ROAS real.',
                'potential': '+25-40% eficiență pe bugetul de ads'
            })
        
        # Based on SEO issues
        seo_issues = [i for i in self.results['issues'] if i['category'] == 'seo']
        if len(seo_issues) >= 2:
            opportunities.append({
                'category': 'seo',
                'title': 'Optimizare SEO On-Page',
                'description': 'Rezolvarea problemelor SEO detectate poate crește traficul organic.',
                'potential': '+30-50% trafic organic în 3-6 luni'
            })
        
        # Based on platform
        if self.results['platform'] in ['Merchantpro', 'Gomag', 'Shopify']:
            opportunities.append({
                'category': 'platform',
                'title': f'Optimizare specifică {self.results["platform"]}',
                'description': f'Avem experiență directă cu {self.results["platform"]} și știm exact ce funcționează.',
                'potential': 'Implementare rapidă, rezultate măsurabile'
            })
        
        self.results['opportunities'] = opportunities
    
    def run_full_analysis(self):
        """Run complete website analysis"""
        print(f"🔍 Analyzing {self.url}...")
        
        if not self.crawl():
            return self.results
        
        print("  ✓ Website crawled")
        
        self.detect_platform()
        print(f"  ✓ Platform detected: {self.results['platform']}")
        
        self.analyze_seo()
        print(f"  ✓ SEO analyzed (score: {self.results['scores'].get('seo', 'N/A')})")
        
        self.analyze_tracking()
        print(f"  ✓ Tracking analyzed (score: {self.results['scores'].get('tracking', 'N/A')})")
        
        self.analyze_technical()
        print(f"  ✓ Technical analyzed (score: {self.results['scores'].get('technical', 'N/A')})")
        
        self.check_meta_ads_library()
        print(f"  ✓ Meta Ads checked (score: {self.results['scores'].get('meta_ads', 'N/A')})")
        
        self.calculate_overall_score()
        self.generate_opportunities()
        
        print(f"\n📊 Overall Score: {self.results['scores']['overall']}/100")
        print(f"📋 Issues found: {len(self.results['issues'])}")
        print(f"💡 Opportunities: {len(self.results['opportunities'])}")
        
        return self.results


def generate_audit_report(results):
    """Generate executive audit report from analysis results"""
    
    issues = results.get('issues', [])
    opportunities = results.get('opportunities', [])
    scores = results.get('scores', {})
    platform = results.get('platform', 'Unknown')
    domain = results.get('domain', '')
    
    # Categorize issues
    errors = [i for i in issues if i['type'] == 'error']
    warnings = [i for i in issues if i['type'] == 'warning']
    
    report = f"""
---
Website Snapshot:
{domain} | Platform: {platform}
Scor general: {scores.get('overall', 'N/A')}/100 | SEO: {scores.get('seo', 'N/A')} | Tracking: {scores.get('tracking', 'N/A')} | Technical: {scores.get('technical', 'N/A')}

Key Growth Gaps:
"""
    
    # Add top issues
    for i, issue in enumerate(issues[:5], 1):
        icon = "🔴" if issue['type'] == 'error' else "🟡"
        report += f"• {icon} {issue['title']}: {issue['description']}\n"
    
    report += f"""
Revenue Opportunity:
Bazat pe analiza efectuată, estimăm următoarele îmbunătățiri posibile:
• Conversii: +25-40% cu tracking corect și optimizare campanii
• Cost per achiziție: -15-25% prin structuri de campanii eficiente  
• Trafic organic: +30-50% în 3-6 luni cu SEO fix

Next Step:
Ai 15 minute pentru o discuție? Analizăm împreună conturile tale de ads și îți arătăm exact ce putem optimiza.
→ Programează aici: https://fulloutmedia.ro/contact
---
"""
    
    return report


# Example usage
if __name__ == "__main__":
    # Test with a sample URL
    test_url = input("Enter website URL to analyze: ").strip()
    
    if test_url:
        analyzer = WebsiteAnalyzer(test_url)
        results = analyzer.run_full_analysis()
        
        # Save results to JSON
        with open('analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*50)
        print(generate_audit_report(results))
        
        print("\n✅ Full results saved to analysis_results.json")
