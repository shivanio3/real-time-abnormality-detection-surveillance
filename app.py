"""Flask Web Application for Real-Time Abnormality Detection"""
import cv2
import os
import time
import traceback
from flask import Flask, render_template, Response, request, jsonify
from werkzeug.utils import secure_filename
from detector import AbnormalityDetector
from alert_system import AlertSystem

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize detector and alert system
detector = AbnormalityDetector()
alert = AlertSystem(
    sender_email=os.getenv('SENDER_EMAIL', 'your_email@gmail.com'),
    sender_pass=os.getenv('SENDER_PASS', 'your_app_password'),
    receiver_email=os.getenv('RECEIVER_EMAIL', 'recipient@gmail.com'),
    cooldown=90
)

# Global variables
use_webcam = True
video_path = None
cap = None
detect_on = False
current_results = {'violence': {}, 'fire': {}, 'fall': {}}
last_alert_time = {}


def open_capture():
    """Open video capture from webcam or uploaded video"""
    global cap, use_webcam, video_path
    if use_webcam:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        cap = cv2.VideoCapture(video_path)


def draw_overlay(frame, results):
    """Draw detection overlays on frame"""
    y = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    def draw_box(text, color):
        nonlocal y
        cv2.rectangle(frame, (10, y-20), (310, y+10), color, -1)
        cv2.putText(frame, text, (20, y), font, 0.6, (255, 255, 255), 2)
        y += 40
    
    # Draw detection status
    if results.get('violence', {}).get('detected', False):
        conf = results['violence']['confidence']
        draw_box(f'VIOLENCE: {conf:.1f}%', (0, 0, 255))
    
    if results.get('fire', {}).get('detected', False):
        conf = results['fire']['confidence']
        draw_box(f'FIRE: {conf:.1f}%', (0, 165, 255))
    
    if results.get('fall', {}).get('detected', False):
        conf = results['fall']['confidence']
        draw_box(f'FALL: {conf:.1f}%', (0, 255, 255))
    
    if not any(r.get('detected', False) for r in results.values()):
        draw_box('ALL CLEAR', (0, 180, 0))
    
    return frame


def send_emails_if_needed(frame, results):
    """Send email alerts when abnormalities detected"""
    try:
        if results.get('violence', {}).get('detected', False):
            alert.send('violence', frame, results['violence']['confidence'])
        if results.get('fire', {}).get('detected', False):
            alert.send('fire', frame, results['fire']['confidence'])
        if results.get('fall', {}).get('detected', False):
            alert.send('fall', frame, results['fall']['confidence'])
    except Exception as e:
        print(f'EMAIL ERROR: {e}')
        traceback.print_exc()


def frame_stream():
    """Generate video stream with detections"""
    global cap, current_results, detect_on
    frame_idx = 0
    
    while True:
        try:
            if cap is None or not cap.isOpened():
                open_capture()
                if cap is None or not cap.isOpened():
                    time.sleep(0.2)
                    continue
            
            ok, frame = cap.read()
            if not ok:
                if not use_webcam and cap is not None:
                    cap.release()
                    cap = None
                    print('INFO: Video ended, awaiting new upload.')
                    break
                time.sleep(0.02)
                continue
            
            frame = cv2.resize(frame, (640, 480))
            
            # Process every 3rd frame to reduce latency
            if detect_on and frame_idx % 3 == 0:
                abnormal, results = detector.detect_all(frame)
                current_results = results
                
                if abnormal:
                    send_emails_if_needed(frame, results)
            
            draw_overlay(frame, current_results)
            
            ret, buf = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(buf.tobytes())).encode() + b'\r\n\r\n' +
                   buf.tobytes() + b'\r\n')
            
            frame_idx += 1
        except Exception as e:
            traceback.print_exc()
            time.sleep(0.1)


@app.route('/')
def index():
    """Render dashboard"""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(frame_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/set_mode', methods=['POST'])
def set_mode():
    """Set detection mode (webcam or video)"""
    global use_webcam, cap
    data = request.get_json(force=True)
    mode = data.get('mode', 'webcam')
    use_webcam = (mode == 'webcam')
    
    if cap:
        cap.release()
        cap = None
    
    return jsonify({'ok': True, 'mode': 'webcam' if use_webcam else 'video'})


@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Upload video file"""
    global video_path, use_webcam, cap
    
    if 'video' not in request.files:
        return jsonify({'error': 'No file provided'}, 400)
    
    f = request.files['video']
    if f.filename == '':
        return jsonify({'error': 'Empty filename'}, 400)
    
    safe = secure_filename(f.filename)
    p = os.path.join(app.config['UPLOAD_FOLDER'], safe)
    f.save(p)
    
    video_path = p
    use_webcam = False
    
    if cap:
        cap.release()
    
    return jsonify({'ok': True, 'path': safe})


@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start abnormality detection"""
    global detect_on
    detect_on = True
    return jsonify({'ok': True})


@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    """Stop abnormality detection"""
    global detect_on
    detect_on = False
    return jsonify({'ok': True})


@app.route('/results')
def results():
    """Get current detection results"""
    return jsonify(current_results)


if __name__ == '__main__':
    print('\n' + '='*60)
    print('Real-Time Abnormality Detection System')
    print('='*60)
    print('Open http://127.0.0.1:5000 in your browser')
    print('='*60 + '\n')
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
