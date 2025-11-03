import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin not available - Firestore storage will not work")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirestoreService:
    """Service for interacting with Firestore database"""
    
    _app = None
    _db = None
    
    def __init__(self):
        """Initialize Firestore connection"""
        if not FIREBASE_AVAILABLE:
            raise ImportError("firebase-admin package is required. Install it with: pip install firebase-admin")
        
        self._initialize_firestore()
    
    def _initialize_firestore(self):
        """Initialize Firebase Admin SDK and Firestore client"""
        try:
            # Check if Firebase app is already initialized
            if FirestoreService._app is None:
                # Try to get credentials from environment variable (JSON string)
                cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                
                if cred_json:
                    # Remove any surrounding quotes and strip whitespace
                    cred_json = cred_json.strip()
                    # Remove outer quotes if present (single or double)
                    if (cred_json.startswith("'") and cred_json.endswith("'")):
                        cred_json = cred_json[1:-1]
                    elif (cred_json.startswith('"') and cred_json.endswith('"')):
                        cred_json = cred_json[1:-1]
                    
                    # Parse JSON string from environment variable
                    # python-dotenv should handle multi-line JSON correctly
                    try:
                        cred_dict = json.loads(cred_json)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
                        raise ValueError(f"Invalid JSON in FIREBASE_CREDENTIALS_JSON: {e}")
                    cred = credentials.Certificate(cred_dict)
                    logger.info("Using Firebase credentials from environment variable")
                else:
                    # Try to load from file
                    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
                    if os.path.exists(cred_path):
                        cred = credentials.Certificate(cred_path)
                        logger.info(f"Using Firebase credentials from file: {cred_path}")
                    else:
                        # Try default service account (for Google Cloud deployments)
                        cred = credentials.ApplicationDefault()
                        logger.info("Using default application credentials")
                
                FirestoreService._app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            
            # Initialize Firestore client
            if FirestoreService._db is None:
                FirestoreService._db = firestore.client()
                logger.info("Firestore client initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing Firestore: {e}")
            raise
    
    @property
    def db(self):
        """Get Firestore database client"""
        if FirestoreService._db is None:
            self._initialize_firestore()
        return FirestoreService._db
    
    # Sensor Data Methods
    def save_sensor_data(self, sensor_data: Dict[str, Any], document_id: Optional[str] = None) -> str:
        """Save sensor data to Firestore"""
        try:
            collection = self.db.collection('sensor_data')
            
            # Add timestamp if not present
            if 'timestamp' not in sensor_data:
                sensor_data['timestamp'] = datetime.utcnow().isoformat()
            
            if document_id:
                doc_ref = collection.document(document_id)
                doc_ref.set(sensor_data)
                logger.info(f"Sensor data saved to Firestore: {document_id}")
                return document_id
            else:
                # Auto-generate document ID
                doc_ref = collection.add(sensor_data)
                logger.info(f"Sensor data saved to Firestore: {doc_ref[1].id}")
                return doc_ref[1].id
                
        except Exception as e:
            logger.error(f"Error saving sensor data to Firestore: {e}")
            raise
    
    def get_sensor_data(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get sensor data by document ID"""
        try:
            doc_ref = self.db.collection('sensor_data').document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            else:
                logger.warning(f"Sensor data not found: {document_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting sensor data from Firestore: {e}")
            return None
    
    def query_sensor_data(self, 
                         farm_id: Optional[str] = None,
                         sensor_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Query sensor data with filters"""
        try:
            query = self.db.collection('sensor_data')
            
            if farm_id:
                query = query.where('farm_id', '==', farm_id)
            
            if sensor_id:
                # For single sensor data, check if sensor_data.sensor_id matches
                query = query.where('sensor_data.sensor_id', '==', sensor_id)
            
            if start_date:
                query = query.where('timestamp', '>=', start_date.isoformat())
            
            if end_date:
                query = query.where('timestamp', '<=', end_date.isoformat())
            
            # Order by timestamp descending and limit
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying sensor data from Firestore: {e}")
            return []
    
    # Prediction Methods
    def save_prediction(self, prediction_data: Dict[str, Any], document_id: Optional[str] = None) -> str:
        """Save prediction results to Firestore"""
        try:
            collection = self.db.collection('predictions')
            
            if 'timestamp' not in prediction_data:
                prediction_data['timestamp'] = datetime.utcnow().isoformat()
            
            if document_id:
                doc_ref = collection.document(document_id)
                doc_ref.set(prediction_data)
                return document_id
            else:
                doc_ref = collection.add(prediction_data)
                return doc_ref[1].id
                
        except Exception as e:
            logger.error(f"Error saving prediction to Firestore: {e}")
            raise
    
    def get_predictions(self, sensor_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get predictions for a sensor"""
        try:
            query = self.db.collection('predictions')
            
            if sensor_id:
                query = query.where('sensor_id', '==', sensor_id)
            
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting predictions from Firestore: {e}")
            return []
    
    # Feedback Methods
    def save_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Save feedback data to Firestore"""
        try:
            collection = self.db.collection('feedback')
            
            if 'timestamp' not in feedback_data:
                feedback_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Use feedback_id as document ID
            doc_id = feedback_data.get('feedback_id')
            if not doc_id:
                doc_id = f"feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                feedback_data['feedback_id'] = doc_id
            
            doc_ref = collection.document(doc_id)
            doc_ref.set(feedback_data)
            
            logger.info(f"Feedback saved to Firestore: {doc_id}")
            return doc_id
                
        except Exception as e:
            logger.error(f"Error saving feedback to Firestore: {e}")
            raise
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback by ID"""
        try:
            doc_ref = self.db.collection('feedback').document(feedback_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting feedback from Firestore: {e}")
            return None
    
    def query_feedback(self, 
                      rating_min: Optional[int] = None,
                      rating_max: Optional[int] = None,
                      limit: int = 50,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """Query feedback with filters"""
        try:
            query = self.db.collection('feedback')
            
            if rating_min is not None:
                query = query.where('user_rating', '>=', rating_min)
            
            if rating_max is not None:
                query = query.where('user_rating', '<=', rating_max)
            
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit + offset)
            
            docs = query.stream()
            results = []
            for i, doc in enumerate(docs):
                if i >= offset:  # Skip to offset
                    data = doc.to_dict()
                    data['id'] = doc.id
                    results.append(data)
            
            return results[:limit]  # Return only limit number
            
        except Exception as e:
            logger.error(f"Error querying feedback from Firestore: {e}")
            return []
    
    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get feedback analytics"""
        try:
            all_feedback = self.query_feedback(limit=1000)
            
            if not all_feedback:
                return {
                    'total_feedback': 0,
                    'average_rating': 0,
                    'rating_distribution': {},
                    'accuracy_rate': 0
                }
            
            total = len(all_feedback)
            ratings = [f.get('user_rating', 0) for f in all_feedback]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            rating_dist = {}
            for rating in range(1, 6):
                rating_dist[str(rating)] = len([r for r in ratings if r == rating])
            
            correct_count = len([f for f in all_feedback if f.get('is_correct') is True])
            accuracy_rate = correct_count / total if total > 0 else 0
            
            return {
                'total_feedback': total,
                'average_rating': round(avg_rating, 2),
                'rating_distribution': rating_dist,
                'accuracy_rate': round(accuracy_rate, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics from Firestore: {e}")
            return {}
    
    # Retraining Queue Methods
    def add_to_retraining_queue(self, feedback_data: Dict[str, Any]) -> str:
        """Add feedback to retraining queue"""
        try:
            collection = self.db.collection('retraining_queue')
            
            queue_item = {
                'feedback_id': feedback_data.get('feedback_id'),
                'queued_at': datetime.utcnow().isoformat(),
                'priority': 'high' if feedback_data.get('user_rating', 5) <= 2 else 'medium',
                'model_types': ['irrigation', 'crop_health', 'yield'],
                'processed': False
            }
            
            doc_ref = collection.add(queue_item)
            logger.info(f"Added to retraining queue: {doc_ref[1].id}")
            return doc_ref[1].id
            
        except Exception as e:
            logger.error(f"Error adding to retraining queue: {e}")
            raise
    
    def get_retraining_queue(self, unprocessed_only: bool = True) -> List[Dict[str, Any]]:
        """Get retraining queue items"""
        try:
            query = self.db.collection('retraining_queue')
            
            if unprocessed_only:
                query = query.where('processed', '==', False)
            
            query = query.order_by('queued_at', direction=firestore.Query.ASCENDING)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting retraining queue from Firestore: {e}")
            return []
    
    def save_retraining_log(self, log_data: Dict[str, Any]) -> str:
        """Save retraining log"""
        try:
            collection = self.db.collection('retraining_logs')
            
            if 'timestamp' not in log_data:
                log_data['timestamp'] = datetime.utcnow().isoformat()
            
            doc_ref = collection.add(log_data)
            return doc_ref[1].id
            
        except Exception as e:
            logger.error(f"Error saving retraining log to Firestore: {e}")
            raise
    
    def get_retraining_status(self) -> Dict[str, Any]:
        """Get retraining status"""
        try:
            queue = self.get_retraining_queue(unprocessed_only=True)
            
            # Get last retraining log
            last_logs = self.db.collection('retraining_logs')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(1)\
                .stream()
            
            last_retraining = None
            for log in last_logs:
                last_retraining = log.to_dict()
                break
            
            return {
                'active_jobs': len(queue),
                'pending_items': len(queue),
                'last_retraining': last_retraining,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting retraining status from Firestore: {e}")
            return {}

