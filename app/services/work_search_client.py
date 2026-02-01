"""
Work Search Client - Job and Freelance Search APIs Integration.

Supports:
- Jobs: Adzuna, RapidAPI (JSearch), SerpAPI (Google Jobs)
- Freelance: Platform URL generators with search queries
"""
from __future__ import annotations

import logging
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import urllib.parse

import httpx

logger = logging.getLogger(__name__)


# ============================================
# Configuration
# ============================================

class JobSearchProvider(str, Enum):
    """Available job search providers."""
    ADZUNA = "adzuna"
    JSEARCH = "jsearch"  # RapidAPI
    SERPAPI = "serpapi"  # Google Jobs
    REMOTIVE = "remotive"  # Free remote jobs API
    ARBEITNOW = "arbeitnow"  # Free jobs API


class FreelanceProvider(str, Enum):
    """Freelance platforms."""
    UPWORK = "upwork"
    FIVERR = "fiverr"
    FREELANCER = "freelancer"
    TOPTAL = "toptal"
    PEOPLEPERHOUR = "peopleperhour"
    GURU = "guru"


@dataclass
class JobListing:
    """Job listing from search."""
    title: str
    company: str
    location: str
    url: str
    salary: Optional[str] = None
    description: Optional[str] = None
    source: str = "unknown"
    posted_date: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, internship


@dataclass
class FreelanceGig:
    """Freelance gig/search URL."""
    platform: str
    search_url: str
    gig_type: str
    platform_logo: Optional[str] = None
    tips: Optional[str] = None


# ============================================
# Job Search Clients
# ============================================

class AdzunaClient:
    """
    Adzuna Job Search API.
    Free tier: 250 calls/month
    Docs: https://developer.adzuna.com/
    """
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "")
        self.country = os.getenv("ADZUNA_COUNTRY", "us")  # us, gb, de, etc.
    
    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)
    
    async def search_jobs(
        self,
        keywords: List[str],
        location: str = "",
        results_per_page: int = 5,
        what_or: str = "",
        salary_min: int = 0
    ) -> List[JobListing]:
        """Search for jobs on Adzuna."""
        if not self.is_configured:
            logger.warning("Adzuna API not configured")
            return []
        
        try:
            query = " ".join(keywords)
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": results_per_page,
                "what": query,
                "content-type": "application/json"
            }
            
            if location:
                params["where"] = location
            if what_or:
                params["what_or"] = what_or
            if salary_min:
                params["salary_min"] = salary_min
            
            url = f"{self.BASE_URL}/{self.country}/search/1"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            jobs = []
            for result in data.get("results", []):
                jobs.append(JobListing(
                    title=result.get("title", ""),
                    company=result.get("company", {}).get("display_name", "Unknown"),
                    location=result.get("location", {}).get("display_name", ""),
                    url=result.get("redirect_url", ""),
                    salary=self._format_salary(result),
                    description=result.get("description", "")[:200],
                    source="Adzuna",
                    posted_date=result.get("created", ""),
                    job_type=result.get("contract_type", "")
                ))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Adzuna search error: {e}")
            return []
    
    def _format_salary(self, result: dict) -> str:
        min_sal = result.get("salary_min")
        max_sal = result.get("salary_max")
        if min_sal and max_sal:
            return f"${int(min_sal):,} - ${int(max_sal):,}"
        elif min_sal:
            return f"From ${int(min_sal):,}"
        return ""


