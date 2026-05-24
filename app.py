import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
import re
import requests

# Native Python email modules (Replaces Brevo SDK)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.validators import (
    validate_signup_data, 
    validate_duplicate_email,
    validate_login_credentials,
    validate_login_form,
    ValidationError
)
from app.password_utils import hash_password, verify_password

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment configuration variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_local_secret")

# Initialize Supabase Client Connection
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def send_status_email(user_email, user_name, status):
    """Sends a transactional HTML notification email to the user via Gmail SMTP"""
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")    
    sender_password = os.getenv("MAIL_PASSWORD")  
    
    sender_name = "CocoScan Platform"
    subject = f"Account Update: Your CocoScan Application has been {status}"
    
    # Dynamic styling matching the context status
    theme_color = "#40916c" if status == "Approved" else "#e63946"
    
    # EXACT FONT-AWESOME 'fa-tree-city' SVG VECTOR DATA PATH
    tree_city_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" width="44" height="44" style="fill: #ffffff; display: block;">
        <path d="M0 480c0 17.7 14.3 32 32 32h384V336c0-13.3-10.7-24-24-24H248c-13.3 0-24 10.7-24 24v176H32c-17.7 0-32-14.3-32-32V254.4c0-11.8 4.9-23 13.5-31l112-104c12.5-11.6 32.5-11.6 45 0l40.1 37.2c-5.7 14-8.8 29.3-8.8 45.4c0 66.3 53.7 120 120 120c24.6 0 47.5-7.4 66.5-20.1L303.4 320H400c44.2 0 80 35.8 80 80v112h128c17.7 0 32-14.3 32-32V224c0-17.7-14.3-32-32-32H480V24c0-13.3-10.7-24-24-24H344c-13.3 0-24 10.7-24 24v123.4L230.2 61.3c-23.4-21.7-59.1-21.7-82.5 0L5.3 191.4C1.9 194.5 0 198.9 0 203.6V480zm352-278a40 40 0 1 1 80 0 40 40 0 1 1 -80 0zm40 134a40 40 0 1 1 0-80 40 40 0 1 1 0 80zM520 256a40 40 0 1 1 80 0 40 40 0 1 1 -80 0zm40 134a40 40 0 1 1 0-80 40 40 0 1 1 0 80z"/>
    </svg>
    """

    if status == "Approved":
        status_title = "Application Approved"
        message_body = f"""
        <p>Great news! Your account application for <strong>CocoScan</strong> has been reviewed and approved by our administration team.</p>
        <p>You can now log in to access your custom dashboard, review coconut metrics, and utilize our pest scanning system features.</p>
        <div style="margin: 30px 0; text-align: center;">
            <a href="http://127.0.0.1:5000/login" style="background-color: {theme_color}; color: #ffffff; padding: 14px 32px; text-decoration: none; font-weight: bold; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">Log In To Dashboard</a>
        </div>
        """
    else:
        status_title = "Application Declined"
        message_body = f"""
        <p>Thank you for your interest in <strong>CocoScan</strong>.</p>
        <p>After carefully reviewing your registration details, our administration team has declined your account application at this time.</p>
        <p style="background-color: #f8f9fa; border-left: 4px solid {theme_color}; padding: 14px; color: #6c757d; font-size: 14px; border-radius: 4px;">
            <strong>Notice:</strong> If you believe this decision was made in error or if you provided incorrect credentials during registration, please reach out to our system support desk for manual verification.
        </p>
        """

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0b1315; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e2e8f0;-webkit-font-smoothing: antialiased;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; background-color: #0b1315; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 550px; background-color: #121f22; border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                        <tr>
                            <td align="center" style="position: relative; padding: 50px 20px; background: linear-gradient(135deg, #162a2d 0%, #0b1315 100%); border-bottom: 2px solid {theme_color};">
                                <div style="position: relative; width: 100px; height: 100px; margin-bottom: 20px; text-align: center;">
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90px; height: 90px; background-color: {theme_color}; border-radius: 50%; opacity: 0.15; filter: blur(10px);"></div>
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; border: 2px solid {theme_color}; border-radius: 50%; opacity: 0.3;"></div>
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 55px; height: 55px; border: 1px dashed {theme_color}; border-radius: 50%; opacity: 0.5;"></div>
                                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); line-height: 1; z-index: 5;">
                                        {tree_city_svg}
                                    </div>
                                </div>
                                <div style="font-weight: 800; font-size: 32px; color: #ffffff; letter-spacing: 1px; margin-bottom: 4px;">CocoScan</div>
                                <div style="font-size: 13px; color: #789c8a; letter-spacing: 2px; text-transform: uppercase; font-weight: 500;">{status_title}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 35px; background-color: #121f22;">
                                <h3 style="margin-top: 0; color: #ffffff; font-size: 18px; font-weight: 600;">Hello {user_name},</h3>
                                <div style="font-size: 15px; line-height: 1.7; color: #cbd5e1;">
                                    {message_body}
                                </div>
                                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.06); margin: 35px 0;">
                                <p style="margin: 0; font-size: 14px; color: #64748b; line-height: 1.5;">
                                    Best regards,<br>
                                    <span style="color: #ffffff; font-weight: 600;">The CocoScan Development Node</span>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="background-color: #0b1315; padding: 25px; font-size: 11px; color: #475569; letter-spacing: 0.5px;">
                                <p style="margin: 0 0 4px 0;">This transmission is encrypted and delivered from the administrative terminal cloud hub.</p>
                                <p style="margin: 0;">&copy; 2026 CocoScan Security Framework • Coconut Disease Detection Systems</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        
        logger.info(f"Notification email dispatched cleanly via Gmail to {user_email}.")
        return True
    except Exception as e:
        logger.error(f"Gmail SMTP Exception thrown while mailing {user_email}: {str(e)}")
        return False
    
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def splash():
    """Renders the initial welcome splash screen loader entry point"""
    return render_template('splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route: Authenticates users against Supabase credentials"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('login.html')

        try:
            validated_email, validated_password = validate_login_form(request.form)
            email = validated_email.strip().lower()
            password = validated_password
        except ValidationError as val_err:
            flash(str(val_err), "error")
            return render_template('login.html')
        except (ValueError, TypeError):
            logger.warning("Login form validator did not return a standard 2-item tuple. Falling back to raw form data.")

        try:
            user_query = supabase.table("users").select("*").eq("email", email).execute()
            
            if not user_query.data:
                flash("Account not found. Please verify your email or sign up.", "error")
                return render_template('login.html')
                
            user_data = user_query.data[0]
            
            if not verify_password(password, user_data.get('password_hash', '')):
                flash("Invalid credentials. Please verify your password and try again.", "error")
                return render_template('login.html')
                
            user_status = user_data.get('status', 'Under Review')
            
            if user_status == 'Under Review':
                flash("Your account is pending administrative approval. You will receive an email once activated.", "warning")
                return render_template('login.html')
            elif user_status == 'Rejected':
                flash("Your application for this account has been declined. Please contact support.", "error")
                return render_template('login.html')

            session.clear()
            session['user_id'] = user_data['id']
            session['user_role'] = user_data['role']
            session['user_name'] = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            
            logger.info(f"User {email} successfully logged in with role: {user_data['role']}")
            
            if str(user_data['role']).strip().lower() == 'admin':
                return redirect(url_for('admin_user_management'))
            else:
                return redirect(url_for('dashboard'))

        except Exception as db_err:
            logger.error(f"Authentication system pipeline breakdown: {str(db_err)}")
            flash("An unexpected error occurred during login. Please try again later.", "error")
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page: Processes user registration with full validation and security"""
    if request.method == 'POST':
        try:
            role = request.form.get('role', '').strip()
            if not role:
                flash("Please select an account role", "error")
                return redirect(url_for('signup'))
            
            validated_data = validate_signup_data(request.form, role)
            email = validated_data['email']
            password = validated_data['password']
            
            if validate_duplicate_email(supabase, email):
                flash("This email address is already registered.", "error")
                return redirect(url_for('signup'))
            
            password_hash = hash_password(password)
            
            user_payload = {
                "first_name": validated_data['first_name'],
                "middle_name": validated_data.get('middle_name'),
                "last_name": validated_data['last_name'],
                "extension_name": validated_data.get('extension_name'),
                "age": validated_data['age'],
                "address": validated_data['address'],
                "email": email,
                "role": role,
                "password_hash": password_hash,
                "status": "Under Review"
            }
            
            user_response = supabase.table("users").insert(user_payload).execute()
            if not user_response.data:
                raise Exception("Failed to insert record into users table")
            
            new_user_id = user_response.data[0]['id']
            profile_payload = {"user_id": new_user_id, "role": role}
            
            if role == 'farmer':
                profile_payload.update({
                    "farmer_barangay": validated_data['farmer_barangay'],
                    "farm_size": validated_data.get('farm_size')
                })
            elif role == 'lgu':
                profile_payload.update({
                    "agency_office": validated_data['lgu_agency'],
                    "position_title": validated_data['lgu_position'],
                    "employee_id": validated_data['lgu_employee_id'],
                    "office_email": validated_data.get('lgu_office_email'),
                    "jurisdiction": validated_data['lgu_jurisdiction']
                })
            elif role == 'agri_expert':
                profile_payload.update({
                    "agency_office": validated_data['agri_office_name'],
                    "position_title": validated_data['agri_position'],
                    "employee_id": validated_data['agri_employee_id'],
                    "office_email": validated_data.get('agri_office_email'),
                    "jurisdiction": validated_data['agri_jurisdiction']
                })
            
            supabase.table("profiles").insert(profile_payload).execute()
            flash(f"Account created successfully! Your account is pending approval.", "success")
            return redirect(url_for('account_notice'))
        
        except ValidationError as e:
            flash(str(e), "error")
            return redirect(url_for('signup'))
        except Exception as e:
            flash("Signup failed. Please check your information and try again.", "error")
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/account-notice')
def account_notice():
    return render_template('notice.html')

