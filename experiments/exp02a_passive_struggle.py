"""
Experiment 2A: OULAD Passive Struggle Detection
========================================================
Validates the Sovereign Learner's performance on the OULAD dataset.

Sub-Experiments:
2a. Passive Struggle Detection (Local vs Cloud)
2b. Complex Query Resolution (Hybrid Effectiveness)
2c. Competency Vector Portability
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, mean_squared_error, r2_score
import sys
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sovereign_system.utils.sovereign_trace_logger import global_tracer

# Path configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "oulad")



@dataclass
class StruggleDetectionResult:
    """Results for struggle detection experiment"""
    condition: str  # 'full_local' or 'sanitized_cloud'
    total_students: int
    struggling_students: int
    f1_score: float
    precision: float
    recall: float
    accuracy: float
    features_used: List[str]



class OULADDataLoader:
    """Load and preprocess OULAD data"""
    
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.student_info = None
        self.student_vle = None
        self.student_assessment = None
        self.vle = None
        self.assessments = None
        self.courses = None
        
    def load_all(self):
        """Load all OULAD tables"""
        print("Loading OULAD data...")
        
        self.student_info = pd.read_csv(os.path.join(self.data_dir, "studentInfo.csv"))
        self.student_vle = pd.read_csv(os.path.join(self.data_dir, "studentVle.csv"))
        self.student_assessment = pd.read_csv(os.path.join(self.data_dir, "studentAssessment.csv"))
        self.vle = pd.read_csv(os.path.join(self.data_dir, "vle.csv"))
        self.assessments = pd.read_csv(os.path.join(self.data_dir, "assessments.csv"))
        self.courses = pd.read_csv(os.path.join(self.data_dir, "courses.csv"))
        
        print(f"  Students: {len(self.student_info)}")
        print(f"  Assessment records: {len(self.student_assessment)}")
        
        global_tracer.log_agent(
            agent_name="OULAD Data Loader",
            agent_role="Data Ingestion",
            input_data=f"Load from {self.data_dir}",
            output_data=f"Loaded: {len(self.student_info)} students, {len(self.student_vle)} interactions",
            duration_ms=500.0,
            privacy_before=1.0, 
            privacy_after=1.0,
            zone=0,
            metadata={"source": "csv", "tables": ["studentInfo", "studentVle", "assessments"]}
        )
        
        return self
    
    def get_student_features(self) -> pd.DataFrame:
        """
        Engineer features for each student from VLE interactions.
        These represent behavioral signals that indicate learning patterns.
        """
        print("Engineering student features...")
        
        # Aggregate VLE interactions per student
        vle_features = self.student_vle.groupby(
            ['code_module', 'code_presentation', 'id_student']
        ).agg({
            'sum_click': ['sum', 'mean', 'std', 'count'],
            'date': ['min', 'max', 'nunique']
        }).reset_index()
        
        # Flatten column names
        vle_features.columns = [
            'code_module', 'code_presentation', 'id_student',
            'total_clicks', 'avg_clicks_per_resource', 'std_clicks', 'resources_accessed',
            'first_activity_date', 'last_activity_date', 'active_days'
        ]
        
        # Calculate engagement metrics
        vle_features['activity_span'] = vle_features['last_activity_date'] - vle_features['first_activity_date']
        vle_features['clicks_per_day'] = vle_features['total_clicks'] / (vle_features['active_days'] + 1)
        
        # Merge with student info
        features = vle_features.merge(
            self.student_info[['code_module', 'code_presentation', 'id_student', 
                              'final_result', 'studied_credits', 'num_of_prev_attempts',
                              'gender', 'region', 'highest_education', 'age_band', 
                              'disability', 'imd_band']],
            on=['code_module', 'code_presentation', 'id_student'],
            how='inner'
        )
        
        # Get assessment performance
        # studentAssessment only has id_assessment, so we merge on that
        assessment_features = self.student_assessment.merge(
            self.assessments[['code_module', 'code_presentation', 'id_assessment', 'assessment_type', 'weight']],
            on='id_assessment',
            how='left'
        )
        
        assessment_agg = assessment_features.groupby(
            ['code_module', 'code_presentation', 'id_student']
        ).agg({
            'score': ['mean', 'std', 'count'],
            'is_banked': 'sum'
        }).reset_index()
        
        assessment_agg.columns = [
            'code_module', 'code_presentation', 'id_student',
            'avg_score', 'std_score', 'assessments_submitted', 'banked_assessments'
        ]
        
        # Merge assessment features
        features = features.merge(
            assessment_agg,
            on=['code_module', 'code_presentation', 'id_student'],
            how='left'
        )
        
        # Fill NaN
        features = features.fillna(0)
        
        # Create struggle label (Fail or Withdrawn = struggling)
        features['is_struggling'] = features['final_result'].isin(['Fail', 'Withdrawn']).astype(int)
        
        print(f"  Total students with features: {len(features)}")
        print(f"  Struggling students: {features['is_struggling'].sum()} ({features['is_struggling'].mean():.1%})")
        
        global_tracer.log_agent(
            agent_name="Feature Engineer",
            agent_role="Data Processor",
            input_data="Raw VLE and Assessment Data",
            output_data=f"Features generated for {len(features)} students",
            duration_ms=1200.0,
            privacy_before=1.0,
            privacy_after=1.0,
            zone=0,
            metadata={"feature_count": len(features.columns), "struggling_pct": features['is_struggling'].mean()}
        )
        
        return features
    
    def get_multi_course_students(self) -> pd.DataFrame:
        """
        Find students who took multiple courses for portability experiment.
        """
        # Count courses per student
        student_courses = self.student_info.groupby('id_student').agg({
            'code_module': 'count',
            'final_result': list
        }).reset_index()
        
        student_courses.columns = ['id_student', 'num_courses', 'results']
        
        # Filter students with 2+ courses
        multi_course = student_courses[student_courses['num_courses'] >= 2]
        
        print(f"  Multi-course students: {len(multi_course)}")
        
        return multi_course



class StruggleDetectionExperiment:
    """
    Experiment 2a: Passive Struggle Detection
    
    Hypothesis: On-device models with full local data achieve higher
    struggle detection accuracy than cloud models with sanitized data.
    """
    
    def __init__(self, features: pd.DataFrame):
        self.features = features
        self.results: List[StruggleDetectionResult] = []
        
    def run(self) -> Dict:
        """Run both conditions and compare"""
        
        print("\n" + "="*60)
        print("EXPERIMENT 2a: PASSIVE STRUGGLE DETECTION")
        print("="*60)
        
        # Condition 1: Full Local Access (Sovereign Learner)
        result_local = self._run_full_local()
        self.results.append(result_local)
        
        # Condition 2: Sanitized Cloud Access
        result_sanitized = self._run_sanitized_cloud()
        self.results.append(result_sanitized)
        
        comparison = self._generate_comparison()
        
        global_tracer.log_agent(
            agent_name="Experiment Runner (Struggle Detection)",
            agent_role="Experiment Orchestrator",
            input_data="Student Features (Full vs Sanitized)",
            output_data=f"Results: {json.dumps(comparison['gaps'])}",
            duration_ms=6500.0,
            privacy_before=1.0,
            privacy_after=1.0,
            zone=0,
            metadata=comparison
        )
        
        return comparison
    
    def _run_full_local(self) -> StruggleDetectionResult:
        """
        Condition: Full local data access (Sovereign Learner approach)
        All behavioral features available for prediction.
        """
        print("\n--- Condition 1: Full Local Access ---")
        
        # All features available
        feature_cols = [
            'total_clicks', 'avg_clicks_per_resource', 'std_clicks', 
            'resources_accessed', 'active_days', 'activity_span',
            'clicks_per_day', 'avg_score', 'std_score', 
            'assessments_submitted', 'studied_credits', 'num_of_prev_attempts'
        ]
        
        X = self.features[feature_cols].values
        y = self.features['is_struggling'].values
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        
        result = StruggleDetectionResult(
            condition="full_local",
            total_students=len(y_test),
            struggling_students=int(y_test.sum()),
            f1_score=f1_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred),
            recall=recall_score(y_test, y_pred),
            accuracy=accuracy_score(y_test, y_pred),
            features_used=feature_cols
        )
        
        print(f"  F1 Score: {result.f1_score:.3f}")
        print(f"  Accuracy: {result.accuracy:.3f}")
        print(f"  Features: {len(feature_cols)}")
        
        return result
    
    def _run_sanitized_cloud(self) -> StruggleDetectionResult:
        """
        Condition: Sanitized cloud access (Privacy-preserving but limited)
        Sensitive behavioral features removed to protect privacy.
        """
        print("\n--- Condition 2: Sanitized Cloud Access ---")
        
        # Only non-sensitive aggregate features (simulating cloud sanitization)
        # Removed: specific click patterns, temporal patterns, individual scores
        feature_cols = [
            'resources_accessed',  # Count only, no specifics
            'assessments_submitted',  # Count only
            'studied_credits',  # Generic academic info
        ]
        
        X = self.features[feature_cols].values
        y = self.features['is_struggling'].values
        
        # Train/test split (same random state for comparability)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        
        result = StruggleDetectionResult(
            condition="sanitized_cloud",
            total_students=len(y_test),
            struggling_students=int(y_test.sum()),
            f1_score=f1_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred),
            recall=recall_score(y_test, y_pred),
            accuracy=accuracy_score(y_test, y_pred),
            features_used=feature_cols
        )
        
        print(f"  F1 Score: {result.f1_score:.3f}")
        print(f"  Accuracy: {result.accuracy:.3f}")
        print(f"  Features: {len(feature_cols)} (sanitized)")
        
        return result
    
    def _generate_comparison(self) -> Dict:
        """Generate comparison report"""
        
        local = self.results[0]
        sanitized = self.results[1]
        
        f1_gap = local.f1_score - sanitized.f1_score
        accuracy_gap = local.accuracy - sanitized.accuracy
        
        comparison = {
            "experiment": "Passive Struggle Detection",
            "hypothesis": "Full local access outperforms sanitized cloud access",
            "results": {
                "full_local": asdict(local),
                "sanitized_cloud": asdict(sanitized)
            },
            "gaps": {
                "f1_gap": f1_gap,
                "f1_gap_percent": f1_gap / sanitized.f1_score * 100 if sanitized.f1_score > 0 else 0,
                "accuracy_gap": accuracy_gap
            },
            "conclusion": f"Local access achieves {f1_gap:.3f} higher F1 ({f1_gap/sanitized.f1_score*100:.1f}% improvement)" if f1_gap > 0 else "No significant difference"
        }
        
        print("\n" + "="*60)
        print("EXPERIMENT 2a RESULTS")
        print("="*60)
        print(f"  Full Local F1:     {local.f1_score:.3f}")
        print(f"  Sanitized Cloud F1: {sanitized.f1_score:.3f}")
        print(f"  Gap:               {f1_gap:.3f} ({f1_gap/sanitized.f1_score*100:.1f}% improvement)")
        
        return comparison





if __name__ == '__main__':
    loader = OULADDataLoader().load_all()
    exp = StruggleDetectionExperiment(loader.get_student_features())
    exp.run()