class JSearchClient:
    """
    JSearch API via RapidAPI.
    Provides LinkedIn, Indeed, Glassdoor jobs.
    Docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """
    
    BASE_URL = "https://jsearch.p.rapidapi.com"
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY", "")
        self.host = "jsearch.p.rapidapi.com"
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def search_jobs(
        self,
        query: str,
        location: str = "",
        num_pages: int = 1,
        date_posted: str = "month",  # all, today, 3days, week, month
        remote_only: bool = False,
        employment_types: str = ""  # FULLTIME, CONTRACTOR, PARTTIME, INTERN
    ) -> List[JobListing]:
        """Search for jobs using JSearch (RapidAPI)."""
        if not self.is_configured:
            logger.warning("JSearch API not configured")
            return []
        
        try:
            search_query = query
            if location:
                search_query = f"{query} in {location}"
            
            params = {
                "query": search_query,
                "page": "1",
                "num_pages": str(num_pages),
                "date_posted": date_posted
            }
            
            if remote_only:
                params["remote_jobs_only"] = "true"
            if employment_types:
                params["employment_types"] = employment_types
            
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.host
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
            
            jobs = []
            for result in data.get("data", [])[:10]:
                jobs.append(JobListing(
                    title=result.get("job_title", ""),
                    company=result.get("employer_name", "Unknown"),
                    location=result.get("job_city", "") or result.get("job_country", ""),
                    url=result.get("job_apply_link", "") or result.get("job_google_link", ""),
                    salary=self._format_salary(result),
                    description=result.get("job_description", "")[:200],
                    source=result.get("job_publisher", "JSearch"),
                    posted_date=result.get("job_posted_at_datetime_utc", ""),
                    job_type=result.get("job_employment_type", "")
                ))
            
            return jobs
            
        except Exception as e:
            logger.error(f"JSearch error: {e}")
            return []
    
    def _format_salary(self, result: dict) -> str:
        min_sal = result.get("job_min_salary")
        max_sal = result.get("job_max_salary")
        currency = result.get("job_salary_currency", "USD")
        period = result.get("job_salary_period", "")
        
        if min_sal and max_sal:
            return f"{currency} {int(min_sal):,} - {int(max_sal):,} {period}"
        elif min_sal:
            return f"From {currency} {int(min_sal):,} {period}"
        return ""


class RemotiveClient:
    """
    Remotive API - Free remote jobs API.
    No API key required!
    Docs: https://remotive.com/api/remote-jobs
    """
    
    BASE_URL = "https://remotive.com/api/remote-jobs"
    
    async def search_jobs(
        self,
        category: str = "",
        search: str = "",
        limit: int = 5
    ) -> List[JobListing]:
        """Search for remote jobs on Remotive."""
        try:
            params = {"limit": limit}
            
            if category:
                # software-dev, data, design, marketing, etc.
                params["category"] = category
            if search:
                params["search"] = search
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            jobs = []
            for result in data.get("jobs", [])[:limit]:
                jobs.append(JobListing(
                    title=result.get("title", ""),
                    company=result.get("company_name", "Unknown"),
                    location="Remote",
                    url=result.get("url", ""),
                    salary=result.get("salary", ""),
                    description=self._clean_html(result.get("description", ""))[:200],
                    source="Remotive",
                    posted_date=result.get("publication_date", ""),
                    job_type=result.get("job_type", "")
                ))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Remotive search error: {e}")
            return []
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        return re.sub(r'<[^>]+>', '', text)


