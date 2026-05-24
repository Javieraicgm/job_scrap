import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.mail_sender.send_weekly_reports import EmailSender
from dotenv import load_dotenv

load_dotenv()

# We need the profile ID. The user's email is javiera.icgm@gmail.com
from supabase import create_client
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

profile = supabase.table('profiles').select('*').eq('email', 'javiera.icgm@gmail.com').single().execute()
if profile.data:
    profile_id = profile.data['id']
    print(f"Profile ID: {profile_id}")
    
    sender = EmailSender()
    success = sender.send_report_for_profile(profile_id)
    print(f"Success: {success}")
else:
    print("Profile not found")
