import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class OULADDataLoader:
    """Standardized OULAD Data Loader for Research Experiments"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Try to find data dir relative to this file (up 3 levels: shared_utils -> experiments -> root)
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base_path, "data", "oulad")
        else:
            self.data_dir = data_dir
            
        self.student_info = None
        self.student_vle = None
        self.student_assessment = None
        self.vle = None
        self.assessments = None
        self.courses = None
        
    def load_all(self):
        """Load all OULAD tables"""
        print(f"Loading OULAD data from {self.data_dir}...")
        
        try:
            self.student_info = pd.read_csv(os.path.join(self.data_dir, "studentInfo.csv"))
            self.student_vle = pd.read_csv(os.path.join(self.data_dir, "studentVle.csv"))
            self.student_assessment = pd.read_csv(os.path.join(self.data_dir, "studentAssessment.csv"))
            self.vle = pd.read_csv(os.path.join(self.data_dir, "vle.csv"))
            self.assessments = pd.read_csv(os.path.join(self.data_dir, "assessments.csv"))
            self.courses = pd.read_csv(os.path.join(self.data_dir, "courses.csv"))
            
            print(f"  Successfully loaded {len(self.student_info)} students.")
            return self
        except Exception as e:
            print(f"  Error loading OULAD data: {str(e)}")
            return None
    
    def get_engineered_features(self) -> pd.DataFrame:
        """
        Engineers features for each student from VLE interactions.
        Consistent with EXP02 methodology.
        """
        if self.student_vle is None:
            self.load_all()
            
        # Aggregate VLE interactions per student
        vle_features = self.student_vle.groupby(
            ['code_module', 'code_presentation', 'id_student']
        ).agg({
            'sum_click': ['sum', 'mean', 'std', 'count'],
            'date': ['min', 'max', 'nunique']
        }).reset_index()
        
        vle_features.columns = [
            'code_module', 'code_presentation', 'id_student',
            'total_clicks', 'avg_clicks_per_resource', 'std_clicks', 'resources_accessed',
            'first_activity_date', 'last_activity_date', 'active_days'
        ]
        
        # Merge with student info
        features = vle_features.merge(
            self.student_info[['code_module', 'code_presentation', 'id_student', 'final_result', 'studied_credits']],
            on=['code_module', 'code_presentation', 'id_student'],
            how='inner'
        )
        
        # Get assessment performance
        assessment_features = self.student_assessment.merge(
            self.assessments[['id_assessment', 'code_module', 'code_presentation']],
            on='id_assessment',
            how='left'
        )
        
        assessment_agg = assessment_features.groupby(
            ['code_module', 'code_presentation', 'id_student']
        ).agg({'score': 'mean'}).reset_index()
        
        assessment_agg.columns = ['code_module', 'code_presentation', 'id_student', 'avg_score']
        
        # Final merge
        features = features.merge(
            assessment_agg,
            on=['code_module', 'code_presentation', 'id_student'],
            how='left'
        ).fillna(0)
        
        # Struggle label
        features['struggle_label'] = features['final_result'].isin(['Fail', 'Withdrawn']).astype(int)
        
        return features
