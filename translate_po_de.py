import os
import re

def translate_po_content(content, translations):
    lines = content.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('msgid "'):
            msgid_lines = []
            curr_line = line[7:-2]
            msgid_lines.append(curr_line)
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                msgid_lines.append(lines[j][1:-2])
                j += 1
            
            msgid = "".join(msgid_lines)
            
            # Skip empty msgid (header)
            if not msgid:
                for k in range(i, j):
                    new_lines.append(lines[k])
                i = j
                continue

            # Look for msgstr ""
            msgstr_index = -1
            k = j
            while k < len(lines) and not (lines[k].startswith('msgid') or lines[k].strip() == ""):
                if lines[k].startswith('msgstr ""'):
                    msgstr_index = k
                    break
                k += 1
            
            if msgstr_index != -1 and msgid in translations:
                # Replace msgstr "" with translated
                lines[msgstr_index] = f'msgstr "{translations[msgid]}"\n'
            
            # Append everything from i to the end of this block
            # Actually, just append until the next msgid or empty line
            for k in range(i, msgstr_index if msgstr_index != -1 else j):
                new_lines.append(lines[k])
            
            if msgstr_index != -1:
                new_lines.append(lines[msgstr_index])
                i = msgstr_index + 1
            else:
                i = j
        else:
            new_lines.append(line)
            i += 1
    return "".join(new_lines)

