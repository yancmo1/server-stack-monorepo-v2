#!/usr/bin/env python3
"""
QSL Card Creator - Web Application
A Flask web interface for the QSL Card Creator desktop application
"""

# Load .env from central config
from dotenv import load_dotenv
load_dotenv('/Users/yancyshepherd/MEGA/PythonProjects/YANCY/shared/config/.env')

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
import sys
import tempfile
import sqlite3
import json
import time
import subprocess
from datetime import datetime
import base64
import io
from io import BytesIO
from PIL import Image
import webbrowser
import urllib.parse
import re
import requests
import xml.etree.ElementTree as ET
import requests
import time
import os
import json
import shutil
import tempfile
import base64
import mimetypes
import pickle
import urllib.parse
import webbrowser
import sys
import sqlite3
import logging
import threading
from contextlib import contextmanager

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

# PDF generation imports
try:
    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfWriter, PdfReader
    REPORTLAB_AVAILABLE = True
    PYPDF2_AVAILABLE = True
except ImportError as e:
    print(f"PDF libraries not available: {e}")
    REPORTLAB_AVAILABLE = False
    PYPDF2_AVAILABLE = False


class SafeDatabaseAccess:
    """
    Thread-safe database access with proper locking and error handling
    to prevent corruption when Log4OM and QSL Card Creator access simultaneously
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.RLock()
    
    @contextmanager
    def get_connection(self, timeout=10, read_only=True):
        """
        Get a database connection with proper locking and error handling
        
        Args:
            timeout: Maximum time to wait for database access
            read_only: If True, opens database in read-only mode to prevent conflicts
        """
        conn = None
        acquired = False
        
        try:
            # Acquire thread lock
            acquired = self._lock.acquire(timeout=timeout)
            if not acquired:
                raise sqlite3.OperationalError("Database timeout: Could not acquire lock")
            
            # Check if database exists
            if not os.path.exists(self.db_path):
                raise sqlite3.OperationalError(f"Database file not found: {self.db_path}")
            
            # Configure connection parameters for safe access
            if read_only:
                # Read-only connection to prevent conflicts with Log4OM
                # Use shorter timeout for read-only to fail fast if DB is locked
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=5.0)
                # Additional read-only optimizations
                conn.execute("PRAGMA query_only=ON")
            else:
                # Read-write connection with WAL mode for better concurrency
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
            
            # Set row factory for easier access
            conn.row_factory = sqlite3.Row
            
            yield conn
            
        except sqlite3.OperationalError as e:
            if "malformed" in str(e).lower():
                # Database corruption detected - try to handle gracefully
                logging.error(f"Database corruption detected: {e}")
                raise sqlite3.DatabaseError(f"Database corruption detected: {e}")
            else:
                logging.error(f"Database operational error: {e}")
                raise
        except Exception as e:
            logging.error(f"Unexpected database error: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            if acquired:
                self._lock.release()
    
    def execute_query(self, query, params=None, read_only=True):
        """
        Execute a database query safely
        
        Args:
            query: SQL query to execute
            params: Query parameters
            read_only: If True, uses read-only connection
        
        Returns:
            Query results or None if error
        """
        try:
            with self.get_connection(read_only=read_only) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logging.error(f"Query execution error: {e}")
            return None
    
    def get_qso_count(self):
        """Get total QSO count safely"""
        try:
            with self.get_connection(read_only=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Log")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting QSO count: {e}")
            return 0
    
    def test_database_integrity(self):
        """Test database integrity and return status"""
        try:
            with self.get_connection(read_only=True) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return str(result[0]).lower() == 'ok'
        except Exception as e:
            logging.error(f"Database integrity check failed: {e}")
            return False

# Add current directory to Python path to import the existing application
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# DATABASE CONFIGURATION - Syncthing Integration
# ============================================================================

def get_database_path():
    """Get the appropriate database path based on environment"""
    # Check for Syncthing database first (preferred for sync)
    syncthing_path = os.path.expanduser("~/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite")
    if os.path.exists(syncthing_path):
        return syncthing_path
    
    # Fall back to local database
    local_path = "Log4OM db.SQLite"
    if os.path.exists(local_path):
        return local_path
    
    # Return Syncthing path as default (for new installs)
    return syncthing_path

# Global database path
DATABASE_PATH = get_database_path()

# Global safe database access instance
safe_db = SafeDatabaseAccess(DATABASE_PATH)

# ============================================================================
# MISSING CLASSES AND FUNCTIONS - Required for web app functionality
# ============================================================================

class AppSettings:
    """Manage application settings and configuration"""
    
    def __init__(self):
        self.config_file = "qsl_settings.json"
        self.settings = self.load_settings()
        self.db_connection = None
        self.db_cursor = None
        self.db_path = ""
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # Default settings
        return {
            "last_template": "",
            "last_database": "",
            "window_size": (800, 700),
            "default_qsl_type": "TNX",
            "show_tooltips": True,
            "recent_templates": [],
            "recent_databases": [],
            "hamqth_username": "",
            "hamqth_password": "",
            "gmail_username": ""
        }
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

def preview_qsl_card(template_path, callsign, date, freq, mode, rst, qsltype):
    """Generate a preview image of the QSL card with proper PDF preview"""
    try:
        # First, try to generate the actual PDF
        pdf_path = generate_qsl_card(template_path, callsign, date, freq, mode, rst, qsltype)
        if not pdf_path or not os.path.exists(pdf_path):
            return generate_fallback_preview(callsign, date, freq, mode, rst, qsltype)
        
        # Try to convert PDF to image using Poppler
        poppler_available, _ = check_poppler()
        if poppler_available:
            try:
                import subprocess
                preview_path = tempfile.mktemp(suffix='.png')
                
                # Use pdftoppm to convert first page of PDF to PNG
                cmd = [
                    'pdftoppm', 
                    '-png', 
                    '-f', '1',  # First page only
                    '-l', '1',  # Last page (same as first)
                    '-scale-to-x', '800',  # Scale to reasonable width
                    '-scale-to-y', '-1',   # Maintain aspect ratio
                    pdf_path,
                    preview_path.replace('.png', '')  # pdftoppm adds -1.png
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                # pdftoppm creates filename-1.png
                actual_preview = preview_path.replace('.png', '-1.png')
                
                if result.returncode == 0 and os.path.exists(actual_preview):
                    # Move to expected filename
                    os.rename(actual_preview, preview_path)
                    # Clean up PDF
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass
                    return preview_path
                else:
                    print(f"PDF to image conversion failed: {result.stderr}")
                    
            except Exception as e:
                print(f"Error converting PDF to image: {e}")
        
        # Fallback to simple preview if PDF conversion fails
        return generate_fallback_preview(callsign, date, freq, mode, rst, qsltype)
        
    except Exception as e:
        print(f"Error generating preview: {e}")
        return generate_fallback_preview(callsign, date, freq, mode, rst, qsltype)

def generate_fallback_preview(callsign, date, freq, mode, rst, qsltype):
    """Generate a simple fallback preview image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 400x250 preview image
        img = Image.new('RGB', (400, 250), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add border
        draw.rectangle([5, 5, 395, 245], outline='black', width=2)
        
        # Add QSL card info
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        text_lines = [
            f"QSL Card Preview",
            f"Callsign: {callsign}",
            f"Date: {date}",
            f"Frequency: {freq}",
            f"Mode: {mode}",
            f"RST: {rst}",
            f"Type: {qsltype}",
            "",
            "(Fallback preview - install Poppler for full PDF preview)"
        ]
        
        y_offset = 20
        for line in text_lines:
            draw.text((20, y_offset), line, fill='black', font=font)
            y_offset += 25
            
        temp_file = tempfile.mktemp(suffix='.png')
        img.save(temp_file, 'PNG')
        return temp_file
        
    except Exception as e:
        print(f"Error generating fallback preview: {e}")
        return None

def generate_qsl_card(template_path, callsign, date, freq, mode, rst, qsltype, output_path=None):
    """Generate QSL card PDF using proper template positioning"""
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.pdf')
        
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return generate_simple_pdf(callsign, date, freq, mode, rst, qsltype, output_path)
        
    try:
        # Import required libraries 
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfWriter, PdfReader
        from io import BytesIO
        
        template_reader = PdfReader(template_path)
        page = template_reader.pages[0]
        
        # Get page dimensions
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Create overlay
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        # QSL card positioning - professionally tuned coordinates
        box_left = 30.445
        box_right = 138.395
        box_top = 167.92
        box_height = 55
        box_bottom = box_top - box_height
        x_center = 84.4
        
        # Format date and time - handle multiple formats including UTC suffix
        try:
            # Try different datetime formats that might come from web interface
            date_clean = str(date).strip()
            
            # Remove " UTC" suffix if present but preserve it for display
            has_utc = " UTC" in date_clean
            if has_utc:
                date_clean = date_clean.replace(" UTC", "")
            
            # Try to parse the cleaned date
            dt = None
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M']:
                try:
                    dt = datetime.strptime(date_clean, fmt)
                    break
                except ValueError:
                    continue
            
            if dt:
                formatted_datetime = f"{dt.strftime('%m-%d-%Y')} • {dt.strftime('%H:%M')} UTC"
            else:
                # If parsing fails, at least try to add UTC if it was in original
                formatted_datetime = f"{date_clean} UTC" if has_utc or not " UTC" in str(date) else str(date)
        except:
            formatted_datetime = str(date)
        
        # Text lines with proper positioning
        lines = [
            ('Arial', 10, 'Confirming QSL With', False),
            ('Arial-Bold', 22, callsign.upper(), False),
            ('Arial', 10, 'QSO TIME', False),
            ('Arial-Bold', 10, formatted_datetime, False),
            ('Arial', 10, 'MHz:', True),
            ('Arial', 10, 'Mode:', True),
            ('Arial', 10, 'RST:', True)
        ]
        
        values = [None, None, None, None, str(freq), str(mode), str(rst)]
        
        # Y positions - professionally calculated spacing
        top_padding = 10
        gap_call = 20
        gap_qso = 16
        gap_qso_date = 13
        gap_to_mhz = 18
        minor_gap = 12
        
        y = box_top - top_padding
        y_positions = [y]
        y -= gap_call
        y_positions.append(y)
        y -= gap_qso
        y_positions.append(y)
        y -= gap_qso_date
        y_positions.append(y)
        y -= gap_to_mhz
        y_positions.append(y)
        y -= minor_gap
        y_positions.append(y)
        y -= minor_gap
        y_positions.append(y)
        
        def font_or_fallback(name):
            # Most compatible sans-serif fonts for Docker/Linux environments
            # Ordered by compatibility and appearance quality
            font_fallbacks = [
                'Helvetica',           # Most reliable PostScript font
                'Helvetica-Bold',      # Bold variant
                'Times-Roman',         # Serif fallback (very reliable)
                'Courier',             # Monospace fallback (always available)
                'Symbol'               # Last resort system font
            ]
            
            # Map requested fonts to compatible equivalents
            font_map = {
                'Arial': 'Helvetica',
                'Arial-Bold': 'Helvetica-Bold',
                'Arial Black': 'Helvetica-Bold',
                'Helvetica': 'Helvetica',
                'Helvetica-Bold': 'Helvetica-Bold',
                'Sans-Serif': 'Helvetica',
                'DejaVu Sans': 'Helvetica',
                'Liberation Sans': 'Helvetica'
            }
            
            # Get the mapped font name
            target_font = font_map.get(name, 'Helvetica')
            
            # Try the target font first
            try:
                can.setFont(target_font, 10)
                return target_font
            except:
                # Try each fallback font in order of preference
                for fallback_font in font_fallbacks:
                    try:
                        can.setFont(fallback_font, 10)
                        return fallback_font
                    except:
                        continue
                
                # If all else fails, use the most basic font available
                return 'Helvetica'  # ReportLab should always have this
        
        # Draw text with professional positioning
        for i, (font, size, text, is_label_value) in enumerate(lines):
            y = y_positions[i]
            font_name = font_or_fallback(font)
            print(f"Drawing text '{text}' using font '{font_name}' (requested: '{font}') at size {size}")
            can.setFont(font_name, size)
            if is_label_value:
                label_width = can.stringWidth(text, font_name, size)
                value = values[i]
                value_font = font_or_fallback('Arial-Bold')
                print(f"Using value font '{value_font}' for value '{value}' (requested: 'Arial-Bold')")
                value_size = 10
                value_width = can.stringWidth(value, value_font, value_size)
                total_width = label_width + 6 + value_width
                label_x = x_center - total_width/2 + label_width
                value_x = label_x + 6
                can.drawRightString(label_x, y, text)
                can.setFont(value_font, value_size)
                can.drawString(value_x, y, value)
            else:
                can.drawCentredString(x_center, y, text)
        
        # Draw line and QSL types - positioned at bottom of white box
        can.setStrokeColorRGB(162/255, 32/255, 53/255)
        can.setLineWidth(2)
        line_y = box_bottom - 52  # Just above the QSL text
        can.line(box_left + 5, line_y, box_right - 5, line_y)
        
        qsl_types = ['QSL', 'PSE', 'TNX']
        qsl_gap = 32
        qsl_y = box_bottom - 65  # Position at actual bottom of white box
        qsl_xs = [x_center - qsl_gap, x_center, x_center + qsl_gap]
        
        for i, t in enumerate(qsl_types):
            qsl_font = font_or_fallback('Arial')
            print(f"Drawing QSL type '{t}' using font '{qsl_font}' (requested: 'Arial')")
            can.setFont(qsl_font, 10)
            can.setFillColorRGB(0, 0, 0)
            can.drawCentredString(qsl_xs[i], qsl_y, t)
            if t == qsltype:
                text_width = can.stringWidth(t, qsl_font, 10)
                can.setFillColorRGB(1, 1, 0)  # Yellow color
                can.rect(qsl_xs[i] - text_width/2 - 2, qsl_y - 2, text_width + 4, 12, stroke=0, fill=1)
                can.setFillColorRGB(0, 0, 0)  # Black text
                can.drawCentredString(qsl_xs[i], qsl_y, t)
        
        can.save()
        packet.seek(0)
        overlay_pdf = packet.getvalue()
        
        # Merge with template
        writer = PdfWriter()
        page.merge_page(PdfReader(BytesIO(overlay_pdf)).pages[0])
        writer.add_page(page)
        
        # Write to output file
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return output_path
        
    except Exception as e:
        print(f"Error generating QSL card: {e}")
        return generate_simple_pdf(callsign, date, freq, mode, rst, qsltype, output_path)

def generate_simple_pdf(callsign, date, freq, mode, rst, qsltype, output_path):
    """Generate a simple text-based PDF when ReportLab is not available"""
    try:
        # Create a simple text file that can be converted to PDF later
        text_content = f"""QSL CARD
========

Callsign: {callsign}
Date: {date}
Frequency: {freq}
Mode: {mode}
RST Sent: {rst}
QSL Type: {qsltype}

Thanks for the QSO!

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # For now, create a text file (could be enhanced to create actual PDF)
        with open(output_path, 'w') as f:
            f.write(text_content)
            
        return output_path
        
    except Exception as e:
        print(f"Error generating simple PDF: {e}")
        return None

# Email Templates System
EMAIL_TEMPLATES = {
    'qsl_confirmation': {
        'name': 'QSL Confirmation',
        'subject': 'QSL Confirmation - {callsign} via {mycall}',
        'body': '''Dear {name},

Thank you for our QSO on {qso_date} at {qso_time}.

QSO Details:
- Frequency: {frequency} MHz
- Mode: {mode}
- Signal Reports: {rst_sent}/{rst_rcvd}

I'm pleased to confirm our contact and have prepared my QSL card.

73 and hope to work you again soon!

de {mycall}
{myname}

---
This email was generated by W5XY QSL Card Creator'''
    },
    'tnx_qsl': {
        'name': 'Thanks for QSL Card',
        'subject': 'Thanks for QSL Card - {callsign}',
        'body': '''Dear {name},

Thank you very much for your QSL card confirming our QSO on {qso_date} at {qso_time}.

QSO Details:
- Date: {qso_date}
- Time: {qso_time}
- Frequency: {frequency} MHz
- Mode: {mode}

Your card is very much appreciated and will be added to my collection.

Hope to work you again soon!

Best 73,

de {mycall}
{myname}'''
    }
}

def get_email_templates():
    """Get available email templates with proper names"""
    return {
        "qsl_confirmation": "QSL Confirmation",
        "tnx_qsl": "Thanks for QSL Card"
    }

def format_email_content(template_type, qso_data):
    """Format email content based on template and QSO data using professional templates"""
    
    # Get operator information from Log4OM database settings
    mycall = 'W5XY'  # Default fallback
    operator = 'Yancy Shepherd'  # Default fallback
    
    try:
        # Try to get operator info from Log4OM database
        db_path = DATABASE_PATH
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Get operator info from settings or station table
            try:
                cursor.execute("SELECT value FROM settings WHERE key = 'station_call'")
                result = cursor.fetchone()
                if result:
                    mycall = result[0]
            except:
                pass
                
            try:
                cursor.execute("SELECT value FROM settings WHERE key = 'operator_name'")
                result = cursor.fetchone()
                if result:
                    operator = result[0]
            except:
                pass
                
            conn.close()
    except Exception as e:
        print(f"[DEBUG] Could not get operator info from database: {e}")
    
    # Extract QSO data
    callsign = qso_data.get('callsign', 'N/A')
    
    # Format name - first name only with proper capitalization
    raw_name = qso_data.get('name', '')
    print(f"[DEBUG NAME] Raw name from database: '{raw_name}'")
    
    if raw_name and raw_name.strip() and raw_name not in ['N/A', 'OM/YL', '']:
        # Get first name only and capitalize it
        first_name = raw_name.split()[0].strip()
        name = first_name.capitalize()
        print(f"[DEBUG NAME] Extracted first name: '{name}'")
    else:
        name = 'OM/YL'  # Fallback to traditional amateur radio greeting
        print(f"[DEBUG NAME] Using fallback name: '{name}'")
        
    qso_date = qso_data.get('qso_date', 'N/A')
    qso_time = qso_data.get('qso_time', 'N/A')
    frequency = qso_data.get('frequency', 'N/A')
    mode = qso_data.get('mode', 'N/A')
    rst_sent = qso_data.get('rst_sent', 'N/A')
    rst_rcvd = qso_data.get('rst_rcvd', 'N/A')
    
    # Use the new EMAIL_TEMPLATES system
    if template_type in EMAIL_TEMPLATES:
        print(f"[DEBUG TEMPLATE] Using EMAIL_TEMPLATES for: {template_type}")
        template = EMAIL_TEMPLATES[template_type]
        
        # Format the template with actual data
        format_data = {
            'callsign': callsign,
            'mycall': mycall,
            'myname': operator,  # Use myname for signature
            'name': name,
            'qso_date': qso_date,
            'qso_time': qso_time,
            'frequency': frequency,
            'mode': mode,
            'rst_sent': rst_sent,
            'rst_rcvd': rst_rcvd
        }
        
        print(f"[DEBUG TEMPLATE] Format data: name='{name}', mycall='{mycall}', myname='{operator}'")
        
        try:
            subject = template['subject'].format(**format_data)
            body = template['body'].format(**format_data)
            print(f"[DEBUG TEMPLATE] Template formatting successful")
        except KeyError as e:
            # Fallback if formatting fails
            print(f"[DEBUG TEMPLATE] Template formatting error: {e}")
            subject = f"QSL {template['name']} - {callsign} via {mycall}"
            body = f"Dear {name},\n\nThank you for our QSO.\n\nBest 73,\n\nde {mycall}\n{operator}"
            
        return subject, body
    
    # Legacy support for old template names - avoid recursion
    elif template_type == "confirmation":
        return format_email_content('qsl_confirmation', qso_data)
    elif template_type == "tnx":
        return format_email_content('tnx_qsl', qso_data)
    else:
        # Fallback for unknown templates
        subject = f"QSL {template_type.upper()} - {callsign} via {mycall}"
        body = f"""Dear {name},

Thank you for our QSO on {qso_date} at {qso_time} UTC.

QSO Details:
- Frequency: {frequency} MHz
- Mode: {mode}
- Signal Reports: {rst_sent}/{rst_rcvd}

I'm pleased to confirm our contact and have prepared my QSL card.

73 and hope to work you again soon!

de {mycall}
{operator}"""
        
        return subject, body

# ============================================================================
# END MISSING FUNCTIONS
# ============================================================================

# HAMQTH XML API Implementation
class HamQTHXMLAPI:
    """HAMQTH XML API client for email lookup"""
    def __init__(self):
        self.session_id = None
        self.session_expires = 0
        self.base_url = "https://www.hamqth.com/xml.php"
        self.username = None
        self.password = None
        self.namespace = None  # Will be set after first response

    def set_credentials(self, username, password):
        self.username = username
        self.password = password

    def _get_namespace(self, root):
        # Extract namespace from root tag: {namespace}HamQTH
        if root.tag.startswith('{'):
            return root.tag.split('}')[0].strip('{')
        return ''

    def get_session(self, force_new=False):
        """Get or renew session ID (reuse if valid, else request new)"""
        try:
            current_time = time.time()
            if not self.username or not self.password:
                return False, "HAMQTH credentials not configured"
            if self.session_id and self.session_expires > current_time and not force_new:
                return True, "Session reused"
            # Request new session
            params = {'u': self.username, 'p': self.password}
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            self.namespace = self._get_namespace(root)
            ns = {'ns': self.namespace} if self.namespace else {}
            session_elem = root.find('ns:session' if ns else 'session', ns)
            if session_elem is not None:
                error_elem = session_elem.find('ns:error' if ns else 'error', ns)
                if error_elem is not None and error_elem.text:
                    return False, f"HAMQTH error: {error_elem.text}"
                session_id_elem = session_elem.find('ns:session_id' if ns else 'session_id', ns)
                if session_id_elem is not None and session_id_elem.text:
                    self.session_id = session_id_elem.text
                    self.session_expires = current_time + 3500  # 58 min
                    return True, "Session established"
                return False, "No session ID in response"
            return False, "No <session> element in response"
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Session error: {str(e)}"

    def lookup_callsign(self, callsign):
        """Lookup callsign information with strict HAMQTH protocol compliance and debug logging"""
        max_retries = 2
        for attempt in range(max_retries):
            session_ok, message = self.get_session(force_new=(attempt > 0))
            if not session_ok:
                return None, message
            try:
                session_id = self.session_id
                program_name = "W5XY_QSL_Card_Creator"
                url = f"https://www.hamqth.com/xml.php?id={session_id}&callsign={callsign.lower()}&prg={program_name}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                # Debug: log raw XML response
                logging.warning(f"HAMQTH raw XML for {callsign}:\n{response.text}")
                root = ET.fromstring(response.content)
                ns_uri = self._get_namespace(root)
                ns = {'ns': ns_uri} if ns_uri else {}
                session_elem = root.find('ns:session' if ns else 'session', ns)
                if session_elem is not None:
                    error_elem = session_elem.find('ns:error' if ns else 'error', ns)
                    if error_elem is not None and error_elem.text:
                        # Session expired or invalid, force new session and retry
                        if ("session" in error_elem.text.lower() or "expired" in error_elem.text.lower() or "invalid" in error_elem.text.lower()) and attempt < max_retries - 1:
                            self.session_id = None
                            self.session_expires = 0
                            continue
                        return None, f"HAMQTH error: {error_elem.text}"
                # Find <search> node (with or without namespace)
                search_elem = root.find('ns:search' if ns else 'search', ns)
                if search_elem is None and ns_uri:
                    search_elem = root.find(f'.//{{{ns_uri}}}search')
                if search_elem is not None:
                    data = {child.tag.split('}', 1)[-1]: child.text for child in search_elem}
                    # Debug: log parsed data
                    logging.warning(f"HAMQTH parsed data for {callsign}: {data}")
                    return data, "Success"
                logging.warning(f"HAMQTH: No <search> node found for {callsign}")
                return None, "No data found for callsign"
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    continue
                return None, f"Network error: {str(e)}"
            except ET.ParseError as e:
                logging.warning(f"HAMQTH: XML parse error for {callsign}: {str(e)}")
                return None, f"XML parse error: {str(e)}"
            except Exception as e:
                logging.warning(f"HAMQTH: Lookup error for {callsign}: {str(e)}")
                return None, f"Lookup error: {str(e)}"
        return None, "Max retries exceeded"

# Global HAMQTH API instance
hamqth_api = HamQTHXMLAPI()

def load_hamqth_credentials():
    """Load HAMQTH credentials from settings"""
    try:
        settings_file = "qsl_settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                hamqth_user = settings.get('hamqth_username', '')
                hamqth_pass = settings.get('hamqth_password', '')
                if hamqth_user and hamqth_pass:
                    hamqth_api.set_credentials(hamqth_user, hamqth_pass)
                    return True
        return False
    except Exception:
        return False

app = Flask(__name__)
app.secret_key = os.environ.get('QSL_SECRET_KEY', 'changeme-please-set-QSL_SECRET_KEY')

# Global settings
app_settings = AppSettings() if 'AppSettings' in globals() else None

# Ensure HAMQTH credentials are loaded and set on startup
if app_settings and 'hamqth_username' in app_settings.settings and 'hamqth_password' in app_settings.settings:
    hamqth_user = app_settings.settings.get('hamqth_username', '')
    hamqth_pass = app_settings.settings.get('hamqth_password', '')
    if hamqth_user and hamqth_pass:
        hamqth_api.set_credentials(hamqth_user, hamqth_pass)

# Define standalone functions (no desktop imports needed)
DESKTOP_FUNCTIONS_AVAILABLE = False
HAMQTH_AVAILABLE = True  # We have our own HAMQTH implementation

def check_poppler():
    """Check if Poppler is available for PDF generation"""
    try:
        # Try to run pdftoppm to check if poppler is available
        result = subprocess.run(['pdftoppm', '-h'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return True, "Poppler available for PDF generation"
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False, "Poppler installed but not accessible"
    except FileNotFoundError:
        return False, "Poppler not installed - PDF generation unavailable"
    except Exception as e:
        return False, f"Poppler check failed: {str(e)}"

def get_save_filename(callsign, date):
    return f"QSL_{callsign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def cleanup_temp_files():
    """Clean up temporary files"""
    pass

def upload_database_to_pc():
    """Upload local database changes back to PC/network mount"""
    try:
        settings = app_settings.settings if app_settings else {}
        deployment_env = settings.get('deployment_environment', 'local')
        local_path = settings.get('last_database', 'Log4OM db.SQLite')
        backup_enabled = settings.get('backup_before_upload', True)
        
        # Choose the correct network path based on deployment environment
        if deployment_env == 'pi':
            network_mount_path = settings.get('pi_network_mount_path', '')
        else:
            # Use Mac OneDrive path for local testing
            network_mount_path = settings.get('network_mount_path', '')
        
        if not network_mount_path:
            return False, f"Network mount path not configured for {deployment_env} environment"
            
        if not os.path.exists(local_path):
            return False, f"Local database not found: {local_path}"
            
        # Check if network mount is accessible
        network_dir = os.path.dirname(network_mount_path)
        if not os.path.exists(network_dir):
            return False, f"Network mount not accessible: {network_dir}"
        
        # Get modification times
        local_mtime = os.path.getmtime(local_path)
        
        # Create backup of target database if it exists and backup is enabled
        if os.path.exists(network_mount_path) and backup_enabled:
            pc_mtime = os.path.getmtime(network_mount_path)
            backup_path = f"{network_mount_path}.backup.{int(pc_mtime)}"
            
            import shutil
            shutil.copy2(network_mount_path, backup_path)
            print(f"Created backup: {backup_path}")
        
        # Copy local database to target
        import shutil
        shutil.copy2(local_path, network_mount_path)
        
        return True, f"Database uploaded to {deployment_env} environment successfully (local modified: {datetime.fromtimestamp(local_mtime)})"
        
    except Exception as e:
        return False, f"Error uploading database: {str(e)}"

def download_database_from_onedrive():
    """Download database from OneDrive (alias for download_database_from_pc)"""
    return download_database_from_pc()

def download_database_from_pc():
    """Download database from PC/network mount (manual only)"""
    try:
        settings = app_settings.settings if app_settings else {}
        deployment_env = settings.get('deployment_environment', 'local')
        local_path = settings.get('last_database', 'Log4OM db.SQLite')
        
        # Choose the correct network path based on deployment environment
        if deployment_env == 'pi':
            network_mount_path = settings.get('pi_network_mount_path', '')
        else:
            # Use Mac OneDrive path for local testing
            network_mount_path = settings.get('network_mount_path', '')
        
        if not network_mount_path:
            return False, f"Network mount path not configured for {deployment_env} environment. Please set appropriate path in qsl_settings.json"
            
        if not os.path.exists(network_mount_path):
            return False, f"Database not found at: {network_mount_path}"
            
        # Check if local database exists and get modification times
        local_exists = os.path.exists(local_path)
        
        pc_mtime = os.path.getmtime(network_mount_path)
        
        if local_exists:
            local_mtime = os.path.getmtime(local_path)
            if local_mtime >= pc_mtime:
                return True, "Local database is already up to date (newer than source database)"
        
        # Create backup of local database if it exists
        if local_exists:
            backup_path = f"{local_path}.backup.{int(time.time())}"
            import shutil
            shutil.copy2(local_path, backup_path)
            print(f"Local database backed up to: {backup_path}")
            
        # Copy database from source
        import shutil
        shutil.copy2(network_mount_path, local_path)
        
        return True, f"Database downloaded successfully from {deployment_env} environment (modified: {datetime.fromtimestamp(pc_mtime).strftime('%Y-%m-%d %H:%M:%S')})"
        
    except Exception as e:
        return False, f"Error downloading database: {str(e)}"

def check_and_download_database():
    """Check database status without auto-downloading"""
    try:
        settings = app_settings.settings if app_settings else {}
        auto_download = settings.get('auto_download_database', False)
        
        if auto_download:
            # Only download if explicitly enabled (now disabled by default)
            return download_database_from_pc()
        else:
            # Just check status
            local_path = settings.get('last_database', 'Log4OM db.SQLite')
            network_mount_path = settings.get('network_mount_path', '')
            
            local_exists = os.path.exists(local_path)
            network_exists = os.path.exists(network_mount_path) if network_mount_path else False
            
            if local_exists and network_exists:
                local_mtime = os.path.getmtime(local_path)
                pc_mtime = os.path.getmtime(network_mount_path)
                
                if local_mtime > pc_mtime:
                    return True, "Local database has newer changes (ready to upload)"
                elif pc_mtime > local_mtime:
                    return True, "PC database has newer changes (download available)"
                else:
                    return True, "Local and PC databases are synchronized"
            elif local_exists:
                return True, "Local database available (PC not mounted)"
            elif network_exists:
                return True, "PC database available (download available)"
            else:
                return False, "No database found locally or on PC"
            
    except Exception as e:
        return False, f"Error checking database: {str(e)}"

def generate_qsl_card_fallback(*args):
    """Fallback QSL card generation - disabled in web-only mode"""
    return False

@app.route('/')
def index():
    """Main page"""
    # Check if Poppler is available
    poppler_status = False
    poppler_message = "Not available"
    
    if 'check_poppler' in globals():
        try:
            poppler_status, poppler_message = check_poppler()
        except Exception as e:
            poppler_message = f"Error checking Poppler: {e}"
    
    # Check if template file exists
    template_path = "W5XY QSL Card Python TEMPLATE.pdf"
    template_exists = os.path.exists(template_path)
    
    # Check if database exists
    db_path = DATABASE_PATH
    db_exists = os.path.exists(db_path)
    
    return render_template('index.html', 
                         poppler_status=poppler_status,
                         poppler_message=poppler_message,
                         template_exists=template_exists,
                         db_exists=db_exists)

@app.route('/create')
def create_qsl():
    """QSL Card creation form"""
    return render_template('create.html')

@app.route('/preview', methods=['POST'])
def preview_qsl():
    """Generate QSL card preview"""
    try:
        # Get form data
        callsign = request.form.get('callsign', '').upper()
        date = request.form.get('date', '')
        time_input = request.form.get('time', '')
        freq = request.form.get('freq', '')
        mode = request.form.get('mode', '')
        rst = request.form.get('rst', '')
        qsltype = request.form.get('qsltype', 'eQSL')
        
        # Process time: preserve UTC designation for QSL card display
        if date and time_input:
            # If time doesn't have UTC, add it (amateur radio standard)
            time_display = time_input if 'UTC' in time_input else f"{time_input} UTC"
            datetime_str = f"{date} {time_display}"
        elif date:
            datetime_str = date
        else:
            datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " UTC"
        
        # Check if preview function is available
        if 'preview_qsl_card' not in globals():
            return jsonify({'success': False, 'error': 'Preview function not available'})
        
        template_path = "W5XY QSL Card Python TEMPLATE.pdf"
        if not os.path.exists(template_path):
            return jsonify({'success': False, 'error': 'Template file not found'})
        
        # Generate preview
        preview_file_path = preview_qsl_card(
            template_path, callsign, datetime_str, freq, mode, rst, qsltype
        )
        
        if preview_file_path and os.path.exists(preview_file_path):
            # Read the PNG file and convert to base64 for web display
            with open(preview_file_path, 'rb') as img_file:
                img_str = base64.b64encode(img_file.read()).decode()
                return jsonify({
                    'success': True, 
                    'preview': f"data:image/png;base64,{img_str}"
                })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate preview'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Preview error: {str(e)}'})

@app.route('/generate', methods=['POST'])
def generate_qsl():
    """Generate and download QSL card PDF"""
    try:
        # Get form data
        callsign = request.form.get('callsign', '').upper()
        date = request.form.get('date', '')
        time_input = request.form.get('time', '')
        freq = request.form.get('freq', '')
        mode = request.form.get('mode', '')
        rst = request.form.get('rst', '')
        qsltype = request.form.get('qsltype', 'eQSL')
        
        # Get QSL tracking data
        qsl_sent = request.form.get('qsl_sent', '')
        qsl_received = request.form.get('qsl_received', '')
        sent_via = request.form.get('sent_via', 'Electronic')
        received_date = request.form.get('received_date', '')
        
        # Process time: get from database for accurate QSO time
        if callsign and date:
            # First try to get the actual QSO time from database
            try:
                conn = sqlite3.connect(DATABASE_PATH, timeout=10)
                cursor = conn.cursor()
                
                # Search for QSO by callsign and date
                cursor.execute("""
                    SELECT callsign, qsodate, frequency, mode, rstsent, rstrcvd, email
                    FROM Log 
                    WHERE callsign = ? AND DATE(qsodate) = DATE(?)
                    ORDER BY qsodate DESC 
                    LIMIT 1
                """, (callsign, date))
                
                row = cursor.fetchone()
                conn.close()
                
                if row and row[1]:  # If QSO found with datetime
                    qso_datetime = row[1]
                    # Extract time from database datetime like email system does
                    try:
                        dt_clean = qso_datetime.replace('Z', '')
                        if ' ' in dt_clean:
                            date_part, time_part = dt_clean.split(' ')
                            # Ensure time is shown as UTC
                            if not time_part.endswith(' UTC'):
                                time_part = time_part + ' UTC'
                            datetime_str = f"{date_part} {time_part}"
                            print(f"[DEBUG QSL] Using database time: callsign='{callsign}', date='{date}', qso_datetime='{qso_datetime}', formatted='{datetime_str}'", flush=True)
                        else:
                            # No time in database, use provided time or current time
                            if time_input.strip():
                                time_display = time_input if 'UTC' in time_input else f"{time_input} UTC"
                                datetime_str = f"{date} {time_display}"
                                print(f"[DEBUG QSL] Database has no time, using form input: '{datetime_str}'", flush=True)
                            else:
                                import datetime as dt
                                current_utc_time = dt.datetime.utcnow().strftime('%H:%M')
                                datetime_str = f"{date} {current_utc_time} UTC"
                                print(f"[DEBUG QSL] Database has no time, using current UTC: '{datetime_str}'", flush=True)
                    except Exception as e:
                        print(f"[DEBUG QSL] Error parsing database datetime '{qso_datetime}': {e}", flush=True)
                        # Fallback to form input or current time
                        if time_input.strip():
                            time_display = time_input if 'UTC' in time_input else f"{time_input} UTC"
                            datetime_str = f"{date} {time_display}"
                        else:
                            import datetime as dt
                            current_utc_time = dt.datetime.utcnow().strftime('%H:%M')
                            datetime_str = f"{date} {current_utc_time} UTC"
                else:
                    print(f"[DEBUG QSL] No QSO found in database for callsign='{callsign}', date='{date}'", flush=True)
                    # Fallback to form input or current time
                    if time_input.strip():
                        time_display = time_input if 'UTC' in time_input else f"{time_input} UTC"
                        datetime_str = f"{date} {time_display}"
                        print(f"[DEBUG QSL] Using form input: '{datetime_str}'", flush=True)
                    else:
                        import datetime as dt
                        current_utc_time = dt.datetime.utcnow().strftime('%H:%M')
                        datetime_str = f"{date} {current_utc_time} UTC"
                        print(f"[DEBUG QSL] Using current UTC: '{datetime_str}'", flush=True)
                        
            except Exception as e:
                print(f"[DEBUG QSL] Database query error: {e}", flush=True)
                # Fallback to form input or current time
                if time_input.strip():
                    time_display = time_input if 'UTC' in time_input else f"{time_input} UTC"
                    datetime_str = f"{date} {time_display}"
                else:
                    import datetime as dt
                    current_utc_time = dt.datetime.utcnow().strftime('%H:%M')
                    datetime_str = f"{date} {current_utc_time} UTC"
        else:
            # No callsign/date provided, use current datetime
            datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " UTC"
            print(f"[DEBUG QSL] No callsign/date provided, using current datetime: '{datetime_str}'", flush=True)
        
        # Check if generation function is available
        settings = app_settings.settings if app_settings else {}
        pdf_enabled = settings.get('pdf_generation_enabled', False)
        
        if not pdf_enabled:
            flash('PDF generation disabled - enable in settings to generate actual PDFs', 'warning')
            # Still allow text-based generation as fallback
        
        template_path = "W5XY QSL Card Python TEMPLATE.pdf"
        if not os.path.exists(template_path):
            flash('Template file not found', 'error')
            return redirect(url_for('create_qsl'))
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate QSL card
        success = generate_qsl_card(
            template_path, callsign, datetime_str, freq, mode, rst, qsltype, output_path
        )
        
        if success and os.path.exists(output_path):
            # Mark QSL as sent in Log4OM database
            mark_success, mark_message = update_qso_qsl_status(callsign, date, qsl_sent, qsl_received, sent_via, received_date)
            # Remove first sentence from message and add link to Gmail drafts
            gmail_drafts_url = "https://mail.google.com/mail/u/0/#drafts"
            
            # Check if we have a draft URL from the function (if it was called)
            draft_url = getattr(mark_success, 'draft_url', None) if hasattr(mark_success, 'draft_url') else None
            
            if draft_url:
                # Only show the drafts link, not the draft_url (which is not always clickable)
                return jsonify({
                    'success': True,
                    'message': f'{mark_message}',
                    'drafts_link': gmail_drafts_url
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'Gmail draft created (fallback). {mark_message}',
                    'drafts_link': gmail_drafts_url
                })
        else:
            error_message = "QSL card generation failed"
            return jsonify({'success': False, 'error': error_message})
            
    except Exception as e:
        flash(f'Generation error: {str(e)}', 'error')
        return redirect(url_for('create_qsl'))

@app.route('/qsos')
def list_qsos():
    """List QSOs from database using safe database access"""
    try:
        # Use safe database access - include QSL confirmation data
        rows = safe_db.execute_query("""
            SELECT callsign, qsodate, freq, mode, rstsent, rstrcvd, email, qsoconfirmations
            FROM Log 
            ORDER BY qsodate DESC 
            LIMIT 100
        """, read_only=True)
        
        if rows is None:
            return render_template('qsos.html', qsos=[], error="Database access error - please try again")
        
        # Handle case where rows might be an integer (should not happen for SELECT, but defensive coding)
        if isinstance(rows, int):
            return render_template('qsos.html', qsos=[], error="Unexpected database response - please try again")
        
        qsos = []
        for row in rows:
            # Parse datetime from qsodate field
            qso_datetime = row[1] if len(row) > 1 else None
            
            # Split date and time
            if qso_datetime:
                try:
                    # Remove 'Z' and split date and time
                    dt_clean = qso_datetime.replace('Z', '')
                    if ' ' in dt_clean:
                        date_part, time_part = dt_clean.split(' ')
                        # Ensure time is shown as UTC
                        if not time_part.endswith(' UTC'):
                            time_part = time_part + ' UTC'
                    else:
                        date_part = dt_clean
                        time_part = ''
                except Exception:
                    date_part = qso_datetime
                    time_part = ''
            else:
                date_part = ''
                time_part = ''
            
            # Parse QSL confirmation data
            qsl_sent = "No"
            qsl_received = "No"
            qso_confirmations = row[7] if len(row) > 7 and row[7] else ""
            
            if qso_confirmations:
                try:
                    import json
                    confirmations = json.loads(qso_confirmations)
                    # Look for QSL card confirmations (not eQSL or LOTW)
                    for conf in confirmations:
                        if conf.get('CT') == 'QSL':  # QSL card (not eQSL)
                            # Only show "Yes" if actually sent/received, ignore "Requested"
                            sent_status = conf.get('S', 'No')
                            received_status = conf.get('R', 'No')
                            qsl_sent = "Yes" if sent_status == "Yes" else "No"
                            qsl_received = "Yes" if received_status == "Yes" else "No"
                            break
                except:
                    pass  # If JSON parsing fails, default to "No"
            
            qso_data = {
                'callsign': row[0],
                'date': date_part,
                'time': time_part,
                'frequency': str(row[2]) if row[2] else '',
                'mode': row[3] if row[3] else '',
                'rst_sent': row[4] if row[4] else '59',
                'rst_received': row[5] if row[5] else '59',
                'email': row[6] if len(row) > 6 and row[6] else '',
                'qsl_sent': qsl_sent,
                'qsl_received': qsl_received,
                'qso_datetime': qso_datetime  # Include full datetime for unique identification
            }
            qsos.append(qso_data)
        
        if len(qsos) == 0:
            return render_template('qsos.html', qsos=[], error="No QSOs found")
        
        return render_template('qsos.html', qsos=qsos)
            
    except Exception as e:
        return render_template('qsos.html', qsos=[], error=f"Database error: {str(e)}")

@app.route('/status')
def status():
    """System status page"""
    status_info = {
        'poppler': {'status': False, 'message': 'Not available'},
        'template': os.path.exists("W5XY QSL Card Python TEMPLATE.pdf"),
        'database': os.path.exists("Log4OM db.SQLite"),
        'functions': {
            'check_poppler': 'check_poppler' in globals(),
            'generate_qsl_card': 'generate_qsl_card' in globals(),
            'preview_qsl_card': 'preview_qsl_card' in globals(),
        }
    }
    
    if 'check_poppler' in globals():
        try:
            status_info['poppler']['status'], status_info['poppler']['message'] = check_poppler()
        except Exception as e:
            status_info['poppler']['message'] = f"Error: {e}"
    
    return render_template('status.html', status=status_info)

@app.route('/api/cleanup')
def api_cleanup():
    """Clean up temporary files"""
    try:
        if 'cleanup_temp_files' in globals():
            cleanup_temp_files()
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Gmail API integration (imported from cruise-price-check/gmail_api.py)
import os
import base64
import mimetypes
import pickle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

class GmailAPIClient:
    def __init__(self, credentials_path='gmail_credentials.json', token_path='gmail_token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.authenticated = False

    def authenticate(self):
        if not GMAIL_API_AVAILABLE:
            return False, "Gmail API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        
        print(f"[GMAIL AUTH] Starting authentication. Token path: {self.token_path}, Credentials path: {self.credentials_path}", flush=True)
        
        creds = None
        # Try loading existing token
        if os.path.exists(self.token_path):
            print(f"[GMAIL AUTH] Token file exists, loading...", flush=True)
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                print(f"[GMAIL AUTH] Token loaded. Valid: {creds.valid if creds else 'None'}", flush=True)
            except Exception as e:
                print(f"[GMAIL AUTH] Error loading token: {e}", flush=True)
                creds = None
        
        # Check if credentials are valid or can be refreshed
        if not creds or not creds.valid:
            print(f"[GMAIL AUTH] Credentials invalid or missing", flush=True)
            if creds and creds.expired and creds.refresh_token:
                print(f"[GMAIL AUTH] Attempting to refresh expired token", flush=True)
                try:
                    creds.refresh(Request())
                    print(f"[GMAIL AUTH] Token refreshed successfully", flush=True)
                    # Save refreshed token
                    with open(self.token_path, 'wb') as token:
                        pickle.dump(creds, token)
                        print(f"[GMAIL AUTH] Refreshed token saved", flush=True)
                except Exception as e:
                    print(f"[GMAIL AUTH] Token refresh failed: {e}", flush=True)
                    creds = None
            
            # If still no valid credentials, need new authentication
            if not creds:
                if not os.path.exists(self.credentials_path):
                    return False, f"Gmail credentials file not found: {self.credentials_path}. Please download from Google Cloud Console."
                
                print(f"[GMAIL AUTH] No valid token, attempting to create new authentication", flush=True)
                
                try:
                    print(f"[GMAIL AUTH] Starting OAuth flow", flush=True)
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, GMAIL_SCOPES)
                    
                    # Try local server OAuth flow
                    creds = flow.run_local_server(port=0)
                    print(f"[GMAIL AUTH] OAuth flow completed", flush=True)
                    
                except Exception as e:
                    print(f"[GMAIL AUTH] OAuth flow failed: {e}", flush=True)
                    return False, f"Authentication failed: {str(e)}. Please ensure you can access Gmail on this system."
                
                # Save new credentials
                if creds:
                    try:
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(creds, token)
                            print(f"[GMAIL AUTH] New token saved", flush=True)
                    except Exception as e:
                        print(f"[GMAIL AUTH] Failed to save token: {e}", flush=True)
        
        # Build Gmail service
        if creds:
            try:
                self.service = build('gmail', 'v1', credentials=creds)
                self.authenticated = True
                print(f"[GMAIL AUTH] Gmail service built successfully", flush=True)
                return True, "Gmail API authenticated successfully"
            except Exception as e:
                print(f"[GMAIL AUTH] Failed to build Gmail service: {e}", flush=True)
                return False, f"Failed to build Gmail service: {str(e)}"
        else:
            print(f"[GMAIL AUTH] No valid credentials available", flush=True)
            return False, "No valid Gmail credentials available"

    def create_message_with_attachment(self, to, subject, body_text, attachment_path=None):
        """Create a MIME message with optional attachment, following Gmail API best practices"""
        print(f"[GMAIL] Creating MIME message: to={to}, subject={subject}, attachment={attachment_path}")
        
        # Create the main message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        # Add the text body
        msg_body = MIMEText(body_text, 'plain', 'utf-8')
        message.attach(msg_body)
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            print(f"[GMAIL] Adding attachment: {attachment_path}")
            try:
                # Guess the content type based on the file's extension
                content_type, encoding = mimetypes.guess_type(attachment_path)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                
                main_type, sub_type = content_type.split('/', 1)
                print(f"[GMAIL] Attachment content type: {content_type}")
                
                # Read the file and create attachment
                with open(attachment_path, 'rb') as fp:
                    attachment = MIMEBase(main_type, sub_type)
                    attachment.set_payload(fp.read())
                    encoders.encode_base64(attachment)
                    
                    # Add header with filename
                    filename = os.path.basename(attachment_path)
                    attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"'
                    )
                    message.attach(attachment)
                    print(f"[GMAIL] Attachment added successfully: {filename}")
            except Exception as e:
                print(f"[GMAIL] Error adding attachment: {e}")
                # Continue without attachment rather than failing completely
        
        # Convert to base64url encoded string as required by Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    def create_draft(self, to, subject, body_text, attachment_path=None):
        """Create a Gmail draft with optional attachment, following Gmail API best practices"""
        print(f"[GMAIL] GmailAPIClient.create_draft called: to={to}, subject={subject}, attachment={attachment_path}")
        
        # Ensure we're authenticated
        if not self.authenticated:
            auth_result, auth_message = self.authenticate()
            print(f"[GMAIL] Authentication result: {auth_result}, message={auth_message}")
            if not auth_result:
                return False, auth_message, None
        
        if not self.service:
            print("[GMAIL] Error: Gmail service is not initialized after authentication.")
            return False, "Gmail service not initialized", None
        
        try:
            # Create the MIME message with optional attachment
            message = self.create_message_with_attachment(to, subject, body_text, attachment_path)
            
            # Create the draft body following Gmail API specification
            draft_body = {'message': message}
            
            # Create the draft using the Gmail API
            print(f"[GMAIL] Calling Gmail API to create draft...")
            draft = self.service.users().drafts().create(userId='me', body=draft_body).execute()
            
            draft_id = draft['id']
            draft_url = f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"
            
            print(f"[GMAIL] Draft created successfully: id={draft_id}, url={draft_url}")
            
            attachment_info = ""
            if attachment_path and os.path.exists(attachment_path):
                attachment_info = f" with attachment {os.path.basename(attachment_path)}"
            
            return True, f"Gmail draft created successfully{attachment_info} (ID: {draft_id})", draft_url
            
        except Exception as e:
            error_msg = f"Error creating draft: {str(e)}"
            print(f"[GMAIL] {error_msg}")
            return False, error_msg, None

# Main function for creating Gmail drafts

def create_gmail_draft_with_attachment(to, subject, body, attachment_path=None, use_api=True):
    print(f"[GMAIL] Attempting to create draft: to={to}, subject={subject}, attachment={attachment_path}, use_api={use_api}", flush=True)
    
    if not to:
        print(f"[GMAIL] Error: No email address provided", flush=True)
        return False, "No email address provided", None
    
    if use_api and GMAIL_API_AVAILABLE:
        try:
            client = GmailAPIClient()
            success, message, draft_url = client.create_draft(to, subject, body, attachment_path)
            print(f"[GMAIL] Draft creation result: success={success}, message={message}, draft_url={draft_url}", flush=True)
            if success:
                return success, message, draft_url
            else:
                print(f"[GMAIL] API failed, falling back to web URL method: {message}", flush=True)
                use_api = False
        except Exception as e:
            print(f"[GMAIL] Exception in API method, falling back to web URL: {e}", flush=True)
            use_api = False
    
    if not use_api or not GMAIL_API_AVAILABLE:
        # Fallback to URL method
        import urllib.parse
        to_param = urllib.parse.quote(to) if to else ""
        subject_param = urllib.parse.quote(subject)
        body_param = urllib.parse.quote(body)
        
        # Add note about attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            attachment_note = f"\n\n[Note: Please manually attach the QSL card file: {os.path.basename(attachment_path)}]"
            body_with_note = body + attachment_note
            body_param = urllib.parse.quote(body_with_note)
        
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to_param}&su={subject_param}&body={body_param}"
        print(f"[GMAIL] Fallback Gmail URL created: {gmail_url}", flush=True)
        return True, "Gmail URL created for manual opening", gmail_url
    
    print("[GMAIL] No method available for creating Gmail draft", flush=True)
    return False, "No method available for creating Gmail draft", None

def create_gmail_web_draft(email_address, subject, body, attachment_path=None):
    """Create Gmail web interface draft - DEPRECATED, use direct URL creation in email_setup route"""
    print("[GMAIL] create_gmail_web_draft called - this function is deprecated")
    return False, "This function is deprecated"

@app.route('/email-setup', methods=['POST'])
def email_setup():
    """Set up email for QSL card"""
    try:
        import sys
        print("[DEBUG EMAIL] Email setup route called", flush=True)
        print(f"[DEBUG FORM] All form data: {dict(request.form)}", flush=True)
        print(f"[DEBUG FORM] Specific time field: '{request.form.get('time', 'NOT_FOUND')}'", flush=True)
        sys.stdout.flush()
        
        # Get form data
        callsign = request.form.get('callsign', '').upper()
        date = request.form.get('date', '')
        time_input = request.form.get('time', '')
        freq = request.form.get('freq', '')
        mode = request.form.get('mode', '')
        rst = request.form.get('rst', '')
        qsltype = request.form.get('qsltype', 'TNX')
        email_address = request.form.get('email_address', '')
        template_type = request.form.get('template_type', 'qsl_confirmation')
        
        # Get QSL tracking data
        qsl_sent = request.form.get('qsl_sent', '')
        qsl_received = request.form.get('qsl_received', '')
        sent_via = request.form.get('sent_via', 'Electronic')
        received_date = request.form.get('received_date', '')
        
        print(f"[DEBUG EMAIL] Form data: callsign={callsign}, email={email_address}, qsl_sent={qsl_sent}, qsl_received={qsl_received}", flush=True)
        sys.stdout.flush()
        
        # Process time: strip UTC for datetime creation, but preserve for email display
        time_clean = time_input.replace(' UTC', '') if time_input else ''
        print(f"[DEBUG EMAIL] Time data: date={date}, time_input='{time_input}', time_clean='{time_clean}'", flush=True)
        
        # Combine date and time
        if date and time_clean:
            datetime_str = f"{date} {time_clean}"
        elif date:
            datetime_str = date
        else:
            datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get the operator name for this callsign from the database
        name = 'OM/YL'  # Default fallback
        try:
            db_path = DATABASE_PATH
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path, timeout=5.0)
                cursor = conn.cursor()
                # Log4OM uses 'Log' table with 'name' and 'callsign' columns
                cursor.execute("SELECT name FROM Log WHERE callsign = ? ORDER BY qsodate DESC LIMIT 1", (callsign,))
                result = cursor.fetchone()
                if result and result[0]:
                    name = result[0].strip()
                    print(f"[DEBUG] Found name for {callsign}: '{name}'")
                else:
                    print(f"[DEBUG] No name found for {callsign} in Log table")
                conn.close()
        except Exception as e:
            print(f"[DEBUG] Could not get name for {callsign}: {e}")
        
        # Format time consistently as "HH:MM UTC" for email display
        formatted_time = time_input.strip() if time_input else ''
        if formatted_time:
            # Clean up time and ensure it has UTC suffix
            if not formatted_time.endswith(' UTC'):
                # If time contains a colon (indicating HH:MM format), add UTC
                if ':' in formatted_time:
                    formatted_time += ' UTC'
            print(f"[DEBUG EMAIL] Time formatting: input='{time_input}' -> output='{formatted_time}'", flush=True)
        else:
            # If no time provided, use current time in UTC as fallback
            import datetime as dt
            current_utc = dt.datetime.utcnow().strftime('%H:%M')
            formatted_time = f"{current_utc} UTC"
            print(f"[DEBUG EMAIL] No time provided, using current UTC time: '{formatted_time}'", flush=True)
        
        # Create QSO data for email template
        qso_data = {
            'callsign': callsign,
            'name': name,  # Add the name field for template substitution
            'qso_date': date,
            'qso_time': formatted_time,  # Use formatted time with "HH:MM UTC"
            'frequency': freq,
            'mode': mode,
            'rst_sent': rst,
            'rst_rcvd': rst,
            'operator_call': 'W5XY',  # You can make this configurable
            'operator_name': 'Operator',  # You can make this configurable
            'operator_sender_name': 'Your Name'  # You can make this configurable
        }
        
        print(f"[DEBUG EMAIL] QSO data for template: qso_time='{qso_data.get('qso_time')}', qso_date='{qso_data.get('qso_date')}'", flush=True)
        
        # Get email templates and format content
        print(f"[DEBUG EMAIL] About to process email templates - template_type: {template_type}", flush=True)
        print(f"[DEBUG EMAIL] QSO data prepared: {qso_data}", flush=True)
        print(f"[DEBUG EMAIL] Checking template functions: get_email_templates={('get_email_templates' in globals())}, format_email_content={('format_email_content' in globals())}", flush=True)
        print(f"[DEBUG EMAIL] Template type requested: {template_type}", flush=True)
        
        if 'get_email_templates' in globals() and 'format_email_content' in globals():
            print(f"[DEBUG EMAIL] Template functions available, getting templates", flush=True)
            templates = get_email_templates()
            print(f"[DEBUG EMAIL] Available templates: {list(templates.keys())}", flush=True)
            
            if template_type in templates:
                print(f"[DEBUG EMAIL] Using template: {template_type}", flush=True)
                try:
                    subject, body = format_email_content(template_type, qso_data)
                    print(f"[DEBUG EMAIL] Template formatting successful", flush=True)
                    print(f"[DEBUG EMAIL] Subject: {subject}", flush=True)
                    print(f"[DEBUG EMAIL] Body preview: {body[:100]}...", flush=True)
                except Exception as e:
                    print(f"[DEBUG EMAIL] ERROR in format_email_content: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    # Use fallback
                    contact_name = qso_data.get('name', 'OM/YL')
                    if contact_name and contact_name != 'OM/YL' and contact_name.strip():
                        first_name = contact_name.split()[0].strip().capitalize()
                    else:
                        first_name = 'OM/YL'
                    
                    subject = f"QSL {qsltype} - {callsign} via W5XY"
                    body = f"Dear {first_name},\n\nThank you for our QSO on {date} at {formatted_time}.\n\nBest 73,\n\nde W5XY\nOperator"
            else:
                print(f"[DEBUG EMAIL] Template {template_type} not found, using fallback", flush=True)
                # Fallback template with proper formatting
                # Extract first name and capitalize
                contact_name = qso_data.get('name', 'OM/YL')
                if contact_name and contact_name != 'OM/YL' and contact_name.strip():
                    first_name = contact_name.split()[0].strip().capitalize()
                else:
                    first_name = 'OM/YL'
                
                subject = f"QSL {qsltype} - {callsign} via W5XY"
                body = f"Dear {first_name},\n\nThank you for our QSO on {date} at {formatted_time}.\n\nBest 73,\n\nde W5XY\nOperator"
        else:
            print(f"[DEBUG EMAIL] Template functions not available, using fallback", flush=True)
            # Fallback if templates not available with proper formatting
            # Extract first name and capitalize
            contact_name = qso_data.get('name', 'OM/YL')
            if contact_name and contact_name != 'OM/YL' and contact_name.strip():
                first_name = contact_name.split()[0].strip().capitalize()
            else:
                first_name = 'OM/YL'
                
            subject = f"QSL {qsltype} - {callsign} via W5XY"
            body = f"Dear {first_name},\n\nThank you for our QSO on {date} at {formatted_time}.\n\nBest 73,\n\nde W5XY\nOperator"
        
        # Generate PDF path if available (for attachment)
        pdf_path = None
        if 'generate_qsl_card' in globals():
            template_path = "W5XY QSL Card Python TEMPLATE.pdf"
            if os.path.exists(template_path):
                # Build PDF filename: QSL_<CALLSIGN>_<YYYYMMDD>_<HHMMSS>.pdf
                now = datetime.now()
                date_str = now.strftime('%Y%m%d')
                time_str = now.strftime('%H%M%S')
                pdf_filename = f"QSL_{callsign}_{date_str}_{time_str}.pdf"
                pdf_path = os.path.join(tempfile.gettempdir(), pdf_filename)
                generate_qsl_card(template_path, callsign, datetime_str, freq, mode, rst, qsltype, pdf_path)
        # Gmail draft creation strategy - prioritize Gmail API for attachment support
        print(f"[DEBUG EMAIL] About to create Gmail draft: email={email_address}, subject={subject}", flush=True)
        
        # Always try Gmail API first if libraries are available - don't check container status
        gmail_api_success = False
        
        if GMAIL_API_AVAILABLE:
            print(f"[DEBUG EMAIL] Gmail API libraries available, attempting API draft creation", flush=True)
            try:
                client = GmailAPIClient()
                success, draft_message, draft_url = client.create_draft(email_address, subject, body, pdf_path)
                print(f"[DEBUG EMAIL] Gmail API result: success={success}, message={draft_message}", flush=True)
                
                if success:
                    gmail_api_success = True
                    # Mark QSL as sent in Log4OM database when email is successfully created
                    mark_success, mark_message = update_qso_qsl_status(callsign, date, qsl_sent, qsl_received, sent_via, received_date)
                    print(f"[DEBUG EMAIL] Database update result: success={mark_success}, message={mark_message}", flush=True)
                    return jsonify({
                        'success': True,
                        'message': f'{draft_message}. {mark_message}',
                        'drafts_link': draft_url or "https://mail.google.com/mail/u/0/#drafts"
                    })
                else:
                    print(f"[DEBUG EMAIL] Gmail API failed: {draft_message}", flush=True)
            except Exception as e:
                print(f"[DEBUG EMAIL] Exception with Gmail API: {str(e)}", flush=True)
                import traceback
                traceback.print_exc()
        else:
            print(f"[DEBUG EMAIL] Gmail API libraries not available", flush=True)
        
        # If Gmail API didn't work, use web interface fallback
        if not gmail_api_success:
            print(f"[DEBUG EMAIL] Using Gmail web interface fallback", flush=True)
            
            # Create Gmail compose URL with attachment note
            attachment_note = ""
            if pdf_path and os.path.exists(pdf_path):
                attachment_note = f"\n\n[Please attach the QSL card file: {os.path.basename(pdf_path)}]"
            
            body_with_note = body + attachment_note
            
            # URL encode the email components
            to_param = urllib.parse.quote(email_address) if email_address else ""
            subject_param = urllib.parse.quote(subject)
            body_param = urllib.parse.quote(body_with_note)
            
            # Gmail compose URL
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to_param}&su={subject_param}&body={body_param}"
            
            # Mark QSL as sent in database
            mark_success, mark_message = update_qso_qsl_status(callsign, date, qsl_sent, qsl_received, sent_via, received_date)
            print(f"[DEBUG EMAIL] Database update result: success={mark_success}, message={mark_message}", flush=True)
            
            return jsonify({
                'success': True,
                'message': f'Gmail compose window will open. {mark_message}',
                'gmail_url': gmail_url,
                'open_gmail': True,  # Signal frontend to open Gmail
                'attachment_note': f"Please manually attach: {os.path.basename(pdf_path)}" if pdf_path and os.path.exists(pdf_path) else None
            })
    except Exception as e:
        print(f"[DEBUG EMAIL] Exception in email setup: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Email setup error: {str(e)}'})

@app.route('/hamqth/<callsign>')
def hamqth_lookup(callsign):
    """Open HAMQTH lookup for email address"""
    try:
        hamqth_url = f"https://www.hamqth.com/detail.php?callsign={callsign.upper()}"
        webbrowser.open(hamqth_url)
        return jsonify({'success': True, 'message': f'HAMQTH lookup opened for {callsign}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error opening HAMQTH: {str(e)}'})

@app.route('/api/hamqth/<callsign>')
def api_hamqth_lookup(callsign):
    """API endpoint for HAMQTH callsign lookup"""
    try:
        if not hamqth_api.username or not hamqth_api.password:
            return jsonify({'success': False, 'error': 'HAMQTH credentials not configured'}), 400
        data, message = hamqth_api.lookup_callsign(callsign)
        if data:
            # Always return key fields for frontend compatibility
            return jsonify({
                'success': True,
                'email': data.get('email', ''),
                'name': data.get('adr_name', ''),
                'nick': data.get('nick', ''),
                'qth': data.get('qth', ''),
                'country': data.get('country', ''),
                'grid': data.get('grid', ''),
                'lotw': data.get('lotw', ''),
                'eqsl': data.get('eqsl', ''),
                'qsl': data.get('qsl', ''),
                'qsldirect': data.get('qsldirect', ''),
                'message': 'Email found via HAMQTH XML API'
            })
        else:
            return jsonify({'success': False, 'error': message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lookup error: {str(e)}'}), 500

@app.route('/api/hamqth-credentials', methods=['POST'])
def set_hamqth_credentials():
    """Set HAMQTH credentials"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'})
        # Set credentials
        hamqth_api.set_credentials(username, password)
        # Test credentials by attempting to get session
        success, message = hamqth_api.get_session()
        if success:
            # Save credentials to settings file
            try:
                settings_file = "qsl_settings.json"
                settings = {}
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                settings['hamqth_username'] = username
                settings['hamqth_password'] = password
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                return jsonify({
                    'success': True,
                    'message': 'HAMQTH credentials saved and verified'
                })
            except Exception as e:
                return jsonify({
                    'success': True,
                    'message': 'Credentials verified but could not save to file',
                    'warning': str(e)
                })
        else:
            return jsonify({'success': False, 'error': f'Invalid credentials: {message}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error setting credentials: {str(e)}'})

@app.route('/api/mark-qsl', methods=['POST'])
def mark_qsl_sent():
    """Mark QSL as sent in Log4OM database"""
    try:
        # Get form data
        data = request.get_json()
        callsign = data.get('callsign', '').upper()
        qso_date = data.get('date', '')
        qsl_sent = data.get('qsl_sent', '')
        qsl_received = data.get('qsl_received', '')
        sent_via = data.get('sent_via', 'Electronic')
        received_date = data.get('received_date', '')
        
        if not callsign or not qso_date:
            return jsonify({'success': False, 'error': 'Callsign and date are required'})
        
        # Update the Log4OM database
        success, message = update_qso_qsl_status(callsign, qso_date, qsl_sent, qsl_received, sent_via, received_date)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'QSL marking error: {str(e)}'})