@app.route('/dashboard')
def dashboard():
    """Central routing hub to dispatch logged-in sessions to role-specific views"""
    user_id = session.get('user_id')
    user_role = str(session.get('user_role', '')).strip().lower()
    
    if not user_id:
        return redirect(url_for('login'))
        
    if user_role == 'farmer':
        return redirect(url_for('farmer_dashboard'))
    elif user_role == 'admin':
        return redirect(url_for('admin_user_management'))
        
    return render_template('404.html')

def calculate_environmental_risk(temp, humidity, rainfall):
    """Rule-based engine returning high-contrast solid color spaces for dark container themes"""
    if temp == "--" or humidity == "--":
        return {
            "level": "Unknown", 
            "color": "#475569", 
            "bg": "#f1f5f9", 
            "border": "#cbd5e1", 
            "text": "Risk assessment unavailable offline."
        }
    
    try:
        t = float(temp)
        h = float(humidity)
    except (ValueError, TypeError):
        return {
            "level": "Moderate", 
            "color": "#b45309", 
            "bg": "#fef3c7", 
            "border": "#fde68a", 
            "text": "Standard environmental monitoring active."
        }

    if t >= 32 and h >= 75:
        return {
            "level": "High Risk",
            "color": "#991b1b",
            "bg": "#fee2e2",
            "border": "#fca5a5",
            "text": "<strong>High Risk</strong>: Accelerated breeding climate detected for both Brontispa and Rhinoceros Beetles. Inspect young fronds immediately."
        }
    elif h >= 80:
        return {
            "level": "Moderate Risk",
            "color": "#92400e",
            "bg": "#fef3c7",
            "border": "#fde68a",
            "text": "<strong>Moderate Risk</strong>: High moisture levels favor Rhinoceros Beetle breeding nests and localized larval development."
        }
    elif t >= 31 and h < 65:
        return {
            "level": "Moderate Risk",
            "color": "#92400e",
            "bg": "#fef3c7",
            "border": "#fde68a",
            "text": "<strong>Moderate Risk</strong>: Warm, dry foliage layout accelerates early-stage Brontispa leaf-incubation cycles."
        }
    else:
        return {
            "level": "Low Risk",
            "color": "#065f46",
            "bg": "#d1fae5",
            "border": "#a7f3d0",
            "text": "<strong>Low Risk</strong>: Current climate conditions are within baseline stability parameters for pest development."
        }

