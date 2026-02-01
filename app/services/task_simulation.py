from __future__ import annotations

import hashlib
from typing import Any

from app.models.schemas import (
    CompanyProfile,
    TaskContext,
    TaskOrigin,
    RoleInfo,
    TechnicalDetails,
    NonTechnicalRealities,
    MindsetComparison,
    SkillsTraining,
    FinalChallenge,
    TaskSimulationStructured,
)


# Egyptian Tech Companies Database
EGYPTIAN_TECH_COMPANIES = {
    "Vodafone Egypt": {
        "type": "Telecommunications",
        "size": "Large Enterprise",
        "focus": "Mobile services, IoT, digital payment solutions",
        "tech_stack": "Java, Python, Oracle, Kafka, Microservices",
        "challenges": "High transaction volume, real-time billing, network optimization"
    },
    "Orange Egypt": {
        "type": "Telecommunications",
        "size": "Large Enterprise", 
        "focus": "Telecom infrastructure, digital services, cloud solutions",
        "tech_stack": "Python, React, PostgreSQL, Docker, Kubernetes",
        "challenges": "Customer data analytics, service reliability, legacy system integration"
    },
    "Valeo Egypt": {
        "type": "Automotive Technology",
        "size": "Large Enterprise",
        "focus": "Automotive electronics, driver assistance systems, sensors",
        "tech_stack": "C++, Python, TensorFlow, embedded systems, real-time OS",
        "challenges": "Predictive maintenance, quality control, manufacturing automation"
    },
    "IBM Egypt": {
        "type": "Enterprise Technology",
        "size": "Large Enterprise",
        "focus": "Cloud computing, AI solutions, enterprise software",
        "tech_stack": "Java, Python, Node.js, Watson AI, IBM Cloud",
        "challenges": "Enterprise integration, security compliance, scalable architectures"
    },
    "Microsoft Egypt": {
        "type": "Software & Cloud",
        "size": "Large Enterprise",
        "focus": "Azure cloud, Office 365, enterprise solutions",
        "tech_stack": "C#, TypeScript, Azure, .NET, Power Platform",
        "challenges": "Multi-tenant systems, global scale, security & compliance"
    },
    "Swvl": {
        "type": "Transportation Tech Startup",
        "size": "Series C Startup",
        "focus": "Mass transit booking, route optimization, mobility platform",
        "tech_stack": "Python, Go, React Native, PostgreSQL, AWS",
        "challenges": "Route optimization algorithms, real-time tracking, payment processing"
    },
    "Instabug": {
        "type": "Developer Tools SaaS",
        "size": "Series B Startup",
        "focus": "Mobile app monitoring, bug reporting, crash analytics",
        "tech_stack": "Swift, Kotlin, JavaScript, Node.js, MongoDB, AWS",
        "challenges": "Real-time data processing, SDK optimization, multi-platform support"
    },
    "Fawry": {
        "type": "Fintech",
        "size": "Public Company",
        "focus": "Digital payment solutions, bill payment, e-commerce",
        "tech_stack": "Java, Spring Boot, Oracle, Redis, payment gateways",
        "challenges": "Transaction security, PCI compliance, high availability systems"
    },
    "Paymob": {
        "type": "Payment Processing",
        "size": "Series A Startup",
        "focus": "Online payment gateway, merchant solutions, financial APIs",
        "tech_stack": "Python, Django, React, PostgreSQL, Stripe API",
        "challenges": "Payment fraud detection, API reliability, merchant onboarding"
    },
    "Noon Academy": {
        "type": "EdTech",
        "size": "Series B Startup",
        "focus": "Online education, live classes, student engagement",
        "tech_stack": "React, Node.js, WebRTC, MongoDB, AWS",
        "challenges": "Video streaming quality, user engagement analytics, content delivery"
    },
    "Vezeeta": {
        "type": "HealthTech",
        "size": "Series C Startup",
        "focus": "Healthcare booking, telemedicine, patient management",
        "tech_stack": "C#, Angular, SQL Server, Azure, Twilio API",
        "challenges": "Patient data privacy, appointment scheduling, doctor-patient matching"
    },
    "Elmenus": {
        "type": "FoodTech",
        "size": "Series B Startup",
        "focus": "Restaurant discovery, food delivery, menu digitization",
        "tech_stack": "Python, Django, React, PostgreSQL, Google Cloud",
        "challenges": "Restaurant data accuracy, search optimization, delivery logistics"
    },
    "Dell Egypt": {
        "type": "Enterprise Hardware & Services",
        "size": "Large Enterprise",
        "focus": "IT infrastructure, enterprise solutions, support services",
        "tech_stack": "Python, Java, VMware, cloud platforms, automation tools",
        "challenges": "Supply chain optimization, customer support automation, inventory management"
    }
}


