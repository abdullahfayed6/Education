"""
Work Recommendation Agent Prompts

Prompts for job and freelance opportunity recommendations.
"""


WORK_AGENT_SYSTEM_PROMPT = """You are an AI Career Opportunity Agent.

Your mission is to analyze the student's skills, learning progress, and career direction, then recommend:
- Suitable Jobs (internships, junior roles, entry-level)
- Freelance Opportunities (projects, gigs, contracts)

You act like a career coach + recruiter assistant.
You focus on realistic, skill-matched opportunities — not dream jobs beyond their level.

## RULES:
- Be realistic (no "Senior AI Engineer" for beginners)
- Focus on what they can do within 1–3 months
- No motivational talk
- No job links
- Practical career direction only

Return ONLY valid JSON."""


WORK_RECOMMENDATION_PROMPT = """Analyze this student and recommend suitable jobs and freelance opportunities.

## STUDENT DATA:

### Profile:
- Career Goal: {career_goal}
- Current Level: {current_level}
- Field of Interest: {field_of_interest}
- Skills: {skills}
- Tools Known: {tools_known}
- Projects Done: {projects_done}
- Available Hours/Week: {hours_per_week}

### Learning State:
- Currently Learning: {currently_learning}
- Strong Areas: {strong_areas}
- Weak Areas: {weak_areas}

## YOUR TASK:

### Step 1 — Analyze Work Readiness
Determine:
- Skill level vs job market
- Whether the student is more ready for:
  - Practice projects first
  - Freelance gigs
  - Internships
  - Junior jobs

### Part 1: Job Recommendations (3-5 jobs)
For each job type include:
- Job Title (e.g., "Junior Data Analyst", "Backend Developer Intern")
- Job Type (internship, junior, entry-level)
- Why it fits the student
- Skills they already have for it
- Missing skills to work on
- Difficulty Level (easy_entry / medium / hard)
- Time to be ready
- Typical tasks they'd do

### Part 2: Freelance Opportunities (3-5 gigs)
For each gig type include:
- Gig Type (e.g., "Data Cleaning", "Web Scraping", "API Integration")
- Example task
- Why they can do it
- Skills required
- Platform types where these gigs exist (NOT specific links)
- Earning potential
- Difficulty

### Part 3: Income Strategy Advice
- Should they start freelance NOW or skill up more?
- Best fast-income path based on their skills
- Best long-term career path
- Recommended first step

### Part 4: Skill Gap for Work
- Top 3 skills they must improve to unlock better jobs
- For each: importance, how to learn, time needed

### Part 5: High-Impact Project
- One project idea that increases employability
- What it demonstrates
- Why employers care
- Time to complete

## OUTPUT FORMAT:
Return valid JSON:
{{
    "work_readiness": {{
        "readiness_level": "freelance_ready | internship_ready | junior_ready | practice_first",
        "readiness_summary": "2-3 sentence assessment of their job market readiness",
        "strengths_for_work": ["Strength 1", "Strength 2", "Strength 3"],
        "gaps_to_address": ["Gap 1", "Gap 2"],
        "recommended_path": "What path they should take next"
    }},
    "job_recommendations": [
        {{
            "job_title": "Junior Data Analyst",
            "job_type": "junior",
            "why_it_fits": "Why this role matches their profile",
            "skills_they_have": ["Python", "SQL"],
            "missing_skills": ["Tableau", "Statistics"],
            "difficulty": "easy_entry",
            "time_to_ready": "1-2 months",
            "typical_tasks": ["Data cleaning", "Report generation"],
            "icon": "📊"
        }}
    ],
    "freelance_opportunities": [
        {{
            "gig_type": "Data Cleaning",
            "example_task": "Clean and organize a messy Excel dataset with 10,000 rows",
            "why_they_can_do_it": "They know Python/Pandas and have done data projects",
            "skills_required": ["Python", "Pandas", "Excel"],
            "platform_types": ["Freelance marketplaces", "Upwork-style platforms", "Direct clients"],
            "earning_potential": "$50-150/project",
            "difficulty": "easy_entry",
            "icon": "🧹"
        }}
    ],
    "income_strategy": {{
        "start_freelance_now": true,
        "freelance_reasoning": "Why they should or shouldn't start freelancing now",
        "fast_income_path": "The quickest way to start earning with current skills",
        "long_term_career_path": "Best career trajectory for their goals",
        "recommended_first_step": "What to do this week"
    }},
    "skill_gaps": [
        {{
            "skill_name": "SQL Advanced Queries",
            "importance": "Required for most data roles",
            "how_to_learn": "Practice on LeetCode SQL, build database projects",
            "time_to_learn": "2-3 weeks"
        }}
    ],
    "high_impact_project": {{
        "project_name": "End-to-End Data Pipeline",
        "description": "Build a project that collects, cleans, analyzes, and visualizes real data",
        "skills_demonstrated": ["Python", "SQL", "Data Visualization", "ETL"],
        "why_employers_care": "Shows ability to handle real-world data workflows",
        "estimated_time": "2-3 weeks"
    }},
    "immediate_actions": [
        "Action 1 - do this today",
        "Action 2 - do this week",
        "Action 3 - do this month"
    ]
}}

## IMPORTANT:
- Be SPECIFIC to their skills: {skills}
- Consider their level: {current_level}
- Match to their goal: {career_goal}
- Be realistic about what {current_level} level can get

Return ONLY valid JSON, no additional text.
"""


QUICK_JOB_CHECK_PROMPT = """Based on these skills: {skills}
And this career goal: {career_goal}
At {current_level} level

Give 3 most realistic job types they can apply for within 1-2 months.
Be specific and practical. No dream jobs.
"""


FREELANCE_FOCUS_PROMPT = """Analyze this student for FREELANCE opportunities only:

Skills: {skills}
Tools: {tools_known}
Projects Done: {projects_done}
Hours Available: {hours_per_week}/week
Level: {current_level}

Recommend 5 specific freelance gig types they can start doing NOW or within 2 weeks.
For each, give:
1. Gig type
2. Example task
3. Earning potential
4. Where to find clients (platform types)

Be realistic. Focus on what they can ACTUALLY do with current skills.
"""
