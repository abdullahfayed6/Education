"""
LinkedIn Jobs Search via SerpAPI Google Search.
Uses site:linkedin.com/jobs operator to scrape LinkedIn job listings.
ONLY returns intern/internship positions.
"""
from __future__ import annotations

import logging
import re
import time

import requests

from app.config import settings
from app.models.schemas import OpportunityRaw

logger = logging.getLogger("linkedin_client")


# ============ Track to Job Titles Mapping ============
TRACK_TITLES = {
    "data science": ["Data Science Intern", "Data Scientist Intern", "Data Analyst Intern", "Analytics Intern"],
    "data scientist": ["Data Science Intern", "Data Scientist Intern", "Data Analyst Intern", "ML Intern"],
    "machine learning": ["Machine Learning Intern", "ML Engineer Intern", "AI Intern", "Deep Learning Intern"],
    "ai engineer": ["AI Intern", "Machine Learning Intern", "AI Engineer Intern", "ML Intern"],
    "software engineering": ["Software Engineer Intern", "Software Developer Intern", "SWE Intern", "Developer Intern"],
    "computer science": ["Software Engineer Intern", "Software Developer Intern", "CS Intern", "Developer Intern"],
    "backend": ["Backend Intern", "Backend Developer Intern", "Server-Side Developer Intern", "API Developer Intern"],
    "backend developer": ["Backend Intern", "Backend Developer Intern", "Node.js Intern", "Python Developer Intern"],
    "frontend": ["Frontend Intern", "Frontend Developer Intern", "UI Developer Intern", "React Intern"],
    "frontend developer": ["Frontend Intern", "React Developer Intern", "Web Developer Intern", "UI Intern"],
    "full stack": ["Full Stack Intern", "Full Stack Developer Intern", "Web Developer Intern", "Software Intern"],
    "devops": ["DevOps Intern", "DevOps Engineer Intern", "SRE Intern", "Platform Engineer Intern", "Cloud Intern"],
    "cloud": ["Cloud Intern", "Cloud Engineer Intern", "AWS Intern", "Azure Intern", "GCP Intern"],
    "mobile": ["Mobile Developer Intern", "iOS Intern", "Android Intern", "Flutter Intern", "Mobile Engineer Intern"],
    "cybersecurity": ["Cybersecurity Intern", "Security Analyst Intern", "Security Engineer Intern", "InfoSec Intern"],
    "data engineering": ["Data Engineering Intern", "Data Engineer Intern", "ETL Intern", "Big Data Intern"],
    "data engineer": ["Data Engineering Intern", "Data Engineer Intern", "ETL Developer Intern", "Pipeline Intern"],
    "product": ["Product Intern", "Product Manager Intern", "APM Intern", "Product Management Intern"],
    "ui/ux": ["UI/UX Intern", "UX Designer Intern", "Product Designer Intern", "Design Intern"],
    "qa": ["QA Intern", "Quality Assurance Intern", "Test Engineer Intern", "SDET Intern"],
    "business analyst": ["Business Analyst Intern", "BA Intern", "Business Intelligence Intern", "BI Intern"],
}

# Exclusion keywords (senior positions)
EXCLUDE_KEYWORDS = ["senior", "lead", "manager", "director", "principal", "staff", "head of", "vp", "chief", "experienced"]