# Translations for German
de_translations = {
    "English": "Englisch",
    "Mandarin Chinese": "Mandarin-Chinesisch",
    "Hindi": "Hindi",
    "Spanish": "Spanisch",
    "Arabic": "Arabisch",
    "French": "Französisch",
    "Bengali": "Bengali",
    "Portuguese": "Portugiesisch",
    "Russian": "Russisch",
    "Urdu": "Urdu",
    "Indonesian": "Indonesisch",
    "German": "Deutsch",
    "Japanese": "Japanisch",
    "Marathi": "Marathi",
    "Telugu": "Telugu",
    "Turkish": "Türkisch",
    "Tamil": "Tamil",
    "Vietnamese": "Vietnamesisch",
    "Cantonese": "Kantonesisch",
    "Swahili": "Suaheli",
    "Password and Confirm Password are required": "Passwort und Passwortbestätigung sind erforderlich",
    "Password and Confirm Password does not match": "Passwort und Passwortbestätigung stimmen nicht überein",
    "Username is required": "Benutzername ist erforderlich",
    "Email is already in use": "E-Mail wird bereits verwendet",
    "Username is already in use": "Benutzername wird bereits verwendet",
    "User with this email does not exist": "Benutzer mit dieser E-Mail existiert nicht",
    "Invalid verification code": "Ungültiger Verifizierungscode",
    "Verification code has expired": "Verifizierungscode ist abgelaufen",
    "Invalid email or password": "Ungültige E-Mail oder Passwort",
    "Account is not activated": "Konto ist nicht aktiviert",
    "Email is required.": "E-Mail ist erforderlich.",
    "Email, code, and password are required.": "E-Mail, Code und Passwort sind erforderlich.",
    "User registered successfully. Please check your email for the verification code.": "Benutzer erfolgreich registriert. Bitte überprüfen Sie Ihre E-Mail auf den Verifizierungscode.",
    "Account activated successfully.": "Konto erfolgreich aktiviert.",
    "User logged out successfully.": "Benutzer erfolgreich abgemeldet.",
    "Email not found in Google token": "E-Mail im Google-Token nicht gefunden",
    "No account found with this email.": "Kein Konto mit dieser E-Mail gefunden.",
    "OTP sent successfully to your email": "OTP erfolgreich an Ihre E-Mail gesendet",
    "User not available on this email": "Benutzer unter dieser E-Mail nicht verfügbar",
    "Invalid OTP": "Ungültiges OTP",
    "OTP expired": "OTP abgelaufen",
    "Password reset successfully": "Passwort erfolgreich zurückgesetzt",
    "Credit account not found.": "Guthabenkonto nicht gefunden.",
    "Reward must be greater than zero": "Belohnung muss größer als Null sein",
    "You have exceeded your daily limit. Please watch ads or buy a subscription for more requests.": "Sie haben Ihr tägliches Limit überschritten. Bitte sehen Sie sich Werbung an oder kaufen Sie ein Abonnement für weitere Anfragen.",
    "no available session found": "keine verfügbare Sitzung gefunden",
    "Voice transcription failed: {}": "Sprachtranskription fehlgeschlagen: {}",
    "Voice transcription returned empty response": "Sprachtranskription gab eine leere Antwort zurück",
    "Voice transcription error: {}": "Sprachtranskriptionsfehler: {}",
    "Unknown media link. Please select an image or video.": "Unbekannter Medienlink. Bitte wählen Sie ein Bild oder Video aus.",
    "Please type a message to receive assistance.": "Bitte geben Sie eine Nachricht ein, um Unterstützung zu erhalten.",
    "Only free model is available for free users. Please upgrade/buy coins to access premium models.": "Für kostenlose Benutzer ist nur das kostenlose Modell verfügbar. Bitte upgraden Sie oder kaufen Sie Münzen, um auf Premium-Modelle zuzugreifen.",
    "Error: {}": "Fehler: {}",
    "Only free model is available for free users. Please upgrade to access premium models.": "Für kostenlose Benutzer ist nur das kostenlose Modell verfügbar. Bitte upgraden Sie, um auf Premium-Modelle zuzugreifen.",
    "This model does not support chat": "Dieses Modell unterstützt keinen Chat",
    "Video generated successfully.": "Video erfolgreich generiert.",
    "Image tool requires an image. Please upload an image first.": "Das Bild-Tool erfordert ein Bild. Bitte laden Sie zuerst ein Bild hoch.",
    "User not found": "Benutzer nicht gefunden",
    "Credit account not found": "Guthabenkonto nicht gefunden",
    "Insufficient credits. Required: {}": "Unzureichendes Guthaben. Erforderlich: {}",
    "Insufficient credits for any response.": "Unzureichendes Guthaben für eine Antwort.",
    "Authentication failed: Invalid API key or configuration.": "Authentifizierung fehlgeschlagen: Ungültiger API-Schlüssel oder Konfiguration.",
    "API error. Please try again later.": "API-Fehler. Bitte versuchen Sie es später noch einmal.",
    "System error occurred.": "Ein Systemfehler ist aufgetreten.",
    "Insufficient credits": "Unzureichendes Guthaben",
    "Video generation timeout after {max_wait_time}s": "Video-Generierungs-Zeitüberschreitung nach {max_wait_time}s",
    "Video generation failed: {}": "Video-Generierung fehlgeschlagen: {}",
    "No videos generated": "Keine Videos generiert",
    "Failed to extract video bytes": "Video-Bytes konnten nicht extrahiert werden",
    "User not found.": "Benutzer nicht gefunden.",
    "Insufficient credits. Required: {charge_amount}": "Unzureichendes Guthaben. Erforderlich: {charge_amount}",
    "Insufficient credits for response.": "Unzureichendes Guthaben für die Antwort.",
    "{} image(s) generated successfully.": "{} Bild(er) erfolgreich generiert.",
    "Failed to generate images.": "Bilder konnten nicht generiert werden.",
    "Request failed. Please try again later.": "Anfrage fehlgeschlagen. Bitte versuchen Sie es später noch einmal.",
    "Invalid target aspect_ratio {aspect_ratio}. Available options: {ASPECT_RATIO}": "Ungültiges Ziel-Seitenverhältnis {aspect_ratio}. Verfügbare Optionen: {ASPECT_RATIO}",
    "Invalid target output_format.Available options: 'png or jpeg'": "Ungültiges Ziel-Ausgabeformat. Verfügbare Optionen: 'png or jpeg'",
    "Invalid model Id .Available model is google/nano-banana/edit": "Ungültige Modell-ID. Verfügbares Modell ist google/nano-banana/edit",
    "User id not found It's required": "Benutzer-ID nicht gefunden. Sie ist erforderlich.",
    "Insufficient credits to perform this operation.": "Unzureichendes Guthaben, um diesen Vorgang auszuführen.",
    "Invalid user ID": "Ungültige Benutzer-ID",
    "Submit failed {response.status_code}: {response.text}": "Übermittlung fehlgeschlagen {response.status_code}: {response.text}",
    "This model is not allow": "Dieses Modell ist nicht zulässig",
    "Submit failed {} {}: {}": "Übermittlung fehlgeschlagen {} {}: {}",
    "Image URL is required for image tool.": "Bild-URL ist für das Bild-Tool erforderlich.",
    "User Id not Found": "Benutzer-ID nicht gefunden",
    "Model ID {model_id} not supported.": "Modell-ID {model_id} wird nicht unterstützt.",
    "Image upscaler only support wavespeed-ai/flashvsr model": "Bild-Upscaler unterstützt nur das Modell wavespeed-ai/flashvsr",
    "The targeted resulation can be 1080p/720p/2k/4k": "Die Zielauflösung kann 1080p/720p/2k/4k sein",
    "Polling error {} {}: {}": "Abfragefehler {} {}: {}",
    "Insufficient credits. Current balance: {}": "Unzureichendes Guthaben. Aktueller Kontostand: {}",
    "Insufficient credits to generate a response.": "Unzureichendes Guthaben, um eine Antwort zu generieren.",
    "Video content is empty": "Videoinhalt ist leer",
    "Video content must be bytes": "Videoinhalt muss aus Bytes bestehen",
    "File write error: {}": "Dateischreibfehler: {}",
    "Unexpected error saving video: {}": "Unerwarteter Fehler beim Speichern des Videos: {}",
    "Prompt cannot be empty": "Eingabeaufforderung darf nicht leer sein",
    "Invalid duration. Allowed values are 4, 8, or 12 second's.": "Ungültige Dauer. Zulässige Werte sind 4, 8 oder 12 Sekunden.",
    "Invalid model ID. Contact admin.": "Ungültige Modell-ID. Kontaktieren Sie den Administrator.",
    "Invalid resolution. Allowed resolutions are: {}": "Ungültige Auflösung. Zulässige Auflösungen sind: {}",
    "User or Credit Account not found": "Benutzer oder Guthabenkonto nicht gefunden",
    "AI error: {}": "KI-Fehler: {}",
    "Video job created but no job ID found in response.": "Video-Job erstellt, aber keine Job-ID in der Antwort gefunden.",
    "Failed to check video status: {}": "Statusprüfung des Videos fehlgeschlagen: {}",
    "Video generated successfully {}.": "Video erfolgreich generiert {}.",
    "Unknown job status: {}": "Unbekannter Jobstatus: {}",
    "Video generation timeout. Job took too long to complete.": "Zeitüberschreitung bei der Videogenerierung. Der Job hat zu lange gedauert.",
    "Base cost must be greater than 0 for image generating models.": "Die Basiskosten müssen für bildgenerierende Modelle größer als 0 sein.",
    "Text prompt is required and must be a string": "Text-Eingabeaufforderung ist erforderlich und muss eine Zeichenfolge sein",
    "Invalid user account ID": "Ungültige Benutzerkonto-ID",
    "Submit failed {response_status_code}: {response_text}": "Übermittlung fehlgeschlagen {response_status_code}: {response_text}",
    "Polling error {poll_resp_status_code}": "Abfragefehler {poll_resp_status_code}",
    "Video generation failed": "Videogenerierung fehlgeschlagen",
    "Session type is required": "Sitzungstyp ist erforderlich",
    "No {} active AI models available.": "Keine aktiven {}-KI-Modelle verfügbar."
}

def main():
    po_file = '/home/salahuddin/multiple-ai-model-system/locale/de/LC_MESSAGES/django.po'
    if os.path.exists(po_file):
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        translated_content = translate_po_content(content, de_translations)
        with open(po_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        print(f"Translated {po_file}")
    else:
        print(f"File not found: {po_file}")

if __name__ == "__main__":
    main()