class ArbeitnowClient:
    """
    Arbeitnow API - Free jobs API.
    No API key required!
    Docs: https://www.arbeitnow.com/api
    """
    
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"
    
    async def search_jobs(self, limit: int = 5) -> List[JobListing]:
        """Get jobs from Arbeitnow."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()
                data = response.json()
            
            jobs = []
            for result in data.get("data", [])[:limit]:
                jobs.append(JobListing(
                    title=result.get("title", ""),
                    company=result.get("company_name", "Unknown"),
                    location=result.get("location", ""),
                    url=result.get("url", ""),
                    description=result.get("description", "")[:200],
                    source="Arbeitnow",
                    posted_date=result.get("created_at", ""),
                    job_type="Remote" if result.get("remote", False) else "On-site"
                ))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Arbeitnow search error: {e}")
            return []


# ============================================
# Freelance Platform URL Generators
# ============================================

class FreelancePlatformURLs:
    """Generate search URLs for freelance platforms."""
    
    PLATFORMS = {
        "upwork": {
            "name": "Upwork",
            "base_url": "https://www.upwork.com/nx/search/jobs/",
            "search_param": "q",
            "logo": "🟢",
            "tips": "Create a strong profile, start with lower rates to build reviews"
        },
        "fiverr": {
            "name": "Fiverr",
            "base_url": "https://www.fiverr.com/search/gigs",
            "search_param": "query",
            "logo": "🟢",
            "tips": "Create specific gigs, use good thumbnails, respond quickly"
        },
        "freelancer": {
            "name": "Freelancer.com",
            "base_url": "https://www.freelancer.com/jobs/",
            "search_param": None,  # Uses path
            "logo": "🔵",
            "tips": "Bid on projects quickly, write personalized proposals"
        },
        "toptal": {
            "name": "Toptal",
            "base_url": "https://www.toptal.com/",
            "search_param": None,
            "logo": "⭐",
            "tips": "Requires screening process, best for senior developers"
        },
        "peopleperhour": {
            "name": "PeoplePerHour",
            "base_url": "https://www.peopleperhour.com/freelance-",
            "search_param": None,
            "logo": "🟠",
            "tips": "Good for UK/EU clients, create hourlies for passive leads"
        },
        "guru": {
            "name": "Guru",
            "base_url": "https://www.guru.com/d/jobs/q/",
            "search_param": None,
            "logo": "🟣",
            "tips": "Lower competition than Upwork, good for beginners"
        },
        "flexjobs": {
            "name": "FlexJobs",
            "base_url": "https://www.flexjobs.com/search?search=",
            "search_param": None,
            "logo": "💼",
            "tips": "Paid membership but vetted jobs, no scams"
        },
        "weworkremotely": {
            "name": "We Work Remotely",
            "base_url": "https://weworkremotely.com/remote-jobs/search?term=",
            "search_param": None,
            "logo": "🌍",
            "tips": "High-quality remote jobs, mostly full-time positions"
        }
    }
    
    @classmethod
    def generate_search_url(cls, platform: str, keywords: List[str]) -> Optional[FreelanceGig]:
        """Generate a search URL for a freelance platform."""
        platform_key = platform.lower()
        if platform_key not in cls.PLATFORMS:
            return None
        
        config = cls.PLATFORMS[platform_key]
        query = "+".join([urllib.parse.quote(k) for k in keywords])
        
        if config["search_param"]:
            url = f"{config['base_url']}?{config['search_param']}={query}"
        else:
            url = f"{config['base_url']}{query}"
        
        return FreelanceGig(
            platform=config["name"],
            search_url=url,
            gig_type=" ".join(keywords),
            platform_logo=config["logo"],
            tips=config["tips"]
        )
    
    @classmethod
    def get_all_search_urls(cls, keywords: List[str]) -> List[FreelanceGig]:
        """Generate search URLs for all platforms."""
        gigs = []
        for platform in cls.PLATFORMS:
            gig = cls.generate_search_url(platform, keywords)
            if gig:
                gigs.append(gig)
        return gigs


# ============================================
# Direct Job Board URLs
# ============================================

class JobBoardURLs:
    """Generate search URLs for job boards."""
    
    BOARDS = {
        "linkedin": {
            "name": "LinkedIn Jobs",
            "base_url": "https://www.linkedin.com/jobs/search/",
            "params": {"keywords": "", "location": "", "f_E": "1,2"},  # Entry level
            "logo": "🔵"
        },
        "indeed": {
            "name": "Indeed",
            "base_url": "https://www.indeed.com/jobs",
            "params": {"q": "", "l": ""},
            "logo": "🟣"
        },
        "glassdoor": {
            "name": "Glassdoor",
            "base_url": "https://www.glassdoor.com/Job/jobs.htm",
            "params": {"sc.keyword": ""},
            "logo": "🟢"
        },
        "dice": {
            "name": "Dice (Tech Jobs)",
            "base_url": "https://www.dice.com/jobs",
            "params": {"q": "", "location": ""},
            "logo": "🔴"
        },
        "stackoverflow": {
            "name": "Stack Overflow Jobs",
            "base_url": "https://stackoverflow.com/jobs",
            "params": {"q": ""},
            "logo": "🟠"
        },
        "angellist": {
            "name": "Wellfound (AngelList)",
            "base_url": "https://wellfound.com/role/",
            "params": {},
            "logo": "⚪"
        },
        "github_jobs": {
            "name": "GitHub Jobs",
            "base_url": "https://jobs.github.com/positions",
            "params": {"description": ""},
            "logo": "⚫"
        },
        "remoteok": {
            "name": "Remote OK",
            "base_url": "https://remoteok.com/remote-",
            "params": {},
            "logo": "🌍"
        }
    }
    
    @classmethod
    def generate_search_url(cls, board: str, keywords: List[str], location: str = "") -> dict:
        """Generate a search URL for a job board."""
        board_key = board.lower().replace(" ", "_")
        if board_key not in cls.BOARDS:
            return {}
        
        config = cls.BOARDS[board_key]
        query = " ".join(keywords)
        encoded_query = urllib.parse.quote(query)
        
        # Build URL based on board type
        if board_key == "linkedin":
            params = f"?keywords={encoded_query}"
            if location:
                params += f"&location={urllib.parse.quote(location)}"
            params += "&f_E=1%2C2"  # Entry level filter
            url = config["base_url"] + params
        elif board_key == "indeed":
            url = f"{config['base_url']}?q={encoded_query}"
            if location:
                url += f"&l={urllib.parse.quote(location)}"
        elif board_key == "remoteok":
            slug = "-".join([k.lower() for k in keywords[:2]])
            url = f"{config['base_url']}{slug}-jobs"
        elif board_key == "angellist":
            role_slug = "-".join([k.lower() for k in keywords[:2]])
            url = f"{config['base_url']}{role_slug}"
        else:
            url = f"{config['base_url']}?q={encoded_query}"
        
        return {
            "name": config["name"],
            "url": url,
            "logo": config["logo"]
        }
    
    @classmethod
    def get_all_search_urls(cls, keywords: List[str], location: str = "") -> List[dict]:
        """Generate search URLs for all job boards."""
        urls = []
        for board in cls.BOARDS:
            url_info = cls.generate_search_url(board, keywords, location)
            if url_info:
                urls.append(url_info)
        return urls


# ============================================
# Main Search Client
# ============================================

class WorkSearchClient:
    """
    Unified work search client.
    Combines multiple job and freelance search sources.
    """
    
    def __init__(self):
        self.adzuna = AdzunaClient()
        self.jsearch = JSearchClient()
        self.remotive = RemotiveClient()
        self.arbeitnow = ArbeitnowClient()
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Check which API providers are configured."""
        return {
            "adzuna": self.adzuna.is_configured,
            "jsearch": self.jsearch.is_configured,
            "remotive": True,  # No API key needed
            "arbeitnow": True,  # No API key needed
        }
    
    async def search_jobs(
        self,
        keywords: List[str],
        location: str = "",
        job_type: str = "",  # internship, junior, entry
        limit: int = 10,
        remote_only: bool = False
    ) -> Dict[str, Any]:
        """
        Search for jobs across multiple providers.
        Returns both API results and direct search URLs.
        """
        results = {
            "api_jobs": [],
            "search_urls": [],
            "providers_used": []
        }
        
        query = " ".join(keywords)
        if job_type:
            query = f"{job_type} {query}"
        
        # Run API searches in parallel
        tasks = []
        
        # Free APIs (always available)
        tasks.append(self.remotive.search_jobs(search=query, limit=limit))
        results["providers_used"].append("Remotive")
        
        tasks.append(self.arbeitnow.search_jobs(limit=limit))
        results["providers_used"].append("Arbeitnow")
        
        # Paid APIs (if configured)
        if self.adzuna.is_configured:
            tasks.append(self.adzuna.search_jobs(keywords, location, limit))
            results["providers_used"].append("Adzuna")
        
        if self.jsearch.is_configured:
            employment_type = "INTERN" if "intern" in job_type.lower() else ""
            tasks.append(self.jsearch.search_jobs(
                query, location, 
                remote_only=remote_only,
                employment_types=employment_type
            ))
            results["providers_used"].append("JSearch")
        
        # Execute all searches
        api_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in api_results:
            if isinstance(result, list):
                results["api_jobs"].extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Search failed: {result}")
        
        # Add direct search URLs for major job boards
        results["search_urls"] = JobBoardURLs.get_all_search_urls(keywords, location)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_jobs = []
        for job in results["api_jobs"]:
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
        results["api_jobs"] = unique_jobs[:limit]
        
        return results
    
    def get_freelance_opportunities(
        self,
        skills: List[str],
        gig_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get freelance platform search URLs.
        Returns URLs for finding gigs on various platforms.
        """
        results = {
            "platforms": [],
            "by_skill": {},
            "tips": []
        }
        
        # Main skill-based search URLs
        for skill in skills[:5]:
            skill_urls = FreelancePlatformURLs.get_all_search_urls([skill])
            results["by_skill"][skill] = [
                {
                    "platform": gig.platform,
                    "url": gig.search_url,
                    "logo": gig.platform_logo
                }
                for gig in skill_urls
            ]
        
        # Combined search URLs
        combined_gigs = FreelancePlatformURLs.get_all_search_urls(skills[:3])
        results["platforms"] = [
            {
                "platform": gig.platform,
                "search_url": gig.search_url,
                "logo": gig.platform_logo,
                "tips": gig.tips
            }
            for gig in combined_gigs
        ]
        
        # Add gig type specific URLs if provided
        if gig_types:
            for gig_type in gig_types:
                gig_urls = FreelancePlatformURLs.get_all_search_urls([gig_type])
                results["by_skill"][gig_type] = [
                    {
                        "platform": gig.platform,
                        "url": gig.search_url,
                        "logo": gig.platform_logo
                    }
                    for gig in gig_urls
                ]
        
        # General tips
        results["tips"] = [
            "Start with Upwork and Fiverr for beginners",
            "Build your profile with 2-3 small projects first",
            "Ask for reviews after each completed project",
            "Set competitive (lower) rates initially to build reputation",
            "Respond to messages within 24 hours",
            "Use specific keywords in your profile for better visibility"
        ]
        
        return results
    
    def generate_job_search_urls(
        self,
        job_title: str,
        skills: List[str] = None,
        location: str = ""
    ) -> List[Dict[str, str]]:
        """Generate search URLs for a specific job title."""
        keywords = [job_title]
        if skills:
            keywords.extend(skills[:2])
        
        return JobBoardURLs.get_all_search_urls(keywords, location)
    
    def generate_freelance_urls_for_gig(
        self,
        gig_type: str,
        skills: List[str] = None
    ) -> List[Dict[str, str]]:
        """Generate freelance platform URLs for a specific gig type."""
        keywords = [gig_type]
        if skills:
            keywords.extend(skills[:2])
        
        gigs = FreelancePlatformURLs.get_all_search_urls(keywords)
        return [
            {
                "platform": gig.platform,
                "url": gig.search_url,
                "logo": gig.platform_logo,
                "tips": gig.tips
            }
            for gig in gigs
        ]


# ============================================
# Utility Functions
# ============================================

def get_work_search_client() -> WorkSearchClient:
    """Get a configured work search client instance."""
    return WorkSearchClient()


async def quick_job_search(
    keywords: List[str],
    location: str = "",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Quick job search helper function."""
    client = WorkSearchClient()
    results = await client.search_jobs(keywords, location, limit=limit)
    
    return [
        {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "salary": job.salary,
            "source": job.source
        }
        for job in results["api_jobs"]
    ]


def get_freelance_urls(skills: List[str]) -> Dict[str, List[Dict]]:
    """Quick helper to get freelance platform URLs."""
    client = WorkSearchClient()
    return client.get_freelance_opportunities(skills)
