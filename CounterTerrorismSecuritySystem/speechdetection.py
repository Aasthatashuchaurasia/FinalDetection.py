import speech_recognition as sr
import smtplib
from email.mime.text import MIMEText
from playsound import playsound
import time
import traceback
import difflib

# === Configuration ===
TRIGGER_PHRASES = [
    "allah hu akbar", "humla karna hai", "bomb lagana hai",
    "yeh jihad hai", "hamla tayyar hai", "bandook le kar aao",
    "mission shuru karo", "zehar milana hai", "taliban ke sath hain",
    "sab kuch barbaad kar do"
]

EMAIL_SENDER = "spiderabhay4321@gmail.com"
EMAIL_PASSWORD = "abcl cfhs giwm elvj"  # Make sure this is a valid Gmail App Password
EMAIL_RECEIVER = "antiterroristgrop@gmail.com"

ALERT_SOUND_PATH = "alert.mp3"
FUZZY_THRESHOLD = 0.8
PHRASE_TIME_LIMIT = 5

# === Email Alert Function ===
def send_email(detected_text):
    subject = "Alert: Suspicious Speech Detected"
    body = f"A suspicious phrase was detected by the Bionic Bird system:\n\n'{detected_text}'"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            print("[✓] Email sent successfully.")
    except Exception as e:
        print("[!] Failed to send email.")
        traceback.print_exc()


# === Voice Detection Function ===
def detect_voice():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as mic:
            print("🎙️ Listening started... Calibrating microphone.")
            recognizer.adjust_for_ambient_noise(mic, duration=2)

            while True:
                print("🎧 Listening for suspicious speech...")
                audio = recognizer.listen(mic, phrase_time_limit=PHRASE_TIME_LIMIT)

                try:
                    text = recognizer.recognize_google(audio).lower().strip()
                    print(f"[You said] ➤ {text}")

                    for phrase in TRIGGER_PHRASES:
                        if phrase in text:
                            print(f"[!!!] Trigger phrase detected: '{phrase}'")
                            playsound(ALERT_SOUND_PATH)
                            send_email(text)
                            time.sleep(5)
                            break
                        else:
                            # Fuzzy matching fallback
                            score = difflib.SequenceMatcher(None, phrase, text).ratio()
                            if score >= FUZZY_THRESHOLD:
                                print(f"[!!!] Fuzzy match (score={score:.2f}): '{phrase}'")
                                playsound(ALERT_SOUND_PATH)
                                send_email(text)
                                time.sleep(5)
                                break

                except sr.UnknownValueError:
                    print("[!] Could not understand audio.")
                except sr.RequestError as e:
                    print(f"[!] API error: {e}")

    except Exception:
        print("[!] Error initializing microphone:")
        traceback.print_exc()

# === Main Entry ===
if __name__ == "__main__":
    detect_voice()
