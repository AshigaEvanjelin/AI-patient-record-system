"""
ml/train_model.py - Script to train a RandomForestClassifier for hospital recommendation.
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

def train_and_save_model():
    # 1. Create Sample Dataset
    # Features: [Severity (1-10), Age, Specialization_Needed (0: General, 1: Cardio, 2: Neuro, 3: Ortho)]
    # Target: Hospital_Type (0: General Clinic, 1: Specialized Hospital, 2: Emergency Center)
    
    data = {
        'severity': [2, 8, 5, 9, 3, 7, 4, 10, 1, 6],
        'age': [25, 65, 40, 70, 20, 55, 30, 80, 15, 45],
        'specialization': [0, 1, 3, 2, 0, 1, 0, 2, 0, 3],
        'hospital_recommendation': [0, 1, 1, 2, 0, 1, 0, 2, 0, 1]
    }
    
    df = pd.DataFrame(data)
    
    X = df[['severity', 'age', 'specialization']]
    y = df['hospital_recommendation']
    
    # 2. Train Model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 3. Save Model
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'model.pkl')
    
    joblib.dump(model, model_path)
    print(f"[OK] Model trained and saved at {model_path}")

if __name__ == "__main__":
    train_and_save_model()