def _pick(options: list[str], seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(options)
    return options[index]


def _get_company_context(company_name: str) -> dict[str, str]:
    """Get realistic company context for Egyptian tech companies."""
    if company_name in EGYPTIAN_TECH_COMPANIES:
        return EGYPTIAN_TECH_COMPANIES[company_name]
    
    # Default context for unknown companies
    return {
        "type": "Technology Company",
        "size": "Mid-sized",
        "focus": "Software development and digital solutions",
        "tech_stack": "Python, JavaScript, SQL, Cloud platforms",
        "challenges": "Scaling systems, improving performance, user experience"
    }


def get_available_companies() -> list[dict[str, str]]:
    """Return list of all available Egyptian tech companies."""
    return [
        {
            "company_name": name,
            "type": info["type"],
            "size": info["size"],
            "focus": info["focus"]
        }
        for name, info in EGYPTIAN_TECH_COMPANIES.items()
    ]


def generate_task_simulation(company_name: str, task_title: str) -> TaskSimulationStructured:
    # Get company-specific context
    company_info = _get_company_context(company_name)
    
    # Egypt-specific business contexts
    overview_options = [
        f"{company_info['size']} {company_info['type']} in Egypt with focus on {company_info['focus']}. Operating in the Egyptian market with regional expansion plans.",
        f"Leading {company_info['type']} based in Cairo, Egypt. Known for {company_info['focus']} with a growing tech team.",
        f"Egyptian {company_info['type']} serving {company_info['size'].lower()} clients. Specializes in {company_info['focus']} with modern tech infrastructure.",
    ]
    
    users_options = [
        "Egyptian consumers, business clients across MENA, internal product and engineering teams.",
        "Local enterprises, government entities, retail customers, and regional B2B partners.",
        "Mobile app users in Egypt and MENA region, customer support teams, analytics and data teams.",
    ]
    
    problem_options = [
        f"System performance degraded during peak hours affecting customer experience in the Egyptian market. {company_info['challenges']} becoming critical.",
        f"Manual workflows causing delays in service delivery. Need automation aligned with {company_info['focus']}.",
        f"Data inconsistencies impacting business decisions. Quality issues in {company_info['challenges']} need resolution.",
        "Customer complaints increasing due to slow response times and outdated features. Market competition intensifying.",
        "Technical debt accumulating from rapid growth phase. System reliability concerns affecting business SLAs.",
    ]
    
    trigger_options = [
        "30% increase in customer support tickets during last month related to system slowness.",
        "Senior leadership requested immediate improvement after competitor launched superior features.",
        "Major client threatened to cancel contract due to recurring technical issues.",
        "Q4 growth targets at risk due to platform limitations and manual processes.",
        "Technical incident caused 2-hour downtime affecting thousands of Egyptian users.",
    ]
    
    constraints_options = [
        f"Limited to {company_info['tech_stack']} stack. 2-week sprint deadline for MVP. Legacy systems must remain operational.",
        "Budget constraints for new infrastructure. Must work within existing team capacity. Compliance with Egyptian data regulations.",
        "No downtime allowed during business hours (8 AM - 10 PM Cairo time). Gradual rollout required. Minimum viable scope for pilot.",
        "Dependency on third-party APIs with rate limits. Testing environment mirrors production partially. Documentation gaps in legacy code.",
    ]
    
    role_options = [
        "Software Engineering Intern",
        "Data Engineering Intern", 
        "Backend Development Intern",
        "ML Engineering Intern",
        "DevOps Engineering Intern",
        "Full Stack Development Intern",
    ]
    
    out_of_scope_options = [
        "Complete system redesign or migrating entire database. These require multi-quarter planning.",
        "Changing core business logic owned by other teams or affecting third-party integrations.",
        "Enterprise-wide rollout. Focus on pilot with 5-10% of users first.",
        "Rewriting frontend applications. Backend API improvement only for this phase.",
    ]
    
    data_issues_options = [
        "Data arrives with 2-4 hour delay from various sources. Missing fields in 15% of records. Arabic text encoding issues.",
        "User behavior tracking incomplete due to ad-blockers and privacy settings. Historical data only available for last 6 months.",
        "Multiple data formats (JSON, CSV, XML) from legacy systems. No unified schema. Documentation outdated.",
        "Real-time data feeds occasionally drop connections. Retry logic needed. Data validation rules not clearly documented.",
    ]
    
    egypt_specific_challenges = [
        "Consider Arabic language support and RTL layout if applicable.",
        "Account for Egyptian business hours and peak usage times (7-11 PM).",
        "Mobile-first approach essential - most users access via mobile in Egypt.",
        "Payment integration with local providers (Fawry, Paymob, etc.) if relevant.",
        "Connectivity issues - optimize for varying internet speeds across Egypt.",
    ]
    
    overview = _pick(overview_options, f"overview:{company_name}:{task_title}")
    users = _pick(users_options, f"users:{company_name}:{task_title}")
    problem = _pick(problem_options, f"problem:{company_name}:{task_title}")
    trigger = _pick(trigger_options, f"trigger:{company_name}:{task_title}")
    constraints = _pick(constraints_options, f"constraints:{company_name}:{task_title}")
    role_title = _pick(role_options, f"role:{company_name}:{task_title}")
    out_of_scope = _pick(out_of_scope_options, f"out-of-scope:{company_name}:{task_title}")
    data_issues = _pick(data_issues_options, f"data:{company_name}:{task_title}")
    egypt_challenge = _pick(egypt_specific_challenges, f"egypt:{company_name}:{task_title}")

    return TaskSimulationStructured(
        company=CompanyProfile(
            name=company_name,
            type=company_info["type"],
            size=company_info["size"],
            focus_areas=company_info["focus"],
            tech_stack=company_info["tech_stack"],
            key_challenges=company_info["challenges"],
        ),
        context=TaskContext(
            company_overview=overview,
            target_users=users,
            business_problem=problem,
            why_it_matters="The issue is impacting customer satisfaction, revenue growth, and competitive positioning in the Egyptian market. Urgent action needed to maintain market leadership.",
        ),
        origin=TaskOrigin(
            requested_by="Engineering Manager in collaboration with Product and Operations teams",
            trigger_event=trigger,
            requirement_quality="High-level requirements defined. Technical implementation details need to be proposed by engineering team. Stakeholders expect progress updates.",
            constraints=constraints,
            egypt_consideration=egypt_challenge,
        ),
        role=RoleInfo(
            job_title=role_title,
            responsibilities="Building the MVP implementation, documenting assumptions, and proposing a safe rollout plan.",
            out_of_scope=out_of_scope,
            collaborators="PMs, a senior engineer for review, an ops stakeholder, and a QA partner who is only available part-time.",
        ),
        technical=TechnicalDetails(
            task_description=f"Design and implement solution for: {task_title}. Follow company standards for {company_info['tech_stack']}. Integrate with existing systems and APIs.",
            data_inputs=f"{data_issues} Must handle Egyptian market data patterns and Arabic content where applicable.",
            expected_outputs=[
                "Working MVP demonstrating core functionality",
                "Technical documentation and deployment guide",
                "Test coverage for critical paths",
                "Performance benchmarks meeting SLA requirements",
            ],
            edge_cases=[
                "System degradation during peak hours (7-11 PM Cairo time)",
                "Partial data availability or third-party API failures",
                "Arabic/English bilingual content handling",
                "Network connectivity issues common in Egyptian infrastructure",
            ],
            performance_requirements=[
                "Must handle typical Egyptian user traffic patterns",
                "Response time < 2 seconds for 95th percentile",
                "Support concurrent users scaling to regional demand",
            ],
            integrations=f"{company_info['tech_stack']} ecosystem. Third-party services common in Egyptian market (payment gateways, SMS providers, etc.)",
            security_requirements=[
                "Comply with Egyptian data protection regulations",
                "Implement proper authentication and authorization",
                "Comprehensive logging for debugging and monitoring",
                "Error handling with user-friendly Arabic/English messages",
            ],
            deployment_expectations=[
                "Deploy to staging environment first",
                "Feature flags for gradual rollout",
                "Monitoring and alerting setup",
                "Rollback plan in case of issues",
            ],
        ),
        realities=NonTechnicalRealities(
            ambiguities=[
                "Requirements may evolve based on stakeholder feedback and market conditions in Egypt",
                "Success criteria need to be clarified with product and business teams",
                "Scope boundaries with other teams' responsibilities unclear initially",
            ],
            tradeoffs=[
                "Speed to market vs. perfect technical solution",
                "MVP feature set vs. comprehensive functionality",
                "Custom development vs. leveraging existing libraries/services",
                "Development time vs. testing coverage",
            ],
            decisions_with_incomplete_info=[
                "Technology choices when requirements are still being finalized",
                "Database schema design with partial data samples",
                "API design before all use cases are known",
                "Scaling strategy with estimated traffic projections",
            ],
            communication_challenges=[
                "Daily standups with distributed team members",
                "Technical explanations to non-technical stakeholders",
                "Coordinating with multiple teams (backend, frontend, QA, DevOps)",
                "Managing expectations on timeline and deliverables",
            ],
            business_pressure=[
                "Leadership wants demo for potential clients next sprint",
                "Marketing team needs features for upcoming campaign",
                "Competition launching similar features in Egyptian market",
                "Balancing technical debt with rapid delivery",
            ],
        ),
        mindset=MindsetComparison(
            student_approach=[
                "Focus on algorithms only",
                "Ignore data issues",
                "Assume perfect requirements",
                "Over-engineer or under-scope",
            ],
            professional_approach=[
                "Breaks the problem into deliverable phases",
                "Reduces risk early",
                "Communicates assumptions clearly",
                "Chooses pragmatic solutions",
                "Plans for iteration, not perfection",
            ],
        ),
        skills=SkillsTraining(
            technical_skills=[
                f"Proficiency in {company_info['tech_stack']}",
                "API design and RESTful principles",
                "Database design and optimization",
                "Testing strategies (unit, integration, E2E)",
                "Version control and collaborative development",
                "Cloud deployment and DevOps practices",
            ],
            system_design=[
                "Breaking complex problems into manageable components",
                "Designing scalable and maintainable architectures",
                "Handling edge cases and failure scenarios",
                "Performance optimization and monitoring",
                "Security considerations and data protection",
            ],
            decision_making=[
                "Prioritizing features for MVP scope",
                "Time-boxed delivery within sprint deadlines",
                "Quality vs. speed trade-offs",
                "Resource allocation and technical debt management",
            ],
            communication=[
                "Writing clear technical documentation",
                "Explaining technical concepts to non-technical stakeholders",
                "Code reviews and giving/receiving feedback",
                "Cross-team coordination and dependency management",
            ],
            handling_ambiguity=[
                "Iterative development and continuous refinement",
                "Stakeholder alignment and expectation management",
                "Adapting to market feedback and business needs",
                "Documenting assumptions and clarifying ambiguities",
            ],
            egypt_market=[
                "Understanding local user behavior and preferences",
                "Mobile-first development for Egyptian market",
                "Bilingual (Arabic/English) support considerations",
                "Local payment and service integrations",
                "Infrastructure constraints and optimization",
            ],
        ),
        challenge=FinalChallenge(
            timeline="2 weeks (10 working days) to deliver an MVP",
            deliverables=[
                "Working implementation demonstrating core functionality",
                "Technical design document explaining your approach",
                "Test suite covering critical scenarios",
                "Deployment guide and documentation",
                "15-minute presentation to stakeholders",
            ],
            key_questions=[
                "Why did you choose this technical approach?",
                "What are the key risks and how did you mitigate them?",
                "How does your solution handle Egyptian market requirements?",
                "What would you do differently with more time?",
                "How will you measure success?",
            ],
            success_criteria=[
                "MVP meets core functional requirements",
                "Code is clean, documented, and maintainable",
                "Solution demonstrates understanding of real-world constraints",
                "Clear communication of technical decisions and trade-offs",
            ],
        ),
        mvp_focus=[
            "Practical implementation skills",
            "Problem-solving under real constraints",
            "Clear technical communication",
            "Understanding business context",
            "Professional work habits",
        ],
        not_focus=[
            "Perfect production-ready code",
            "Advanced optimization",
            "Comprehensive feature set",
            "Complex architectural patterns",
        ],
        goal=f"Simulate realistic work at {company_name} in Egypt. Bridge gap between academic learning and Egyptian tech industry. Train engineers to think, communicate, and decide like professionals.",
    )
