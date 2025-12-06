"""Core Detection Pipeline for Abnormality Detection"""
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18
import mediapipe as mp


class AbnormalityDetector:
    """Main detector class combining multiple detection models"""
    
    def __init__(self):
        """Initialize all detection models"""
        self.violence_threshold = 65
        self.fire_threshold = 65
        self.fall_threshold = 60
        
        # Load ResNet-18 for violence detection
        try:
            self.violence_model = resnet18(pretrained=True)
            self.violence_model.eval()
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.violence_model.to(self.device)
        except Exception as e:
            print(f'Warning: Could not load ResNet model: {e}')
            self.violence_model = None
        
        # Load MediaPipe Pose for fall detection
        try:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            print(f'Warning: Could not load MediaPipe: {e}')
            self.pose = None
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def detect_violence(self, frame):
        """Detect violence using entropy analysis on ResNet features"""
        try:
            if self.violence_model is None:
                return False, 0
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = transforms.ToPILImage()(rgb_frame)
            
            # Preprocess
            tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # Get features
            with torch.no_grad():
                features = self.violence_model(tensor)
            
            # Calculate entropy (measure of chaos/disorder)
            probs = torch.softmax(features, dim=1).cpu().numpy()
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            
            # Normalize entropy (0-100)
            confidence = min(100, max(0, entropy * 20))
            detected = confidence > self.violence_threshold
            
            return detected, confidence
        except Exception as e:
            print(f'Violence detection error: {e}')
            return False, 0
    
    def detect_fire(self, frame, prev_frame=None):
        """Detect fire using HSV color segmentation and motion analysis"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Define fire color range (red, orange, yellow)
            lower_fire = np.array([0, 100, 100])
            upper_fire = np.array([35, 255, 255])
            
            # Create mask
            mask = cv2.inRange(hsv, lower_fire, upper_fire)
            
            # Calculate fire color percentage
            total_pixels = mask.shape[0] * mask.shape[1]
            fire_pixels = cv2.countNonZero(mask)
            color_confidence = (fire_pixels / total_pixels) * 100
            
            # Motion analysis (flicker detection)
            motion_confidence = 0
            if prev_frame is not None:
                diff = cv2.absdiff(frame, prev_frame)
                motion_in_fire = cv2.bitwise_and(diff, diff, mask=mask)
                motion_intensity = np.mean(motion_in_fire)
                motion_confidence = min(100, motion_intensity)
            
            # Combine color and motion confidence
            confidence = (color_confidence * 0.6 + motion_confidence * 0.4)
            detected = confidence > self.fire_threshold
            
            return detected, confidence
        except Exception as e:
            print(f'Fire detection error: {e}')
            return False, 0
    
    def detect_fall(self, frame):
        """Detect falls using MediaPipe pose estimation"""
        try:
            if self.pose is None:
                return False, 0
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                return False, 0
            
            # Extract key landmarks
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape
            
            # Get positions
            nose = (landmarks[0].x * w, landmarks[0].y * h)
            left_shoulder = (landmarks[11].x * w, landmarks[11].y * h)
            right_shoulder = (landmarks[12].x * w, landmarks[12].y * h)
            left_hip = (landmarks[23].x * w, landmarks[23].y * h)
            right_hip = (landmarks[24].x * w, landmarks[24].y * h)
            
            # Calculate body orientation (vertical vs horizontal)
            shoulder_dist = abs(left_shoulder[0] - right_shoulder[0])
            hip_dist = abs(left_hip[0] - right_hip[0])
            body_width = max(shoulder_dist, hip_dist)
            
            # Check for vertical position
            avg_y = np.mean([landmarks[i].y for i in range(len(landmarks))])
            
            # Aspect ratio (width/height)
            body_height = abs(landmarks[0].y - landmarks[27].y) * h if landmarks[27].y > 0 else 1
            aspect_ratio = body_width / (body_height + 1e-5)
            
            # Fall detection logic
            is_horizontal = aspect_ratio > 1.5  # Lying down
            is_low = avg_y > 0.7  # Near ground
            
            confidence = 0
            if is_horizontal and is_low:
                confidence = min(100, aspect_ratio * 40)
            
            detected = confidence > self.fall_threshold
            return detected, confidence
        except Exception as e:
            print(f'Fall detection error: {e}')
            return False, 0
    
    def detect_all(self, frame):
        """Run all detections on frame"""
        results = {}
        any_detected = False
        
        # Violence detection
        v_detected, v_conf = self.detect_violence(frame)
        results['violence'] = {'detected': v_detected, 'confidence': v_conf}
        any_detected = any_detected or v_detected
        
        # Fire detection
        f_detected, f_conf = self.detect_fire(frame)
        results['fire'] = {'detected': f_detected, 'confidence': f_conf}
        any_detected = any_detected or f_detected
        
        # Fall detection
        f_d_detected, f_d_conf = self.detect_fall(frame)
        results['fall'] = {'detected': f_d_detected, 'confidence': f_d_conf}
        any_detected = any_detected or f_d_detected
        
        return any_detected, results