# Farmer
@app.route('/farmer/dashboard')
def farmer_dashboard():
    user_id = session.get('user_id')
    user_role = str(session.get('user_role', '')).strip().lower()
    
    if not user_id or user_role != 'farmer':
        flash("Unauthorized access path.", "error")
        return redirect(url_for('login'))
        
    try:
        # Fetch the real profile name details from cloud instance
        user_query = supabase.table("users").select("first_name, last_name").eq("id", user_id).execute()
        user_name = f"{user_query.data[0].get('first_name', '')} {user_query.data[0].get('last_name', '')}".strip() if user_query.data else "Farmer"
        
        # -------------------------------------------------------------
        # PRODUCTION REPLACEMENT: LIVE REAL-TIME DATA METRICS DOCKING
        # -------------------------------------------------------------
        # Total report count query
        { 'count': 'exact', 'head': True }
        total_res = supabase.table('reports').select('*', count='exact', head=True).execute()
        total_cases = total_res.count if hasattr(total_res, 'count') else 0

        # Unresolved cases query
        pending_res = supabase.table('reports').select('*', count='exact', head=True).eq('status', 'Pending').execute()
        pending_cases = pending_res.count if hasattr(pending_res, 'count') else 0

        # Resolved cases query
        resolved_res = supabase.table('reports').select('*', count='exact', head=True).eq('status', 'Recommendation Issued').execute()
        resolved_cases = resolved_res.count if hasattr(resolved_res, 'count') else 0

        metrics = {
            "total_cases": total_cases, 
            "pending_cases": pending_cases, 
            "resolved_cases": resolved_cases
        }
        # -------------------------------------------------------------
        
        weather = {
            "location": "San Pablo City, Laguna",
            "temp": "--",
            "humidity": "--",
            "rainfall": "--",
            "wind": "--",
            "is_down": False
        }
        
        latitude = 14.0708
        longitude = 121.3256
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        
        try:
            response = requests.get(weather_url, timeout=4)
            if response.status_code == 200:
                data = response.json()
                current_data = data.get("current", {})
                weather["temp"] = round(current_data.get("temperature_2m"))
                weather["humidity"] = current_data.get("relative_humidity_2m")
                weather["rainfall"] = current_data.get("precipitation", 0.0)
                weather["wind"] = round(current_data.get("wind_speed_10m"))
            else:
                weather["is_down"] = True
        except Exception as weather_err:
            weather["is_down"] = True
            logger.error(f"Weather diagnostic error: {str(weather_err)}")

        risk = calculate_environmental_risk(weather["temp"], weather["humidity"], weather["rainfall"])

        return render_template('farmer_dashboard.html', user_name=user_name, metrics=metrics, weather=weather, risk=risk)
        
    except Exception as e:
        logger.error(f"Dashboard routing exception: {str(e)}")
        return redirect(url_for('logout'))

