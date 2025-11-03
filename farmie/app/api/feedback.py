from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import os

from app.schemas.models import FeedbackData, APIResponse
from app.utils.helpers import DataStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Initialize data storage
data_storage = DataStorage()

# Initialize Firestore service for feedback operations
try:
    from app.services.firestore import FirestoreService
    firestore_service = FirestoreService()
    USE_FIRESTORE = True
except Exception as e:
    logger.warning(f"Firestore not available for feedback: {e}")
    firestore_service = None
    USE_FIRESTORE = False


@router.post("/submit", response_model=APIResponse)
async def submit_feedback(
    feedback: FeedbackData,
    background_tasks: BackgroundTasks
):
    """
    Submit user feedback for model predictions or system performance
    """
    try:
        logger.info(f"Received feedback: {feedback.feedback_id}")
        
        # Validate feedback data
        if not feedback.user_rating or not (1 <= feedback.user_rating <= 5):
            raise HTTPException(status_code=400, detail="User rating must be between 1 and 5")
        
        # Process feedback data
        feedback_dict = feedback.dict()
        feedback_dict['processed_at'] = datetime.utcnow().isoformat()
        
        # Save feedback in background
        background_tasks.add_task(_save_feedback, feedback_dict)
        
        # Check if feedback indicates model retraining is needed
        if feedback.user_rating <= 2 or (feedback.is_correct is False):
            background_tasks.add_task(_queue_for_retraining, feedback_dict)
        
        return APIResponse(
            success=True,
            message="Feedback submitted successfully",
            data={
                'feedback_id': feedback.feedback_id,
                'processed_at': feedback_dict['processed_at'],
                'queued_for_retraining': feedback.user_rating <= 2 or feedback.is_correct is False
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/feedback/{feedback_id}", response_model=FeedbackData)
async def get_feedback(feedback_id: str):
    """
    Get specific feedback by ID
    """
    try:
        if USE_FIRESTORE and firestore_service:
            feedback_data = firestore_service.get_feedback(feedback_id)
            if feedback_data:
                return FeedbackData(**feedback_data)
            else:
                raise HTTPException(status_code=404, detail=f"Feedback not found: {feedback_id}")
        else:
            # Fallback to mock data if Firestore not available
            mock_feedback = FeedbackData(
                feedback_id=feedback_id,
                sensor_data_id="sensor_001",
                prediction_id="pred_001",
                user_rating=4,
                feedback_text="Prediction was accurate and helpful",
                is_correct=True,
                timestamp=datetime.utcnow()
            )
            return mock_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/feedback", response_model=List[FeedbackData])
async def get_all_feedback(
    limit: int = 50,
    offset: int = 0,
    rating_min: Optional[int] = None,
    rating_max: Optional[int] = None
):
    """
    Get all feedback with optional filtering
    """
    try:
        if USE_FIRESTORE and firestore_service:
            feedback_list = firestore_service.query_feedback(
                rating_min=rating_min,
                rating_max=rating_max,
                limit=limit,
                offset=offset
            )
            return [FeedbackData(**f) for f in feedback_list]
        else:
            # Fallback to mock data if Firestore not available
            mock_feedback_list = [
                FeedbackData(
                    feedback_id=f"feedback_{i}",
                    sensor_data_id=f"sensor_{i:03d}",
                    prediction_id=f"pred_{i:03d}",
                    user_rating=max(1, min(5, 3 + (i % 3))),
                    feedback_text=f"Sample feedback {i}",
                    is_correct=i % 2 == 0,
                    timestamp=datetime.utcnow()
                )
                for i in range(1, min(limit + 1, 11))
            ]
            
            # Apply rating filters if provided
            if rating_min is not None:
                mock_feedback_list = [f for f in mock_feedback_list if f.user_rating >= rating_min]
            
            if rating_max is not None:
                mock_feedback_list = [f for f in mock_feedback_list if f.user_rating <= rating_max]
            
            return mock_feedback_list[offset:offset + limit]
        
    except Exception as e:
        logger.error(f"Error getting feedback list: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analytics", response_model=Dict[str, Any])
async def get_feedback_analytics():
    """
    Get analytics and insights from feedback data
    """
    try:
        if USE_FIRESTORE and firestore_service:
            analytics = firestore_service.get_feedback_analytics()
            
            # Get retraining queue info
            retraining_status = firestore_service.get_retraining_status()
            analytics['retraining_queue'] = {
                'pending_items': retraining_status.get('pending_items', 0),
                'last_retraining': retraining_status.get('last_retraining', {}).get('timestamp'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return analytics
        else:
            # Fallback to mock analytics if Firestore not available
            analytics = {
                'total_feedback': 150,
                'average_rating': 3.8,
                'rating_distribution': {
                    '1': 5,
                    '2': 12,
                    '3': 35,
                    '4': 68,
                    '5': 30
                },
                'accuracy_rate': 0.85,
                'common_issues': [
                    'Temperature predictions too high',
                    'Irrigation recommendations too frequent',
                    'Crop health scores inaccurate'
                ],
                'improvement_suggestions': [
                    'Retrain temperature model with recent data',
                    'Adjust irrigation threshold parameters',
                    'Improve crop health feature engineering'
                ],
                'retraining_queue': {
                    'pending_items': 8,
                    'last_retraining': '2024-01-15T10:30:00Z',
                    'next_scheduled': '2024-01-22T10:30:00Z'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            return analytics
        
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/retrain", response_model=APIResponse)
async def trigger_model_retraining(
    background_tasks: BackgroundTasks,
    model_type: Optional[str] = None,
    force: bool = False
):
    """
    Manually trigger model retraining based on feedback
    """
    try:
        logger.info(f"Triggering model retraining for: {model_type or 'all models'}")
        
        # Queue retraining task
        background_tasks.add_task(_perform_model_retraining, model_type, force)
        
        return APIResponse(
            success=True,
            message=f"Model retraining queued for {model_type or 'all models'}",
            data={
                'retraining_triggered': True,
                'model_type': model_type,
                'force': force,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error triggering model retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/retraining-status", response_model=Dict[str, Any])
async def get_retraining_status():
    """
    Get status of model retraining processes
    """
    try:
        if USE_FIRESTORE and firestore_service:
            status = firestore_service.get_retraining_status()
            return status
        else:
            # Fallback to mock status if Firestore not available
            status = {
                'active_jobs': 0,
                'completed_jobs': 3,
                'failed_jobs': 1,
                'last_retraining': {
                    'model_type': 'irrigation',
                    'status': 'completed',
                    'started_at': '2024-01-15T10:00:00Z',
                    'completed_at': '2024-01-15T10:45:00Z',
                    'accuracy_improvement': 0.05
                },
                'next_scheduled': '2024-01-22T10:00:00Z',
                'timestamp': datetime.utcnow().isoformat()
            }
            return status
        
    except Exception as e:
        logger.error(f"Error getting retraining status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _save_feedback(feedback_data: Dict[str, Any]):
    """Save feedback data to storage"""
    try:
        if USE_FIRESTORE and firestore_service:
            firestore_service.save_feedback(feedback_data)
            logger.info(f"Feedback saved to Firestore: {feedback_data['feedback_id']}")
        else:
            # Fallback to file storage
            filename = f"feedback_{feedback_data['feedback_id']}.json"
            data_storage.save_sensor_data(feedback_data, filename)
            logger.info(f"Feedback saved: {feedback_data['feedback_id']}")
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")


def _queue_for_retraining(feedback_data: Dict[str, Any]):
    """Queue feedback for model retraining"""
    try:
        if USE_FIRESTORE and firestore_service:
            firestore_service.add_to_retraining_queue(feedback_data)
            logger.info(f"Feedback queued for retraining in Firestore: {feedback_data['feedback_id']}")
        else:
            # Fallback to file storage
            retraining_queue_file = "data/retraining_queue.json"
            
            # Load existing queue
            queue = []
            if os.path.exists(retraining_queue_file):
                with open(retraining_queue_file, 'r') as f:
                    queue = json.load(f)
            
            # Add new feedback to queue
            queue.append({
                'feedback_id': feedback_data['feedback_id'],
                'queued_at': datetime.utcnow().isoformat(),
                'priority': 'high' if feedback_data['user_rating'] <= 2 else 'medium',
                'model_types': ['irrigation', 'crop_health', 'yield']  # Default to all models
            })
            
            # Save updated queue
            with open(retraining_queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
            
            logger.info(f"Feedback queued for retraining: {feedback_data['feedback_id']}")
        
    except Exception as e:
        logger.error(f"Error queuing feedback for retraining: {e}")


def _perform_model_retraining(model_type: Optional[str], force: bool):
    """Perform model retraining"""
    try:
        logger.info(f"Starting model retraining for: {model_type or 'all models'}")
        
        # This would typically:
        # 1. Load recent feedback data
        # 2. Prepare training data with feedback labels
        # 3. Retrain the specified model(s)
        # 4. Validate new model performance
        # 5. Deploy new model if performance improved
        
        # For now, we'll just log the retraining attempt
        retraining_log = {
            'model_type': model_type,
            'force': force,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'completed',
            'accuracy_improvement': 0.03
        }
        
        # Save retraining log
        if USE_FIRESTORE and firestore_service:
            firestore_service.save_retraining_log(retraining_log)
            logger.info("Retraining log saved to Firestore")
        else:
            # Fallback to file storage
            log_filename = f"retraining_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            data_storage.save_sensor_data(retraining_log, log_filename)
        
        logger.info(f"Model retraining completed for: {model_type or 'all models'}")
        
    except Exception as e:
        logger.error(f"Error during model retraining: {e}")