def update_qso_qsl_status(callsign, qso_date, qsl_sent, qsl_received, sent_via, received_date):
    """Update QSO record in Log4OM database with QSL status"""
    try:
        print(f"[DEBUG QSL UPDATE] Called with: callsign={callsign}, qso_date={qso_date}, qsl_sent={qsl_sent}, qsl_received={qsl_received}")
        
        db_path = DATABASE_PATH
        if not os.path.exists(db_path):
            return False, "Database file not found"
        
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Format dates for Log4OM format (MM/DD/YYYY 00:00:00)
        from datetime import datetime
        import json
        
        # Get current date for sent date
        sent_date = datetime.now().strftime('%m/%d/%Y 00:00:00')
        
        # Format received date if provided
        if received_date:
            try:
                # Convert from YYYY-MM-DD to MM/DD/YYYY 00:00:00
                parsed_date = datetime.strptime(received_date, '%Y-%m-%d')
                received_date_formatted = parsed_date.strftime('%m/%d/%Y 00:00:00')
            except:
                received_date_formatted = ''
        else:
            received_date_formatted = ''
        
        # Find the QSO record to update
        print(f"[DEBUG QSL UPDATE] Searching for QSO: callsign={callsign}, qso_date={qso_date}", flush=True)
        
        # Try multiple date formats to find the QSO
        search_queries = [
            # Direct date match
            ("callsign = ? AND DATE(qsodate) = DATE(?)", (callsign, qso_date)),
            # Try with different date formats if first fails
            ("callsign = ? AND (DATE(qsodate) = DATE(?) OR qsodate LIKE ?)", (callsign, qso_date, f"{qso_date}%")),
            # Try searching by callsign only and get the most recent
            ("callsign = ?", (callsign,))
        ]
        
        qso_record = None
        query_used = None
        
        for i, (where_clause, params) in enumerate(search_queries):
            print(f"[DEBUG QSL UPDATE] Trying search method {i+1}: {where_clause} with params {params}", flush=True)
            cursor.execute(f"""
                SELECT qsoid, qsoconfirmations, qsodate FROM Log 
                WHERE {where_clause}
                ORDER BY qsodate DESC 
                LIMIT 1
            """, params)
            
            qso_record = cursor.fetchone()
            if qso_record:
                query_used = i + 1
                print(f"[DEBUG QSL UPDATE] Found QSO using search method {query_used}: {qso_record}", flush=True)
                break
            else:
                print(f"[DEBUG QSL UPDATE] No QSO found with search method {i+1}", flush=True)
        
        print(f"[DEBUG QSL UPDATE] Final QSO search result: {qso_record}", flush=True)
        if not qso_record:
            # List all QSOs for this callsign to help debug
            print(f"[DEBUG QSL UPDATE] No QSO found. Listing all QSOs for {callsign}:", flush=True)
            cursor.execute("SELECT qsoid, qsoconfirmations, qsodate FROM Log WHERE callsign = ? ORDER BY qsodate DESC", (callsign,))
            all_records = cursor.fetchall()
            for record in all_records:
                print(f"[DEBUG QSL UPDATE] Available QSO: {record}", flush=True)
            
            conn.close()
            return False, f"QSO record not found for {callsign} on {qso_date}. Found {len(all_records)} total QSOs for {callsign}."
        
        qso_id = qso_record[0]
        existing_confirmations = qso_record[1] or "{}"
        qso_date_found = qso_record[2]
        print(f"[DEBUG QSL UPDATE] Using QSO ID: {qso_id}, date: {qso_date_found}, existing confirmations: {existing_confirmations}", flush=True)
        
        # Parse existing QSL confirmations JSON
        try:
            confirmations = json.loads(existing_confirmations)
            print(f"[DEBUG QSL UPDATE] Parsed confirmations type: {type(confirmations)}, content: {confirmations}", flush=True)
        except:
            confirmations = []
            print(f"[DEBUG QSL UPDATE] Failed to parse confirmations, using empty list", flush=True)
        
        # Log4OM stores confirmations as a list of objects like:
        # [{"CT":"QSL","S":"Requested","R":"Requested","SV":"Electronic","RV":"Electronic"}]
        # We need to find and update the QSL entry
        
        # Update QSL status fields in Log4OM format
        if isinstance(confirmations, list):
            # Find the QSL confirmation entry
            qsl_entry = None
            for entry in confirmations:
                if isinstance(entry, dict) and entry.get('CT') == 'QSL':
                    qsl_entry = entry
                    break
            
            # If no QSL entry exists, create one
            if not qsl_entry:
                qsl_entry = {
                    "CT": "QSL",
                    "S": "No",
                    "R": "No",
                    "SV": "Electronic",
                    "RV": "Electronic"
                }
                confirmations.append(qsl_entry)
            
            # Update the QSL entry
            if qsl_sent:
                qsl_entry['S'] = qsl_sent
                if qsl_sent == 'Yes':
                    qsl_entry['SV'] = sent_via if sent_via else 'Electronic'
            
            if qsl_received:
                qsl_entry['R'] = qsl_received
                if qsl_received == 'Yes':
                    qsl_entry['RV'] = 'Electronic'  # Default for received via
            
            print(f"[DEBUG QSL UPDATE] Updated QSL entry: {qsl_entry}", flush=True)
        else:
            # If confirmations is not a list, create a new structure
            confirmations = [{
                "CT": "QSL",
                "S": qsl_sent if qsl_sent else "No",
                "R": qsl_received if qsl_received else "No", 
                "SV": sent_via if sent_via else "Electronic",
                "RV": "Electronic"
            }]
            print(f"[DEBUG QSL UPDATE] Created new confirmations structure: {confirmations}", flush=True)
        
        # Convert back to JSON
        updated_confirmations = json.dumps(confirmations)
        print(f"[DEBUG QSL UPDATE] Updated confirmations: {updated_confirmations}")
        
        # Update the QSO record
        cursor.execute("""
            UPDATE Log 
            SET qsoconfirmations = ?,
                qslmsg = 'EQSL sent via W5XY QSL Card Creator'
            WHERE qsoid = ?
        """, (updated_confirmations, qso_id))
        
        conn.commit()
        print(f"[DEBUG QSL UPDATE] Database update committed for QSO ID: {qso_id}")
        conn.close()
        
        status_msg = []
        if qsl_sent:
            status_msg.append(f"QSL Sent: {qsl_sent}")
        if qsl_received:
            status_msg.append(f"QSL Received: {qsl_received}")
        
        return True, f"QSL status updated for {callsign}. {', '.join(status_msg)}"
        
    except Exception as e:
        return False, f"Database update error: {str(e)}"