@app.route('/farmer/scan')
def farmer_scan():
    user_id = session.get('user_id')
    user_role = str(session.get('user_role', '')).strip().lower()
    
    if not user_id or user_role != 'farmer':
        flash("Unauthorized access path. Please log in.", "error")
        return redirect(url_for('login'))
        
    try:
        user_query = supabase.table("users").select("first_name, last_name").eq("id", user_id).execute()
        user_name = f"{user_query.data[0].get('first_name', '')} {user_query.data[0].get('last_name', '')}".strip() if user_query.data else "Farmer"
        
        return render_template('farmer_scan.html', user_name=user_name)
    except Exception as e:
        logger.error(f"Scan Pest routing exception: {str(e)}")
        return redirect(url_for('logout'))

@app.route('/farmer/reports')
def farmer_reports():
    user_id = session.get('user_id')
    user_role = str(session.get('user_role', '')).strip().lower()
    
    if not user_id or user_role != 'farmer':
        flash("Unauthorized access path. Please log in.", "error")
        return redirect(url_for('login'))
        
    try:
        user_query = supabase.table("users").select("first_name, last_name").eq("id", user_id).execute()
        user_name = f"{user_query.data[0].get('first_name', '')} {user_query.data[0].get('last_name', '')}".strip() if user_query.data else "Farmer"
        
        return render_template('farmer_reports.html', user_name=user_name)
    except Exception as e:
        logger.error(f"Farmer Reports feed layout routing exception: {str(e)}")
        return redirect(url_for('logout'))

@app.route('/farmer/submit-report', methods=['POST'])
def farmer_submit_report():
    """Processes pest scan data from the frontend and inserts it into the Supabase 'reports' table"""
    user_id = session.get('user_id')
    user_role = str(session.get('user_role', '')).strip().lower()
    
    if not user_id or user_role != 'farmer':
        return jsonify({'success': False, 'message': 'Unauthorized user session'}), 403

    try:
        # 1. Extract data sent by your scanning interface/form
        # Adjust these keys if your frontend HTML form uses different 'name' attributes
        pest_type = request.form.get('pest_type', 'Unknown Pest').strip()
        damage_severity = request.form.get('damage_severity', 'Low').strip()
        location_notes = request.form.get('location_notes', '').strip()
        image_url = request.form.get('image_url', '').strip() # If your scanner uploads an image first

        # 2. Build the production-ready payload mapped to your database schema
        report_payload = {
            "user_id": user_id,
            "pest_type": pest_type,
            "damage_severity": damage_severity,
            "location_notes": location_notes,
            "image_url": image_url,
            "status": "Pending", # Default status matching our dashboard counter query
        }

        # 3. Fire directly to the live Supabase cloud instance
        response = supabase.table("reports").insert(report_payload).execute()

        if not response.data:
            logger.error("Supabase accepted the connection but failed to write rows.")
            return jsonify({'success': False, 'message': 'Database rejected insertion payload.'}), 500

        logger.info(f"Pest report logged successfully for user {user_id}. Report ID: {response.data[0].get('id')}")
        
        # If your frontend expects a JSON response (like an AJAX submit):
        return jsonify({'success': True, 'message': 'Report submitted and synchronized cleanly!'})
        
        # ALTERNATIVE: If your frontend is a standard form submit that reloads the page, comment out the jsonify line above and uncomment these below:
        # flash("Pest diagnostic report submitted successfully!", "success")
        # return redirect(url_for('farmer_reports'))

    except Exception as e:
        logger.error(f"Cloud instance synchronization failed: {str(e)}")
        return jsonify({'success': False, 'message': f"Cloud instance synchronization failed: {str(e)}"}), 500

