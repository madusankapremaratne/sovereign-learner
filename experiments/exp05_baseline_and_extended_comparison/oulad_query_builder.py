import random
import pandas as pd
from typing import List, Dict
from experiments.shared_utils.oulad_utils import OULADDataLoader

COURSE_DOMAINS = {
    "AAA": {
        "subject": "Social Sciences",
        "topic_pool": [
            "statistical analysis of survey data",
            "qualitative coding methodology",
            "literature review for social policy",
            "research ethics for human participants",
            "thematic analysis techniques"
        ]
    },
    "BBB": {
        "subject": "STEM Foundation",
        "topic_pool": [
            "mathematical modelling approaches",
            "data interpretation in scientific reports",
            "laboratory protocol documentation",
            "scientific writing for peer review",
            "experimental design methodology"
        ]
    },
    "CCC": {
        "subject": "Computing and IT",
        "topic_pool": [
            "algorithm implementation in Python",
            "database query optimisation",
            "software testing methodology",
            "network security protocols",
            "object-oriented design patterns"
        ]
    },
    "DDD": {
        "subject": "Engineering",
        "topic_pool": [
            "systems modelling and simulation",
            "signal processing techniques",
            "materials characterisation methods",
            "control system design",
            "engineering drawing standards"
        ]
    },
    "EEE": {
        "subject": "Education Studies",
        "topic_pool": [
            "assessment design for learning outcomes",
            "differentiated instruction strategies",
            "curriculum mapping methodology",
            "formative feedback techniques",
            "inclusive education practices"
        ]
    },
    "FFF": {
        "subject": "Health Sciences",
        "topic_pool": [
            "clinical data interpretation",
            "patient-centred care frameworks",
            "public health intervention design",
            "evidence-based practice methodology",
            "health outcomes measurement"
        ]
    },
    "GGG": {
        "subject": "Business and Economics",
        "topic_pool": [
            "financial modelling techniques",
            "market analysis frameworks",
            "strategic management methodology",
            "econometric analysis approaches",
            "organisational behaviour theory"
        ]
    }
}

class OULADQueryBuilder:
    def __init__(self, data_dir: str = None):
        self.loader = OULADDataLoader(data_dir)
        self.features = None

    def build(self, n: int = 50, seed: int = 42) -> List[Dict]:
        """
        Build a stratified n-query test set from real OULAD student records.
        """
        if self.features is None:
            self.features = self.loader.get_engineered_features()
            
        rng = random.Random(seed)
        queries = []
        
        modules = self.features['code_module'].unique()
        per_module = n // len(modules)
        
        for module in sorted(modules):
            module_df = self.features[self.features['code_module'] == module]
            
            # Split by struggle state
            struggling = module_df[module_df['struggle_label'] == 1]
            not_struggling = module_df[module_df['struggle_label'] == 0]
            
            n_each = per_module // 2
            
            # Sample with fixed seed
            s_sample = struggling.sample(n=min(n_each, len(struggling)), random_state=seed)
            ns_sample = not_struggling.sample(n=min(n_each, len(not_struggling)), random_state=seed)
            
            for _, row in pd.concat([s_sample, ns_sample]).iterrows():
                q = self._derive_query(row.to_dict(), seed)
                queries.append(q)
        
        # Top up if needed
        if len(queries) < n:
            remaining = self.features.sample(n=n - len(queries), random_state=seed)
            for _, row in remaining.iterrows():
                q = self._derive_query(row.to_dict(), seed)
                queries.append(q)
                
        return queries[:n]

    def _derive_query(self, student_row: dict, seed: int) -> dict:
        rng = random.Random(seed + hash(str(student_row['id_student'])) % 10000)
        
        module = student_row['code_module']
        domain_info = COURSE_DOMAINS.get(module, COURSE_DOMAINS['CCC'])
        topic = rng.choice(domain_info['topic_pool'])
        struggle = student_row['struggle_label']
        
        avg_score = student_row.get('avg_score', 55)
        total_clicks = student_row.get('total_clicks', 200)
        active_days = student_row.get('active_days', 10)
        
        if struggle == 1:
            templates = [
                f"I'm working on {topic} for my {domain_info['subject']} module and struggling with the core concepts. My average score is {avg_score:.0f}% and I've been active for {active_days} days. What should I focus on?",
                f"Can you help me understand {topic}? I have {module} module assessments coming up. I've accessed {total_clicks:.0f} resources but still feel unclear on the methodology.",
                f"I need help with {topic} in my {domain_info['subject']} course. My current score is {avg_score:.0f}% which is below passing. What are the key things I'm likely missing?"
            ]
        else:
            templates = [
                f"I'm studying {topic} as part of my {domain_info['subject']} module. Looking to go deeper than the course materials. What are the most important advanced concepts I should explore?",
                f"For my {module} module work on {topic}, I want to apply this to my assignment. What are current best practices and key references?",
                f"Can you explain the theoretical foundations behind {topic}? I'm doing well in my {domain_info['subject']} course and want to strengthen my conceptual understanding."
            ]
        
        query_text = rng.choice(templates)
        
        # Sensitive fields present
        sensitive_metadata = []
        if str(int(avg_score)) in query_text: sensitive_metadata.append({"field": "avg_score", "value": str(int(avg_score))})
        if str(int(total_clicks)) in query_text: sensitive_metadata.append({"field": "total_clicks", "value": str(int(total_clicks))})
        if str(int(active_days)) in query_text: sensitive_metadata.append({"field": "active_days", "value": str(int(active_days))})
        if module in query_text: sensitive_metadata.append({"field": "code_module", "value": module})
        
        return {
            "query_id": f"oulad_{student_row['id_student']}_{module}",
            "query": query_text,
            "student_id": student_row['id_student'],
            "module": module,
            "struggle_label": struggle,
            "sensitive_fields": sensitive_metadata,
            "domain": domain_info['subject']
        }