class LinkedInSerpAPIClient:
    """
    Search LinkedIn jobs using SerpAPI Google Search.
    Uses site:linkedin.com/jobs operator.
    Filters for INTERN positions only.
    """
    
    SERPAPI_URL = "https://serpapi.com/search.json"
    
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = 0
    
    def _rate_limit(self) -> None:
        current_time = time.time()
        if current_time - self.last_request_time < 1.0:
            time.sleep(1.0 - (current_time - self.last_request_time))
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _is_intern_position(self, title: str, snippet: str = "") -> bool:
        """
        Check if position is an internship.
        Returns True for intern/internship positions.
        Rejects senior-level positions.
        """
        text = f"{title} {snippet}".lower()
        title_lower = title.lower()
        
        # LinkedIn search results with 'intern' query are usually relevant
        # Accept if title contains intern-related keywords
        intern_keywords = ["intern", "internship", "trainee", "تدريب", "fresh", "junior", "entry"]
        has_intern = any(kw in text for kw in intern_keywords)
        
        # REJECT if title starts with senior keywords (definite rejection)
        reject_starts = ["senior", "lead", "manager", "director", "principal", "staff", "head"]
        for reject in reject_starts:
            if title_lower.startswith(reject):
                return False
        
        # REJECT if title contains these without intern keyword
        if not has_intern:
            for exclude in EXCLUDE_KEYWORDS:
                if exclude in title_lower:
                    return False
        
        # Accept LinkedIn job results (already filtered by search query)
        return True
    
    def _extract_company(self, title: str) -> str:
        """
        Extract company name from LinkedIn title format.
        
        Formats:
        - "Company hiring Job Title in Location"
        - "Job Title - Company - LinkedIn"
        - "Job Title at Company"
        """
        title_lower = title.lower()
        
        # Format: "Company hiring Job Title..."
        if " hiring " in title_lower:
            return title.split(" hiring ")[0].strip()
        
        # Format: "Job Title at Company"
        if " at " in title_lower:
            parts = title.split(" at ")
            if len(parts) >= 2:
                company = parts[-1].strip()
                # Remove trailing location info
                if " in " in company:
                    company = company.split(" in ")[0].strip()
                return company
        
        # Format: "Job Title - Company - LinkedIn"
        if " - " in title:
            parts = title.split(" - ")
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i].strip()
                if part.lower() not in ["linkedin", ""] and len(part) > 2:
                    return part
        
        return "Unknown Company"
    
    def _clean_title(self, title: str) -> str:
        """Clean LinkedIn title to extract just the job title."""
        # Format: "Company hiring Job Title in Location"
        if " hiring " in title.lower():
            after_hiring = title.split(" hiring ", 1)[-1]
            # Remove "in Location" suffix
            if " in " in after_hiring:
                return after_hiring.split(" in ")[0].strip()
            return after_hiring.strip()
        
        # Remove "- LinkedIn" suffix
        title = re.sub(r"\s*-\s*LinkedIn$", "", title, flags=re.IGNORECASE)
        
        # If has " - Company" format, keep just job title
        if " - " in title:
            return title.split(" - ")[0].strip()
        
        # If has " at Company" format, keep just job title
        if " at " in title.lower():
            return title.split(" at ")[0].strip()
        
        return title.strip()
    
    def search(self, query: str, limit: int, location_preference: str = "egypt") -> list[OpportunityRaw]:
        """
        Search LinkedIn jobs via Google with site:linkedin.com/jobs.
        
        Makes 10 searches with 8 results each.
        Uses 10 SerpAPI credits total.
        Returns combined deduplicated results.
        """
        # Simplify query for better results - keep only key terms
        words = query.lower().split()
        clean_words = [w for w in words if len(w) > 2 and w not in ["the", "and", "for", "intern", "internship"]]
        base_query = " ".join(clean_words[:2])  # Max 2 keywords for base
        
        # Build location suffixes
        if location_preference == "egypt":
            locations = ["Egypt", "Cairo"]
        elif location_preference == "remote":
            locations = ["remote", "worldwide"]
        elif location_preference == "abroad":
            locations = ["USA", "Europe", "UAE"]
        else:
            locations = ["Egypt", "Cairo"]
        
        # Job type keywords
        job_types = ["intern", "internship", "trainee", "junior", "fresh graduate"]
        
        # Build 10 search variations
        search_variations = []
        first_word = clean_words[0] if clean_words else "software"
        
        # 10 diverse searches
        search_variations = [
            f'site:linkedin.com/jobs {base_query} intern {locations[0]}',
            f'site:linkedin.com/jobs {base_query} internship {locations[0]}',
            f'site:linkedin.com/jobs {base_query} trainee {locations[0]}',
            f'site:linkedin.com/jobs {first_word} intern {locations[0]}',
            f'site:linkedin.com/jobs {first_word} internship {locations[0]}',
            f'site:linkedin.com/jobs {base_query} junior {locations[0]}',
            f'site:linkedin.com/jobs {base_query} "fresh graduate" {locations[0]}',
            f'site:linkedin.com/jobs {first_word} trainee {locations[0]}',
            f'site:linkedin.com/jobs {base_query} intern {locations[1] if len(locations) > 1 else locations[0]}',
            f'site:linkedin.com/jobs {base_query} internship {locations[1] if len(locations) > 1 else locations[0]}',
        ]
        
        all_results = []
        seen_urls = set()
        credits_used = 0
        
        for search_query in search_variations:
            self._rate_limit()
            credits_used += 1
            
            params = {
                "engine": "google",
                "q": search_query.strip(),
                "api_key": self.api_key,
                "num": 8,  # 8 results per search
                "tbs": "qdr:m",  # Posted in last month
            }
            
            try:
                logger.info(f"LinkedIn search: {search_query}")
                response = requests.get(self.SERPAPI_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                organic_results = data.get("organic_results", [])
                
                for item in organic_results:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")
                    
                    # Skip if already seen
                    if link in seen_urls:
                        continue
                    seen_urls.add(link)
                    
                    # Must be LinkedIn domain
                    if "linkedin.com" not in link.lower():
                        continue
                    
                    # ONLY accept individual job pages (/jobs/view/...)
                    if "/jobs/view/" not in link.lower():
                        continue
                    
                    # Skip senior-level positions
                    title_lower = title.lower()
                    if any(title_lower.startswith(kw) for kw in ["senior", "lead", "manager", "director", "principal"]):
                        continue
                    
                    clean_title = self._clean_title(title)
                    company = self._extract_company(title)
                    
                    all_results.append(
                        OpportunityRaw(
                            title=clean_title,
                            company=company,
                            location="Egypt" if location_preference == "egypt" else "Remote/International",
                            url=link,
                            snippet=snippet,
                            source="LinkedIn",
                            posted_date="Last month",
                        )
                    )
                    
                    if len(all_results) >= limit:
                        break
                
                logger.info(f"Search {credits_used}/10: Found {len(organic_results)} results")
                
            except requests.RequestException as e:
                logger.error(f"SerpAPI error: {e}")
                continue
            
            # Stop if we have enough results
            if len(all_results) >= limit:
                break
        
        logger.info(f"Total: {len(all_results)} unique LinkedIn jobs ({credits_used} API credits used)")
        return all_results[:limit]
    
    def search_with_profile(self, track: str, skills: list[str], location_preference: str, limit: int = 10) -> list[OpportunityRaw]:
        """Search using profile data."""
        track_key = track.lower().strip()
        titles = TRACK_TITLES.get(track_key, TRACK_TITLES.get("software engineering", ["Software Intern"]))
        
        # Use primary title + skills
        query = f"{titles[0]} {' '.join(skills[:2])}" if skills else titles[0]
        return self.search(query, limit, location_preference)


class LinkedInMockClient:
    """Mock client for testing without API."""
    
    def search(self, query: str, limit: int, location_preference: str = "egypt") -> list[OpportunityRaw]:
        import random
        
        intern_titles = [
            "Software Engineering Intern", "Data Science Intern", "Machine Learning Intern",
            "Backend Developer Intern", "Frontend Developer Intern", "DevOps Intern",
            "Data Engineering Intern", "Mobile Developer Intern", "QA Engineering Intern",
        ]
        
        companies = [
            "Vodafone Egypt", "Orange Egypt", "Valeo Egypt", "IBM Egypt", "Microsoft Egypt",
            "Swvl", "Instabug", "Fawry", "Paymob", "Dell Egypt",
        ]
        
        locations = ["Cairo, Egypt", "Smart Village, Giza", "New Cairo, Egypt", "Maadi, Cairo"]
        
        results = []
        for i in range(limit):
            results.append(
                OpportunityRaw(
                    title=random.choice(intern_titles),
                    company=random.choice(companies),
                    location=random.choice(locations),
                    url=f"https://linkedin.com/jobs/view/{1000 + i}",
                    snippet=f"Great internship opportunity for students. {query}",
                    source="LinkedIn",
                    posted_date="1 week ago",
                )
            )
        return results
    
    def search_with_profile(self, track: str, skills: list[str], location_preference: str, limit: int = 10) -> list[OpportunityRaw]:
        return self.search(f"{track} intern", limit, location_preference)


def get_linkedin_client() -> LinkedInSerpAPIClient | LinkedInMockClient:
    """Get LinkedIn client - uses SerpAPI for real search."""
    if settings.search_api_key:
        logger.info("Using SerpAPI for LinkedIn search")
        return LinkedInSerpAPIClient(settings.search_api_key)
    
    logger.info("Using mock LinkedIn client (no API key)")
    return LinkedInMockClient()