# Admin
@app.route('/admin/user-management')
def admin_user_management():
    current_role = str(session.get('user_role', '')).strip().lower()
    if current_role != 'admin':
        return redirect(url_for('login'))

    status_filter = request.args.get('status', 'All').strip()
    search_query = request.args.get('search', '').strip()
    
    try:
        current_page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        current_page = 1
    PER_PAGE = 10

    try:
        response = supabase.table("users").select("*, profiles(*)").order("created_at", desc=True).execute()
        raw_users = response.data or []

        processed_users = []
        for u in raw_users:
            if str(u.get('role', '')).strip().lower() == 'admin':
                continue
            
            user_status = u.get('status', 'Under Review')
            if status_filter != 'All' and user_status != status_filter:
                continue

            first = u.get('first_name') or ''
            last = u.get('last_name') or ''
            email = u.get('email') or ''
            
            u['highlighted_first'] = first
            u['highlighted_last'] = last
            u['highlighted_email'] = email

            if search_query:
                sq = search_query.lower()
                full_compiled = f"{first} {last}".lower()
                
                if sq in full_compiled or sq in email.lower() or sq in (u.get('address') or '').lower():
                    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
                    u['highlighted_first'] = pattern.sub(lambda m: f'<mark class="ux-highlight">{m.group(0)}</mark>', first)
                    u['highlighted_last'] = pattern.sub(lambda m: f'<mark class="ux-highlight">{m.group(0)}</mark>', last)
                    u['highlighted_email'] = pattern.sub(lambda m: f'<mark class="ux-highlight">{m.group(0)}</mark>', email)
                else:
                    continue

            processed_users.append(u)

        total_records = len(processed_users)
        total_pages = max(1, (total_records + PER_PAGE - 1) // PER_PAGE)
        current_page = min(current_page, total_pages)
        
        start_idx = (current_page - 1) * PER_PAGE
        end_idx = start_idx + PER_PAGE
        paginated_users = processed_users[start_idx:end_idx]

    except Exception as e:
        flash(f"Database alignment execution error: {str(e)}", "error")
        paginated_users, total_pages, current_page = [], 1, 1

    return render_template(
        'admin_user_management.html', 
        users=paginated_users, 
        current_status=status_filter, 
        search=search_query,
        current_page=current_page,
        total_pages=total_pages
    )

@app.route('/admin/update-user-status', methods=['POST'])
def update_user_status():
    """Asynchronous API endpoint that saves status, runs email notice, and records logs"""
    if str(session.get('user_role', '')).strip().lower() != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
        
    data = request.get_json() or {}
    user_id = data.get('user_id')
    action = data.get('action')
    
    if not user_id or action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid parameters provided'}), 400
        
    target_status = 'Approved' if action == 'approve' else 'Rejected'
    admin_name = session.get('user_name', 'PCA Admin')
    
    try:
        user_query = supabase.table("users").select("email, first_name, last_name").eq("id", user_id).execute()
        if not user_query.data:
            return jsonify({'success': False, 'message': 'Target profile record not found'}), 404
            
        target_user = user_query.data[0]
        target_email = target_user.get('email')
        target_fullname = f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip()
        
        email_sent = send_status_email(target_email, target_fullname, target_status)
        db_email_status = "Sent Successfully" if email_sent else "Delivery Failed"

        supabase.table("users").update({
            "status": target_status,
            "approved_by": admin_name,
            "email_status": db_email_status
        }).eq("id", user_id).execute()
        
        return jsonify({
            'success': True, 
            'target_status': target_status, 
            'admin_name': admin_name,
            'email_notified': email_sent
        })
    except Exception as e:
        logger.error(f"Status update route processing failure: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)