@app.route('/api/download-database', methods=['POST'])
def api_download_database():
    """Download database from OneDrive"""
    try:
        success, message = download_database_from_onedrive()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database download error: {str(e)}'
        })

@app.route('/api/upload-database-to-onedrive', methods=['POST'])
def api_upload_database_to_onedrive():
    """Upload local database changes back to PC/OneDrive"""
    try:
        success, message = upload_database_to_pc()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database upload error: {str(e)}'
        })

@app.route('/api/database-info')
def api_database_info():
    """Get current database information with debug details"""
    try:
        settings = app_settings.settings if app_settings else {}
        local_path = settings.get('last_database', 'Log4OM db.SQLite')
        
        # Check if database exists
        db_exists = os.path.exists(local_path)
        
        # Initialize response data
        response_data = {
            'exists': db_exists,
            'database_path': local_path,
            'debug': {
                'is_symlink': os.path.islink(local_path) if db_exists else False,
                'real_path': os.path.realpath(local_path) if db_exists else None,
                'container_cwd': os.getcwd(),
                'container_files': os.listdir('.') if os.path.exists('.') else []
            }
        }
        
        if not db_exists:
            response_data['message'] = 'No database loaded'
            return jsonify(response_data)
        
        # Get database info
        file_size = os.path.getsize(local_path)
        mod_time = os.path.getmtime(local_path)
        
        # Get QSO count using safe database access
        qso_count = safe_db.get_qso_count()
        
        # Check for Syncthing information
        syncthing_info = {}
        real_path = os.path.realpath(local_path)
        is_symlink = os.path.islink(local_path)
        
        # First, check if we can detect Syncthing from the path itself
        if real_path and 'SyncthingFolders' in real_path:
            syncthing_info['detected_from'] = 'path_analysis'
            syncthing_info['folder_path'] = os.path.dirname(real_path)
            # Extract folder name from path
            if '/SyncthingFolders/' in real_path:
                folder_name = real_path.split('/SyncthingFolders/')[1].split('/')[0]
                syncthing_info['folder_name'] = folder_name
            syncthing_info['status'] = 'detected_via_container'
            syncthing_info['note'] = 'Detected from symlink path (Docker container)'
        
        # Look for Syncthing folder markers (for direct access)
        for potential_dir in [
            "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database",
            os.path.dirname(real_path) if real_path else None
        ]:
            if potential_dir and os.path.exists(potential_dir):
                stfolder_path = os.path.join(potential_dir, '.stfolder')
                if os.path.exists(stfolder_path):
                    syncthing_info['detected_from'] = 'stfolder_metadata'
                    # Find syncthing metadata file
                    for file in os.listdir(stfolder_path):
                        if file.startswith('syncthing-folder-'):
                            try:
                                with open(os.path.join(stfolder_path, file), 'r') as f:
                                    content = f.read()
                                    for line in content.split('\n'):
                                        if line.startswith('folderID:'):
                                            syncthing_info['folder_id'] = line.split(':', 1)[1].strip()
                                        elif line.startswith('created:'):
                                            syncthing_info['created'] = line.split(':', 1)[1].strip()
                                break
                            except:
                                pass
                    break
        
        # Update response with full information
        response_data.update({
            'size_mb': round(file_size / (1024 * 1024), 1),
            'modified': datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S"),
            'qso_count': qso_count,
            'syncthing': syncthing_info if syncthing_info else None,
            'debug': {
                **response_data['debug'],
                'file_size_bytes': file_size,
                'modification_timestamp': mod_time,
                'syncthing_search_paths': [
                    "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database",
                    os.path.dirname(real_path) if real_path else None
                ]
            }
        })
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'exists': False,
            'error': f'Database info error: {str(e)}',
            'debug': {
                'exception_type': type(e).__name__,
                'exception_message': str(e),
                'container_cwd': os.getcwd(),
                'traceback': str(e)
            }
        })

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update application settings"""
    try:
        if request.method == 'GET':
            # Return current settings (excluding sensitive data)
            settings = app_settings.settings if app_settings else {}
            safe_settings = settings.copy()
            if 'hamqth_password' in safe_settings:
                safe_settings['hamqth_password'] = '***' if safe_settings['hamqth_password'] else ''
            return jsonify(safe_settings)
            
        elif request.method == 'POST':
            # Update settings
            data = request.get_json()
            if app_settings:
                # Update specific settings
                for key, value in data.items():
                    if key in ['auto_download_database', 'pdf_generation_enabled', 'poppler_enabled']:
                        app_settings.settings[key] = value
                
                # Save settings
                app_settings.save_settings()
                return jsonify({
                    'success': True,
                    'message': 'Settings updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Settings manager not available'
                })
        
        # Default return for any other method
        return jsonify({
            'success': False,
            'error': 'Invalid request method'
        })
                
    except Exception as e:
               return jsonify({
            'success': False,
            'error': f'Settings error: {str(e)}'
        })

@app.route('/api/qsos')
def api_qsos():
    """API endpoint to get QSOs data as JSON"""
    try:
        # Use safe database access - include QSL confirmation data
        rows = safe_db.execute_query("""
            SELECT callsign, qsodate, freq, mode, rstsent, rstrcvd, email, qsoconfirmations
            FROM Log 
            ORDER BY qsodate DESC 
            LIMIT 100
        """, read_only=True)
        
        if rows is None:
            return jsonify({'error': 'Database access error - please try again'})
        
        # Handle case where rows might be an integer (should not happen for SELECT, but defensive coding)
        if isinstance(rows, int):
            return jsonify({'error': 'Unexpected database response - please try again'})
        
        qsos = []
        for row in rows:
            # Parse datetime from qsodate field
            qso_datetime = row[1] if len(row) > 1 else None
            
            # Split date and time
            if qso_datetime:
                try:
                    # Remove 'Z' and split date and time
                    dt_clean = qso_datetime.replace('Z', '')
                    if ' ' in dt_clean:
                        date_part, time_part = dt_clean.split(' ')
                        # Ensure time is shown as UTC
                        if not time_part.endswith(' UTC'):
                            time_part = time_part + ' UTC'
                    else:
                        date_part = dt_clean
                        time_part = ''
                except Exception:
                    date_part = qso_datetime
                    time_part = ''
            else:
                date_part = ''
                time_part = ''
            
            # Parse QSL confirmation data
            qsl_sent = "No"
            qsl_received = "No"
            qso_confirmations = row[7] if len(row) > 7 and row[7] else ""
            
            if qso_confirmations:
                try:
                    import json
                    confirmations = json.loads(qso_confirmations)
                    # Look for QSL card confirmations (not eQSL or LOTW)
                    for conf in confirmations:
                        if conf.get('CT') == 'QSL':  # QSL card (not eQSL)
                            # Only show "Yes" if actually sent/received, ignore "Requested"
                            sent_status = conf.get('S', 'No')
                            received_status = conf.get('R', 'No')
                            qsl_sent = "Yes" if sent_status == "Yes" else "No"
                            qsl_received = "Yes" if received_status == "Yes" else "No"
                            break
                except:
                    pass  # If JSON parsing fails, default to "No"
            
            qso_data = {
                'callsign': row[0],
                'date': date_part,
                'time': time_part,
                'frequency': str(row[2]) if row[2] else '',
                'mode': row[3] if row[3] else '',
                'rst_sent': row[4] if row[4] else '59',
                'rst_received': row[5] if row[5] else '59',
                'email': row[6] if row[6] else '',
                'qsl_sent': qsl_sent,
                'qsl_received': qsl_received
            }
            qsos.append(qso_data)
        
        return jsonify({
            'count': len(qsos),
            'qsos': qsos
        })
        
    except Exception as e:
        return jsonify({'error': f"Database error: {str(e)}"})

@app.route('/qsos/<callsign>')
def get_qso_by_callsign(callsign):
    """Get QSO data for a specific callsign"""
    try:
        callsign = callsign.upper()
        
        # Query database for QSOs with this callsign
        rows = safe_db.execute_query("""
            SELECT callsign, qsodate, freq, mode, rstsent, rstrcvd, email, qsoconfirmations
            FROM Log 
            WHERE UPPER(callsign) = ?
            ORDER BY qsodate DESC
        """, (callsign,), read_only=True)
        
        if not rows:
            return jsonify({'error': f'No QSOs found for {callsign}', 'count': 0})
        
        qsos = []
        for row in rows:
            # Parse datetime - handle Log4OM format
            qso_datetime = row[1]
            
            if isinstance(qso_datetime, str):
                # Use the same parsing logic as QSL generation and email system
                try:
                    # Remove 'Z' and split date and time
                    dt_clean = qso_datetime.replace('Z', '')
                    if ' ' in dt_clean:
                        date_part, time_part = dt_clean.split(' ')
                        # Convert to HTML date format if needed
                        if '/' in date_part:
                            # Handle MM/DD/YYYY format
                            try:
                                dt = datetime.strptime(date_part, '%m/%d/%Y')
                                date_part = dt.strftime('%Y-%m-%d')
                            except ValueError:
                                pass
                    else:
                        date_part = dt_clean
                        time_part = ''
                except Exception:
                    # Fallback: try original parsing methods
                    try:
                        # Log4OM format: MM/DD/YYYY HH:MM:SS
                        dt = datetime.strptime(qso_datetime, '%m/%d/%Y %H:%M:%S')
                        date_part = dt.strftime('%Y-%m-%d')  # HTML date input format
                        time_part = dt.strftime('%H:%M')     # HTML time format
                    except ValueError:
                        try:
                            # Alternative format: YYYY-MM-DD HH:MM:SS
                            dt = datetime.strptime(qso_datetime, '%Y-%m-%d %H:%M:%S')
                            date_part = dt.strftime('%Y-%m-%d')
                            time_part = dt.strftime('%H:%M')
                        except ValueError:
                            # If parsing fails, try to extract just date
                            date_part = qso_datetime.split(' ')[0] if ' ' in qso_datetime else qso_datetime
                            time_part = ''
            else:
                date_part = str(qso_datetime)
                time_part = ''
            
            # Parse QSL confirmations
            qsl_sent = "No"
            qsl_received = "No"
            if row[7]:  # qsoconfirmations field
                try:
                    confirmations = json.loads(row[7])
                    qsl_sent = confirmations.get('eqsl_sent', 'No')
                    qsl_received = confirmations.get('eqsl_received', 'No')
                except:
                    pass
            
            qso_data = {
                'callsign': row[0],
                'date': date_part,
                'time': time_part,
                'frequency': str(row[2]) if row[2] else '',
                'mode': row[3] if row[3] else '',
                'rst_sent': row[4] if row[4] else '59',
                'rst_received': row[5] if row[5] else '59',
                'email': row[6] if row[6] else '',
                'qsl_sent': qsl_sent,
                'qsl_received': qsl_received
            }
            qsos.append(qso_data)
        
        return jsonify({
            'count': len(qsos),
            'qsos': qsos
        })
        
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}', 'count': 0})

@app.route('/api/email-templates')
def api_get_email_templates():
    """API endpoint to get available email templates"""
    templates = []
    for key, template in EMAIL_TEMPLATES.items():
        templates.append({
            'key': key,
            'name': template['name']
        })
    return jsonify({'templates': templates})

@app.route('/api/test-email-template', methods=['POST'])
def test_email_template():
    """Test email template functionality"""
    try:
        print("[DEBUG TEST] Testing email template functionality", flush=True)
        
        # Create test QSO data
        test_data = {
            'callsign': 'W1AW',
            'name': 'John Smith',
            'qso_date': '2024-01-15',
            'qso_time': '1230',
            'frequency': '14.230',
            'mode': 'SSB',
            'rst_sent': '59',
            'rst_rcvd': '59'
        }
        
        # Test template functions availability
        templates_available = 'get_email_templates' in globals() and 'format_email_content' in globals()
        print(f"[DEBUG TEST] Template functions available: {templates_available}", flush=True)
        
        if templates_available:
            templates = get_email_templates()
            print(f"[DEBUG TEST] Available templates: {list(templates.keys())}", flush=True)
            
            # Test formatting
            template_type = 'qsl_confirmation'
            if template_type in templates:
                print(f"[DEBUG TEST] Testing template: {template_type}", flush=True)
                subject, body = format_email_content(template_type, test_data)
                print(f"[DEBUG TEST] Subject: {subject}", flush=True)
                print(f"[DEBUG TEST] Body: {body[:200]}...", flush=True)
                
                return jsonify({
                    'success': True,
                    'subject': subject,
                    'body': body,
                    'template_type': template_type,
                    'test_data': test_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Template {template_type} not found',
                    'available_templates': list(templates.keys())
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Template functions not available'
            })
            
    except Exception as e:
        print(f"[DEBUG TEST] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e)
        })

if __name__ == '__main__':
    print("🌐 Starting QSL Card Creator Web Application")
    print("=" * 50)
    
    # Check and download database if enabled
    try:
        db_success, db_message = check_and_download_database()
        if db_success:
            print(f"Database: ✓ {db_message}")
        else:
            print(f"Database: ⚠️ {db_message}")
    except Exception as e:
        print(f"Database check error: {e}")
    
    # Check system status
    print(f"Poppler available: {'✓' if check_poppler()[0] else '✗'}")
    print(f"Template file: {'✓' if os.path.exists('W5XY QSL Card Python TEMPLATE.pdf') else '✗'}")
    print(f"Database file: {'✓' if os.path.exists('Log4OM db.SQLite') else '✗'}")
    
    # Load HAMQTH credentials if available
    if load_hamqth_credentials():
        print("HAMQTH credentials: ✓")
    else:
        print("HAMQTH credentials: ✗ (set via web interface)")
    
    # Check settings
    if app_settings:
        settings = app_settings.settings
        print(f"PDF generation: {'✓' if settings.get('pdf_generation_enabled') else '✗'}")
        print(f"Auto database sync: {'✓' if settings.get('auto_download_database') else '✗'}")
    
    print("\n🚀 Starting web server...")
    
    # Require SSL certificates for production-ready HTTPS-only deployment
    # Always run in HTTP mode for Docker/Nginx
    print("🌍 Starting QSL Card Creator in HTTP mode for Docker/Nginx")
    app.run(host='0.0.0.0', port=5553, debug=False)
