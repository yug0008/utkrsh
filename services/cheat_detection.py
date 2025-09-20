import cv2
import numpy as np
from typing import Dict, Any
import logging
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

async def detect_cheating(video_url: str) -> Dict[str, Any]:
    """
    Detect potential cheating in sports videos using various techniques
    """
    try:
        # Download and process video
        video_path = await download_video(video_url)  # Reuse from ai_analysis
        frames = extract_frames(video_path)
        
        # Perform various cheat detection analyses
        frame_duplication = detect_frame_duplication(frames)
        unnatural_movement = detect_unnatural_movement(frames)
        speed_analysis = analyze_movement_speed(frames)
        
        # Combine results
        is_cheating = frame_duplication["is_duplicated"] or unnatural_movement["is_unnatural"]
        
        return {
            "is_cheating_detected": is_cheating,
            "confidence": max(frame_duplication["confidence"], unnatural_movement["confidence"]),
            "detected_anomalies": frame_duplication["anomalies"] + unnatural_movement["anomalies"],
            "frames_analyzed": len(frames),
            "duplicate_frames": frame_duplication["duplicate_count"]
        }
        
    except Exception as e:
        logger.error(f"Cheat detection failed: {str(e)}")
        return {
            "is_cheating_detected": False,
            "confidence": 0.0,
            "detected_anomalies": ["Analysis failed"],
            "frames_analyzed": 0,
            "duplicate_frames": 0
        }

def extract_frames(video_path: str, frame_interval: int = 5) -> list:
    """Extract frames from video at specified intervals"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            # Resize and convert to grayscale for efficiency
            frame = cv2.resize(frame, (224, 224))
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray_frame)
        
        frame_count += 1
    
    cap.release()
    return frames

def detect_frame_duplication(frames: list, threshold: float = 0.95) -> Dict[str, Any]:
    """Detect duplicate or very similar frames that might indicate tampering"""
    if len(frames) < 2:
        return {
            "is_duplicated": False,
            "confidence": 0.0,
            "duplicate_count": 0,
            "anomalies": []
        }
    
    duplicates = 0
    anomalies = []
    
    # Compare consecutive frames
    for i in range(1, len(frames)):
        # Calculate similarity between frames
        similarity = calculate_frame_similarity(frames[i-1], frames[i])
        
        if similarity > threshold:
            duplicates += 1
            anomalies.append(f"Frames {i-1} and {i} are {similarity*100:.1f}% similar")
    
    is_duplicated = duplicates > (len(frames) * 0.1)  # More than 10% duplicates
    
    return {
        "is_duplicated": is_duplicated,
        "confidence": min(duplicates / len(frames), 1.0),
        "duplicate_count": duplicates,
        "anomalies": anomalies
    }

def calculate_frame_similarity(frame1, frame2) -> float:
    """Calculate similarity between two frames using histogram comparison"""
    hist1 = cv2.calcHist([frame1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([frame2], [0], None, [256], [0, 256])
    
    # Normalize histograms
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
    
    # Calculate correlation
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return max(similarity, 0)  # Ensure non-negative

def detect_unnatural_movement(frames: list) -> Dict[str, Any]:
    """Detect unnatural movement patterns that might indicate CGI or manipulation"""
    # This is a simplified implementation
    movement_changes = []
    anomalies = []
    
    # Calculate optical flow between consecutive frames
    for i in range(1, len(frames)):
        flow = calculate_optical_flow(frames[i-1], frames[i])
        movement_changes.append(np.mean(flow))
    
    # Analyze movement patterns for anomalies
    if len(movement_changes) > 1:
        mean_movement = np.mean(movement_changes)
        std_movement = np.std(movement_changes)
        
        # Detect outliers in movement patterns
        for i, movement in enumerate(movement_changes):
            if abs(movement - mean_movement) > 2 * std_movement:
                anomalies.append(f"Unnatural movement detected between frames {i} and {i+1}")
    
    return {
        "is_unnatural": len(anomalies) > 0,
        "confidence": min(len(anomalies) / len(movement_changes), 1.0) if movement_changes else 0.0,
        "anomalies": anomalies
    }

def calculate_optical_flow(prev_frame, next_frame):
    """Calculate optical flow between two frames"""
    flow = cv2.calcOpticalFlowFarneback(
        prev_frame, next_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0
    )
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    return magnitude

def analyze_movement_speed(frames: list) -> Dict[str, Any]:
    """Analyze movement speed consistency"""
    # Placeholder implementation
    return {
        "average_speed": 0.0,
        "speed_consistency": 0.0,
        "anomalies": []
    }
