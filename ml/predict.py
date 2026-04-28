"""
ml/predict.py - Safe model loading and prediction logic for hospital recommendation.
"""

import joblib
import os
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Absolute path handling for model loading
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, 'model.pkl')

def load_model():
    """Safely load the ML model from disk."""
    try:
        if not os.path.exists(MODEL_PATH):
            logger.error(f"ML model file not found at {MODEL_PATH}")
            return None
        
        model = joblib.load(MODEL_PATH)
        logger.info("ML Model Loaded Successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading ML model: {e}")
        return None

# Load model on module startup
ml_model = load_model()

def predict_hospital(features):
    """
    Predict hospital type based on features.
    features: list [severity, age, specialization_index]
    Returns dict: {'score': prediction, 'success': bool, 'error': str}
    """
    global ml_model
    
    if ml_model is None:
        # Retry loading if it failed initially
        ml_model = load_model()
        if ml_model is None:
            return {'success': False, 'error': 'ML model module not found'}
    
    try:
        # Expecting features as a 2D array for scikit-learn
        prediction = ml_model.predict([features])[0]
        # Mapping back to human-readable (simplified)
        mapping = {0: "General Clinic", 1: "Specialized Hospital", 2: "Emergency Center"}
        result = mapping.get(int(prediction), "Unknown")
        
        return {
            'success': True,
            'score': int(prediction),
            'recommended_hospital': result
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {'success': False, 'error': str(e)}
