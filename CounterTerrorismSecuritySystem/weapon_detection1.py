import cv2
import os
import time
import logging
from playsound import playsound
import smtplib
from email.message import EmailMessage
import geocoder
import numpy as np
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO)

# Paths configuration
weapon_images_folder = r"C:\Users\Aastha Chaurasia\OneDrive\Desktop\landing_page\weapon_images"
alert_sound_path = r"C:\Users\Aastha Chaurasia\OneDrive\Desktop\landing_page\alert.mp3"

# Email configuration
EMAIL_CONFIG = {
    'sender_email': "spiderabhay4321@gmail.com",
    'sender_password': "abcl cfhs giwm elvj",
    'recipient_email': "antiterroristgrop@gmail.com"
}

# Enhanced weapon detection setup
def load_weapon_templates(weapon_folder):
    weapons = []
    weapon_names = []
    valid_extensions = ('.jpg', '.jpeg', '.png', '.jfif')
    
    try:
        weapon_files = [f for f in os.listdir(weapon_folder) if f.lower().endswith(valid_extensions)]
        logging.info(f"Loaded {len(weapon_files)} weapon templates")
        
        for weapon_file in weapon_files:
            template = cv2.imread(os.path.join(weapon_folder, weapon_file), 0)  # Read as grayscale
            if template is not None:
                # Preprocess template
                template = cv2.equalizeHist(template)
                template = cv2.GaussianBlur(template, (3, 3), 0)
                weapons.append(template)
                weapon_names.append(os.path.splitext(weapon_file)[0])
                logging.info(f"Loaded weapon template: {weapon_file} (Size: {template.shape})")
            else:
                logging.warning(f"Could not load weapon template {weapon_file}")
                
        return weapons, weapon_names
    except Exception as e:
        logging.error(f"Error loading weapon templates: {e}")
        return [], []

def detect_weapons(frame, weapon_templates, weapon_names, threshold=0.55):
    detected_weapons = []
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.equalizeHist(gray_frame)
    gray_frame = cv2.GaussianBlur(gray_frame, (3, 3), 0)
    
    for template, name in zip(weapon_templates, weapon_names):
        try:
            # Multi-scale detection
            for scale in [0.7, 0.85, 1.0, 1.15, 1.3]:
                resized = cv2.resize(template, None, fx=scale, fy=scale)
                h, w = resized.shape
                
                # Skip if template is larger than frame
                if h > gray_frame.shape[0] or w > gray_frame.shape[1]:
                    continue
                    
                res = cv2.matchTemplate(gray_frame, resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                # Debug confidence values
                logging.debug(f"Testing {name} at scale {scale:.2f}: Max confidence = {max_val:.2f}")
                
                if max_val >= threshold:
                    detected_weapons.append({
                        'name': name,
                        'location': max_loc,
                        'template_size': (w, h),
                        'confidence': max_val
                    })
                    
        except Exception as e:
            logging.error(f"Error detecting weapon {name}: {e}")
    
    # Remove duplicate detections
    if detected_weapons:
        detected_weapons = sorted(detected_weapons, key=lambda x: x['confidence'], reverse=True)
        final_detections = []
        used_locations = []
        
        for det in detected_weapons:
            overlap = False
            for used in used_locations:
                dist = np.sqrt((det['location'][0] - used[0])**2 + (det['location'][1] - used[1])**2)
                if dist < max(det['template_size'][0], det['template_size'][1])/2:
                    overlap = True
                    break
            if not overlap:
                final_detections.append(det)
                used_locations.append(det['location'])
        
        return final_detections
    
    return detected_weapons

def send_alert(name, image_path, location, confidence):
    subject = f"Weapon Detected: {name} (Confidence: {confidence:.2f})"
    body = f"Alert: Weapon Detected!\n"
    body += f"Weapon Type: {name}\n"
    body += f"Confidence: {confidence:.2f}\n"
    body += f"Location: {location}\n"
    body += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    msg = EmailMessage()
    msg['From'] = EMAIL_CONFIG['sender_email']
    msg['To'] = EMAIL_CONFIG['recipient_email']
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with open(image_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='image', subtype='jpeg', filename=os.path.basename(image_path))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            logging.info(f"Alert sent for {name} (Confidence: {confidence:.2f})")
    except Exception as e:
        logging.error(f"Error sending alert email: {e}")

def play_alert_sound(sound_path):
    if os.path.exists(sound_path):
        try:
            playsound(sound_path)
        except Exception as e:
            logging.error(f"Error playing alert sound: {e}")
    else:
        logging.error(f"Alert sound file not found at {sound_path}")

def main():
    # Load weapon templates
    weapon_templates, weapon_names = load_weapon_templates(weapon_images_folder)
    
    if not weapon_templates:
        logging.error("No weapon templates loaded. Exiting.")
        return
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Could not open webcam.")
        return

    # Cooldown tracking
    last_alert_time = {}
    COOLDOWN_PERIOD = 60  # seconds
    detection_threshold = 0.55  # Initial threshold (adjust as needed)

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture frame.")
            break

        # Weapon detection
        detected_weapons = detect_weapons(frame, weapon_templates, weapon_names, detection_threshold)
        
        # Dynamic threshold adjustment
        if not detected_weapons and detection_threshold > 0.4:
            detection_threshold -= 0.02  # Lower threshold if no detections
        elif detected_weapons and detection_threshold < 0.7:
            detection_threshold += 0.01  # Increase threshold if detections
            
        for weapon in detected_weapons:
            name = weapon['name']
            top_left = weapon['location']
            bottom_right = (top_left[0] + weapon['template_size'][0], top_left[1] + weapon['template_size'][1])
            confidence = weapon['confidence']
            
            # Draw bounding box and info
            cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)
            cv2.putText(frame, f"{name} ({confidence:.2f})", (top_left[0], top_left[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Check cooldown
            current_time = time.time()
            if name not in last_alert_time or (current_time - last_alert_time[name] > COOLDOWN_PERIOD):
                last_alert_time[name] = current_time
                
                # Save image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"detected_weapon_{name}_{timestamp}.jpg"
                cv2.imwrite(image_path, frame)
                
                # Get location
                g = geocoder.ip('me')
                location = f"{g.latlng}" if g.latlng else "Location not available"
                
                # Alert
                play_alert_sound(alert_sound_path)
                send_alert(name, image_path, location, confidence)

        # Display threshold info
        cv2.putText(frame, f"Threshold: {detection_threshold:.2f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('Weapon Detection System', frame)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('+'):  # Increase threshold manually
            detection_threshold = min(0.9, detection_threshold + 0.05)
        elif key == ord('-'):  # Decrease threshold manually
            detection_threshold = max(0.3, detection_threshold - 0.05)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 