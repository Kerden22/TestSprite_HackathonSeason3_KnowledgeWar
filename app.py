from dotenv import load_dotenv

# .env must load before any module reads GEMINI_API_KEY / YOUTUBE_API_KEY
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
import os
import requests
import json
import re
import urllib3
from werkzeug.security import generate_password_hash, check_password_hash
import time
import google.generativeai as genai
from services.roadmap_service import build_learning_roadmap

# SSL uyarılarını kapatma
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TR_TZ = timezone(timedelta(hours=3))

def now_tr():
    """TR duvar-saati (naive) — DB'deki naive değerlerle karşılaştırmak için."""
    return datetime.now(TR_TZ).replace(tzinfo=None)

def now_tr_str():
    """SQLite CURRENT_TIMESTAMP ile aynı format, TR saatiyle."""
    return now_tr().strftime('%Y-%m-%d %H:%M:%S')

# Gemini API konfigürasyonu
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
if GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'btk-auth-secret-key-2024')
CORS(app)

# Veritabanı oluşturma
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Users tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Turnuvalar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            question_count INTEGER DEFAULT 15,
            duration_minutes INTEGER DEFAULT 45,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Sorular tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
        )
    ''')
    
    # Turnuva katılımcıları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tournament_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            total_score INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
        )
    ''')

    # Kullanıcı cevapları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tournament_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    # Kullanıcı profilleri tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            goal TEXT NOT NULL,
            level TEXT NOT NULL,
            time_commitment TEXT NOT NULL,
            learning_style TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Seçilen kurslar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_title TEXT NOT NULL,
            course_link TEXT NOT NULL,
            course_description TEXT,
            roadmap_sections TEXT,
            status TEXT DEFAULT 'active',
            completed_at TIMESTAMP NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def update_database_schema():
    """Mevcut veritabanı şemasını güncelle"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        
        cursor.execute("PRAGMA table_info(tournaments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'question_count' not in columns:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN question_count INTEGER DEFAULT 15')
            print("question_count sütunu eklendi")
            
        if 'duration_minutes' not in columns:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN duration_minutes INTEGER DEFAULT 45')
            print("duration_minutes sütunu eklendi")
        
        cursor.execute("PRAGMA table_info(user_courses)")
        user_courses_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in user_courses_columns:
            cursor.execute('ALTER TABLE user_courses ADD COLUMN status TEXT DEFAULT "active"')
            print("user_courses status sütunu eklendi")
            
        if 'completed_at' not in user_courses_columns:
            cursor.execute('ALTER TABLE user_courses ADD COLUMN completed_at TIMESTAMP NULL')
            print("user_courses completed_at sütunu eklendi")
        
        conn.commit()
        conn.close()
        print("Veritabanı şeması güncellendi")
        
    except Exception as e:
        print(f"Veritabanı güncelleme hatası: {e}")

def seed_default_test_user():
    """Her deploy'da TestSprite için varsayılan test kullanıcısını garanti et (Render SQLite ephemeral)."""
    email = os.getenv('DEFAULT_TEST_USER_EMAIL', 'k.erden03@gmail.com')
    password = os.getenv('DEFAULT_TEST_USER_PASSWORD', '123456')
    first_name = os.getenv('DEFAULT_TEST_USER_FIRST_NAME', 'Kerem')
    last_name = os.getenv('DEFAULT_TEST_USER_LAST_NAME', 'Test')

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            cursor.execute(
                'UPDATE users SET password_hash = ?, first_name = ?, last_name = ? WHERE email = ?',
                (password_hash, first_name, last_name, email)
            )
        else:
            cursor.execute(
                'INSERT INTO users (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)',
                (first_name, last_name, email, password_hash)
            )
        conn.commit()
        conn.close()
        print(f"Default test user ready: {email}")
    except Exception as e:
        print(f"Default test user seed error: {e}")

# Veritabanını başlatma
init_db()
update_database_schema()
seed_default_test_user()

def analyze_user_profile(responses):
    """Kullanıcı yanıtlarını analiz ederek profil oluştur"""
    try:
        # Basit profil oluştur (Gemini API olmadan)
        level_mapping = {
            "none": "başlangıç",
            "basic": "başlangıç",
            "intermediate": "orta",
            "advanced": "ileri",
            "Hiç bilmiyorum": "başlangıç",
            "Temel bilgim var": "başlangıç",
            "Orta seviye": "orta",
            "İleri seviye": "ileri",
            "Complete beginner": "başlangıç",
            "Basic knowledge": "başlangıç",
            "Intermediate": "orta",
            "Advanced": "ileri",
        }
        
        style_mapping = {
            "Videolu anlatım": "görsel ve işitsel öğrenme",
            "Uygulamalı görevler": "pratik odaklı öğrenme",
            "Proje odaklı": "proje tabanlı öğrenme",
            "Metin ve dökümanla öğrenme": "okuma ve yazma odaklı öğrenme"
        }
        
        return {
            "hedef": f"{responses['skill']} öğrenerek {responses['goal']}",
            "seviye": level_mapping.get(responses['level'], "başlangıç"),
            "yaklasim": "genel öğrenme",
            "sure": f"{responses['time']} süreyle",
            "ozel_ihtiyaclar": "Yok"
        }
        
    except Exception as e:
        print(f"Profil analizi hatası: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def loginIndex():
    return render_template('login-register.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')

@app.route('/tournament')
def tournament():
    return render_template('tournament.html')

@app.route('/learn')
def learn():
    return render_template('learn.html')

@app.route('/tournament-admin')
def tournament_admin():
    return render_template('tournament-admin.html')

@app.route('/battle')
def battle():
    return render_template('battle.html')

@app.route('/test')
def test():
    return render_template('test.html')



@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Veri doğrulama
        required_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        # Email formatı kontrolü
        if '@' not in data['email']:
            return jsonify({'error': 'Geçerli bir email adresi giriniz'}), 400
        
        # Şifre uzunluğu kontrolü
        if len(data['password']) < 6:
            return jsonify({'error': 'Şifre en az 6 karakter olmalıdır'}), 400
        
        # Veritabanına kaydet
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Email kontrolü
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bu email adresi zaten kayıtlı'}), 400
        
        # Şifreyi hashle
        password_hash = generate_password_hash(data['password'])
        
        # Kullanıcıyı kaydet
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (data['first_name'], data['last_name'], data['email'], password_hash))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # JWT token oluştur
        token = jwt.encode({
            'user_id': user_id,
            'email': data['email'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Kayıt başarılı!',
            'token': token,
            'user': {
                'id': user_id,
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Veri doğrulama
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email ve şifre gereklidir'}), 400
        
        # Kullanıcıyı bul
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, first_name, last_name, email, password_hash 
            FROM users WHERE email = ?
        ''', (data['email'],))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # Şifre kontrolü
        if not check_password_hash(user[4], data['password']):
            conn.close()
            return jsonify({'error': 'Email veya şifre hatalı'}), 401
        
        # Son giriş zamanını güncelle
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (user[0],))
        
        conn.commit()
        conn.close()
        
        # JWT token oluştur
        token = jwt.encode({
            'user_id': user[0],
            'email': user[3],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Giriş başarılı!',
            'token': token,
            'user': {
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'email': user[3]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        # Kullanıcı bilgilerini getir
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, first_name, last_name, email, created_at, last_login
            FROM users WHERE id = ?
        ''', (payload['user_id'],))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        return jsonify({
            'user': {
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'email': user[3],
                'created_at': user[4],
                'last_login': user[5]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Tüm kullanıcıları listele (admin için)"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, first_name, last_name, email, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'email': user[3],
                'created_at': user[4],
                'last_login': user[5]
            })
        
        return jsonify({'users': user_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/analyze-profile', methods=['POST'])
def analyze_profile():
    """Kullanıcı profilini analiz et ve Gemini + YouTube ile yol haritası üret"""
    try:
        print("=== ANALYZE PROFILE API CALLED ===")
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        required_fields = ['skill', 'goal', 'level', 'time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        profile = analyze_user_profile(data)
        if not profile:
            return jsonify({'error': 'Profil analizi başarısız'}), 500
        
        lang = resolve_content_lang(data.get('lang') or request.headers.get('X-Content-Lang'))
        roadmap_result = build_learning_roadmap(
            data['skill'],
            data['goal'],
            data['level'],
            data['time'],
            lang,
        )
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_profiles (user_id, skill, goal, level, time_commitment, learning_style)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (payload['user_id'], data['skill'], data['goal'], data['level'], data['time'], 'Genel öğrenme'))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'profile': profile,
            'roadmap_title': roadmap_result['roadmap_title'],
            'roadmap_steps': roadmap_result['roadmap_steps'],
            'total_steps': roadmap_result['total_steps'],
        }), 200
        
    except Exception as e:
        print(f"ERROR in analyze_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/add-course-to-roadmap', methods=['POST'])
def add_course_to_roadmap():
    """Kursu kullanıcının yol haritasına ekle"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        required_fields = ['roadmap_title', 'roadmap_steps']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        roadmap_steps = data['roadmap_steps']
        if not isinstance(roadmap_steps, list) or len(roadmap_steps) == 0:
            return jsonify({'error': 'roadmap_steps geçerli bir liste olmalıdır'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        course_description = data.get('course_description') or data['roadmap_title']
        
        cursor.execute('''
            INSERT INTO user_courses (user_id, course_title, course_link, course_description, roadmap_sections, added_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            payload['user_id'],
            data['roadmap_title'],
            '#',
            course_description,
            json.dumps(roadmap_steps),
            now_tr_str(),
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Yol haritası kaydedildi'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/get-user-roadmap', methods=['GET'])
def get_user_roadmap():
    """Kullanıcının yol haritasını getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        # Kullanıcının profili ve kurslarını getir
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Profil bilgileri
        cursor.execute('''
            SELECT skill, goal, level, time_commitment, learning_style, created_at
            FROM user_profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (payload['user_id'],))
        
        profile = cursor.fetchone()
        
        # Kurslar (sadece aktif olanlar)
        cursor.execute('''
            SELECT id, course_title, course_link, course_description, roadmap_sections, added_at
            FROM user_courses WHERE user_id = ? AND status = 'active' ORDER BY added_at DESC
        ''', (payload['user_id'],))
        
        courses = cursor.fetchall()
        
        roadmap_data = {
            'profile': None,
            'courses': []
        }
        
        if profile:
            roadmap_data['profile'] = {
                'skill': profile[0],
                'goal': profile[1],
                'level': profile[2],
                'time_commitment': profile[3],
                'learning_style': profile[4],
                'created_at': profile[5]
            }
        
        for course in courses:
            course_id, course_title, course_link, course_description, roadmap_sections_raw, added_at = course
            roadmap_steps = []
            if roadmap_sections_raw:
                try:
                    roadmap_steps = json.loads(roadmap_sections_raw)
                except Exception:
                    roadmap_steps = []

            roadmap_data['courses'].append({
                'title': course_title,
                'link': course_link,
                'description': course_description,
                'roadmap_steps': roadmap_steps,
                'added_at': added_at
            })

        conn.commit()
        conn.close()
        
        return jsonify(roadmap_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/update-user-progress', methods=['POST'])
def update_user_progress():
    """Kullanıcının yol haritası ilerlemesini güncelle"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        # Veri doğrulama
        if 'completed_step' not in data or 'roadmap_steps' not in data:
            return jsonify({'error': 'completed_step ve roadmap_steps alanları gereklidir'}), 400
        
        # Veritabanına kaydet
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Kullanıcının en son kursunu bul
        cursor.execute('''
            SELECT id, course_title, roadmap_sections
            FROM user_courses 
            WHERE user_id = ? 
            ORDER BY added_at DESC 
            LIMIT 1
        ''', (payload['user_id'],))
        
        course = cursor.fetchone()
        if not course:
            conn.close()
            return jsonify({'error': 'Kullanıcının aktif kursu bulunamadı'}), 404
        
        course_id, course_title, existing_roadmap = course
        
        updated_roadmap = json.dumps(data['roadmap_steps'])
        steps = data['roadmap_steps']
        all_completed = (
            isinstance(steps, list)
            and len(steps) > 0
            and all(step.get('status') == 'completed' for step in steps)
        )
        
        cursor.execute('''
            UPDATE user_courses 
            SET roadmap_sections = ?
            WHERE id = ?
        ''', (updated_roadmap, course_id))
        
        if all_completed:
            cursor.execute('''
                UPDATE user_courses
                SET status = 'completed', completed_at = ?
                WHERE id = ?
            ''', (now_tr_str(), course_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'İlerleme başarıyla kaydedildi',
            'completed_step': data['completed_step'],
            'course_title': course_title,
            'course_completed': all_completed,
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/complete-course', methods=['POST'])
def complete_course():
    """Kullanıcının kursunu tamamlandı olarak işaretle"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        # Veritabanına kaydet
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Kullanıcının en son kursunu bul
        cursor.execute('''
            SELECT id FROM user_courses 
            WHERE user_id = ? AND status = 'active'
            ORDER BY added_at DESC 
            LIMIT 1
        ''', (payload['user_id'],))
        
        course = cursor.fetchone()
        if not course:
            conn.close()
            return jsonify({'error': 'Tamamlanacak aktif kurs bulunamadı'}), 404
        
        course_id = course[0]
        
        # Kursu tamamlandı olarak işaretle
        cursor.execute('''
            UPDATE user_courses 
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        ''', (now_tr_str(), course_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Kurs başarıyla tamamlandı! Tebrikler!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

def clean_and_fix_json(json_text):
    """JSON metnini temizler ve eksik kapanan tırnak işaretlerini düzeltir"""
    try:
        # Önce normal JSON parse dene
        json.loads(json_text)
        return json_text
    except json.JSONDecodeError as e:
        print(f"JSON temizleme gerekli: {e}")
        
        # Markdown kod bloğu varsa temizle
        if json_text.startswith('```'):
            json_text = re.sub(r'^```(?:json)?\s*', '', json_text)
            json_text = re.sub(r'\s*```$', '', json_text)
        
        # Eksik kapanan tırnak işaretlerini düzelt
        lines = json_text.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Satırda açık tırnak işareti varsa ve kapanmamışsa
            if '"' in line:
                quote_count = line.count('"')
                if quote_count % 2 != 0:  # Tek sayıda tırnak işareti varsa
                    # Satırın sonuna tırnak işareti ekle
                    if not line.strip().endswith('"'):
                        line = line.rstrip() + '"'
                    # Eğer satır virgülle bitmiyorsa ve sonraki satır yoksa virgül ekle
                    if not line.strip().endswith(',') and not line.strip().endswith(']') and not line.strip().endswith('}'):
                        line = line.rstrip() + ','
            
            fixed_lines.append(line)
        
        # Eksik kapanan parantezleri düzelt
        fixed_text = '\n'.join(fixed_lines)
        
        # Eğer JSON hala tamamlanmamışsa, basit bir yapı oluştur
        if not fixed_text.strip().endswith('}'):
            # Son soruyu tamamla
            if not fixed_text.strip().endswith(']'):
                fixed_text = fixed_text.rstrip().rstrip(',') + ']'
            if not fixed_text.strip().endswith('}'):
                fixed_text = fixed_text.rstrip().rstrip(',') + '}'
        
        # Son bir deneme daha
        try:
            json.loads(fixed_text)
            return fixed_text
        except json.JSONDecodeError:
            # Hala hata varsa, basit bir JSON yapısı oluştur
            return '{"questions": []}'
        
    except Exception as e:
        print(f"JSON temizleme hatası: {e}")
        return '{"questions": []}'

def extract_questions_from_text(text, topic, max_questions=15):
    """AI yanıtından soruları manuel olarak çıkarır"""
    try:
        questions = []
        lines = text.split('\n')
        
        current_question = None
        current_options = []
        option_count = 0
        
        for line in lines:
            line = line.strip()
            
            # Soru satırını bul
            if '"question"' in line or 'question' in line.lower():
                # Önceki soruyu kaydet
                if current_question and len(current_options) == 4:
                    questions.append({
                        "question": current_question,
                        "options": current_options,
                        "correct_option": "A"  # Varsayılan
                    })
                
                # Yeni soru başlat
                current_question = extract_quoted_text(line)
                current_options = []
                option_count = 0
                
            # Seçenek satırını bul
            elif '"options"' in line or 'options' in line.lower():
                continue
            elif line.startswith('"') and ('"' in line[1:]) and option_count < 4:
                option_text = extract_quoted_text(line)
                if option_text:
                    current_options.append(option_text)
                    option_count += 1
        
        # Son soruyu ekle
        if current_question and len(current_options) == 4:
            questions.append({
                "question": current_question,
                "options": current_options,
                "correct_option": "A"  # Varsayılan
            })
        
        # Soru sayısını sınırla
        if len(questions) > max_questions:
            questions = questions[:max_questions]
        
        return questions
        
    except Exception as e:
        print(f"Soru çıkarma hatası: {e}")
        return []

def extract_quoted_text(line):
    """Satırdan tırnak işaretleri arasındaki metni çıkarır"""
    try:
        # İlk tırnak işaretini bul
        start = line.find('"')
        if start == -1:
            return None
        
        # İkinci tırnak işaretini bul
        end = line.find('"', start + 1)
        if end == -1:
            return None
        
        return line[start + 1:end]
    except:
        return None

SUPPORTED_CONTENT_LANGS = ('en', 'tr')

def resolve_content_lang(lang):
    """Normalize UI/content language for Gemini prompts."""
    if not lang:
        return 'en'
    normalized = str(lang).lower().strip()
    return normalized if normalized in SUPPORTED_CONTENT_LANGS else 'en'

_TURKISH_CHAR_RE = re.compile(r'[çğıöşüÇĞİÖŞÜ]')
_TURKISH_WORD_RE = re.compile(
    r'\b(bir|için|icin|olan|değil|degil|doğru|dogru|yanlış|yanlis|aşağıdaki|asagidaki|'
    r'hangisi|sorusu|şıkkı|sikki|cevap|nedir|nasıl|nasil|veya|ancak|lütfen|lutfen|'
    r'konuda|konusu|seçenek|secenek|açıklayın|aciklayin|tanımlayın|tanimlayin)\b',
    re.IGNORECASE,
)

def _looks_turkish(text):
    if not text:
        return False
    s = str(text)
    if _TURKISH_CHAR_RE.search(s):
        return True
    return bool(_TURKISH_WORD_RE.search(s))

def questions_need_translation(questions, target_lang):
    if resolve_content_lang(target_lang) != 'en':
        return False
    for q in questions:
        if _looks_turkish(q.get('question', '')):
            return True
        for opt in q.get('options', []):
            if _looks_turkish(opt):
                return True
    return False

def ensure_questions_language(questions, lang):
    """When UI is English, normalize quiz text to English (translate if needed)."""
    lang = resolve_content_lang(lang)
    if lang != 'en' or not questions:
        return questions
    print(f'ensure_questions_language: enforcing English for {len(questions)} question(s)')
    return translate_questions_with_gemini(questions, 'en')

def _build_question_generation_prompt(topic, question_count, lang):
    lang = resolve_content_lang(lang)
    if lang == 'en':
        return f"""
Generate {question_count} multiple-choice questions about "{topic}".

RULES:
- Write ALL questions and ALL answer options in English only (never Turkish)
- Even if the topic name "{topic}" is in another language, the quiz must still be entirely in English
- Every question must be strictly about "{topic}"
- Each question must have exactly 4 options (A, B, C, D) with only one correct answer
- Medium difficulty; clear wording; exactly one correct answer
- correct_option must be A, B, C, or D

RESPONSE FORMAT - JSON ONLY:
{{
    "questions": [
        {{
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_option": "A"
        }}
    ]
}}

IMPORTANT:
- Return JSON only, no markdown code fences
- No extra commentary
- Valid, complete JSON
- Exactly 4 options per question
"""
    return f"""
{topic} konusu için {question_count} adet çoktan seçmeli soru üret.

KURALLAR:
- Sorular Türkçe olmalı ve tamamen "{topic}" konusu ile ilgili olmalı
- Her soru için 4 şık olmalı (A, B, C, D) ve sadece bir doğru cevap olmalı
- Soruların zorluk seviyesi orta düzeyde olsun
- Her soru net, anlaşılır ve tek doğru cevabı olsun
- correct_option değeri A, B, C veya D olmalı

YANIT FORMATI - SADECE JSON:
{{
    "questions": [
        {{
            "question": "Soru metni buraya",
            "options": ["A şıkkı", "B şıkkı", "C şıkkı", "D şıkkı"],
            "correct_option": "A"
        }}
    ]
}}

ÖNEMLİ:
- Sadece JSON döndür, markdown kod bloğu kullanma
- Başka açıklama ekleme
- Tüm tırnak işaretlerini doğru kapat
- JSON formatının tam ve geçerli olduğundan emin ol
- Her soru için tam 4 seçenek olmalı
"""

def _parse_gemini_questions_json(response, topic, question_count):
    import json

    response_text = response.text.strip()

    if response_text.startswith('```json'):
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1).strip()
        else:
            response_text = response_text[7:].strip()
    elif response_text.startswith('```'):
        json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1).strip()
        else:
            response_text = response_text[3:].strip()

    response_text = clean_and_fix_json(response_text)
    result = json.loads(response_text)
    questions = result.get("questions", [])

    if len(questions) > question_count:
        questions = questions[:question_count]
    elif len(questions) < question_count:
        print(f"Uyarı: İstenen {question_count} soru yerine {len(questions)} soru üretildi")

    return questions

def translate_questions_with_gemini(questions, target_lang='en'):
    """Fallback: translate question set when output language does not match UI."""
    target_lang = resolve_content_lang(target_lang)
    if target_lang != 'en' or not questions:
        return questions

    try:
        if GEMINI_API_KEY == "your_gemini_api_key_here":
            return questions

        model = genai.GenerativeModel('gemini-2.5-flash')
        import json
        payload = json.dumps({"questions": questions}, ensure_ascii=False)
        prompt = f"""
Translate the following quiz questions and all answer options into English.
Keep the same JSON structure, number of questions, number of options, and correct_option letters (A/B/C/D).
Do not change which option is correct — only translate the text.

INPUT JSON:
{payload}

Return JSON only in this format:
{{
    "questions": [
        {{
            "question": "...",
            "options": ["...", "...", "...", "..."],
            "correct_option": "A"
        }}
    ]
}}
"""
        response = model.generate_content(prompt)
        translated = _parse_gemini_questions_json(response, "translation", len(questions))
        return translated if translated else questions
    except Exception as e:
        print(f"Soru çeviri hatası: {e}")
        return questions

def _fallback_error_question(topic, lang, message_key='generic'):
    lang = resolve_content_lang(lang)
    if lang == 'en':
        messages = {
            'api_key': f"Gemini API key is not configured. Could not generate questions for {topic}.",
            'parse': f"Could not parse questions for {topic}. Please try again.",
            'error': f"An error occurred while generating questions for {topic}.",
        }
        options = ["API key required", "Please configure", "Environment variable", "GEMINI_API_KEY"]
    else:
        messages = {
            'api_key': f"Gemini API anahtarı ayarlanmamış. {topic} için sorular üretilemedi.",
            'parse': f"{topic} konusunda JSON parse hatası oluştu. Lütfen tekrar deneyin.",
            'error': f"{topic} için soru üretilirken hata oluştu.",
        }
        options = ["API anahtarı gerekli", "Lütfen ayarlayın", "Environment variable", "GEMINI_API_KEY"]
    return [{
        "question": messages.get(message_key, messages['error']),
        "options": options if message_key == 'api_key' else ["API yanıtı hatalı", "JSON formatı bozuk", "Tekrar deneyin", "Sistem hatası"],
        "correct_option": "A" if message_key == 'api_key' else "C"
    }]

# Turnuva API'leri
def generate_questions_with_gemini(topic, question_count=15, lang='en'):
    """Gemini API ile soru üret"""
    lang = resolve_content_lang(lang)
    print(f'generate_questions_with_gemini topic={topic!r} count={question_count} lang={lang}')
    try:
        if GEMINI_API_KEY == "your_gemini_api_key_here":
            print("UYARI: Gemini API anahtarı ayarlanmamış. Lütfen GEMINI_API_KEY environment variable'ını ayarlayın.")
            return _fallback_error_question(topic, lang, 'api_key')

        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = _build_question_generation_prompt(topic, question_count, lang)
        
        response = model.generate_content(prompt)
        
        import json
        
        try:
            questions = _parse_gemini_questions_json(response, topic, question_count)
            questions = ensure_questions_language(questions, lang)
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON parse hatası: {e}")
            print(f"Orijinal AI yanıtı: {response.text[:500]}...")
            
            try:
                questions = extract_questions_from_text(response.text, topic, question_count)
                if questions:
                    questions = ensure_questions_language(questions, lang)
                    print(f"Manuel çıkarma başarılı: {len(questions)} soru bulundu")
                    return questions
            except Exception as extract_error:
                print(f"Manuel çıkarma hatası: {extract_error}")
            
            return _fallback_error_question(topic, lang, 'parse')
            
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        q = _fallback_error_question(topic, lang, 'error')
        q[0]['question'] = q[0]['question'] + (f": {str(e)}" if lang == 'en' else f": {str(e)}")
        return q



@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    """AI ile soru üret"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        # Veri doğrulama
        if not data.get('content'):
            return jsonify({'error': 'Turnuva içeriği gereklidir'}), 400
        
        # Soruları üret
        lang = resolve_content_lang(data.get('lang') or request.headers.get('X-Content-Lang'))
        questions = generate_questions_with_gemini(
            data['content'],
            data.get('question_count', 15),
            lang=lang
        )
        
        return jsonify({
            'success': True,
            'questions': questions
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/generate-test-questions', methods=['POST'])
def generate_test_questions():
    """Test için soru üret"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        # Veri doğrulama
        if 'topic' not in data:
            return jsonify({'error': 'Konu başlığı gereklidir'}), 400
        
        topic = data['topic']
        difficulty = data.get('difficulty', 'medium')
        count = data.get('count', 5)
        lang = resolve_content_lang(data.get('lang') or request.headers.get('X-Content-Lang'))
        print(f'generate_test_questions lang={lang} topic={topic!r}')
        
        # Gemini ile test soruları üret
        questions = generate_questions_with_gemini(topic, count, lang=lang)
        
        # Soruları test formatına dönüştür
        test_questions = []
        for q in questions:
            test_questions.append({
                'question': q['question'],
                'options': q['options'],
                'correct_answer': q['correct_option']
            })
        
        return jsonify({
            'success': True,
            'questions': test_questions,
            'topic': topic,
            'difficulty': difficulty,
            'count': len(test_questions),
            'lang': lang,
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Test soruları üretme hatası: {str(e)}'}), 500



@app.route('/api/save-tournament', methods=['POST'])
def save_tournament():
    """Turnuvayı kaydet"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        # Veri doğrulama
        required_fields = ['title', 'content', 'start_time', 'end_time', 'questions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        # Veritabanına kaydet
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuvayı kaydet
        cursor.execute('''
            INSERT INTO tournaments (title, content, question_count, duration_minutes, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (data['title'], data['content'], data['question_count'], data['duration_minutes'], data['start_time'], data['end_time']))
        
        tournament_id = cursor.lastrowid
        
        # Soruları kaydet
        for question in data['questions']:
            cursor.execute('''
                INSERT INTO questions (tournament_id, question, option_a, option_b, option_c, option_d, correct_option)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tournament_id,
                question['question'],
                question['options'][0],
                question['options'][1],
                question['options'][2],
                question['options'][3],
                question['correct_option']
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Turnuva başarıyla kaydedildi',
            'tournament_id': tournament_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    """Aktif turnuvaları listele"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Önce status'u NULL olan turnuvaları 'active' yap
        cursor.execute('''
            UPDATE tournaments 
            SET status = 'active' 
            WHERE status IS NULL OR status = ''
        ''')
        conn.commit()
        
        cursor.execute('''
            SELECT id, title, content, question_count, duration_minutes, start_time, end_time, status, created_at
            FROM tournaments 
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''')
        
        tournaments = cursor.fetchall()
        conn.close()
        
        tournament_list = []
        for tournament in tournaments:
            tournament_list.append({
                'id': tournament[0],
                'title': tournament[1],
                'content': tournament[2],
                'question_count': tournament[3],
                'duration_minutes': tournament[4],
                'start_time': tournament[5],
                'end_time': tournament[6],
                'status': tournament[7],
                'created_at': tournament[8]
            })
        
        return jsonify({
            'success': True,
            'tournaments': tournament_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/join-tournament', methods=['POST'])
def join_tournament():
    """Turnuvaya katıl"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        if not data.get('tournament_id'):
            return jsonify({'error': 'Turnuva ID gereklidir'}), 400
        
        # Veritabanına kaydet
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva zaman kontrolü
        cursor.execute('''
            SELECT start_time, end_time, status FROM tournaments WHERE id = ?
        ''', (data['tournament_id'],))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Zaman kontrolü (daha esnek)
        try:
            start_time = datetime.fromisoformat(tournament[0].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(tournament[1].replace('Z', '+00:00'))
            current_time = now_tr()
            
            # Turnuva bitmişse katılıma izin verme
            if current_time > end_time:
                conn.close()
                return jsonify({'error': 'Turnuva süresi dolmuş'}), 400
        except:
            # Zaman formatı sorunluysa katılıma izin ver
            pass
        
        # Daha önce katılmış mı kontrol et
        cursor.execute('''
            SELECT id FROM tournament_participants 
            WHERE user_id = ? AND tournament_id = ?
        ''', (payload['user_id'], data['tournament_id']))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bu turnuvaya zaten katıldınız'}), 400
        
        # Katılımı kaydet
        cursor.execute('''
            INSERT INTO tournament_participants (user_id, tournament_id, total_questions, correct_answers, joined_at)
            VALUES (?, ?, 0, 0, ?)
        ''', (payload['user_id'], data['tournament_id'], now_tr_str()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Turnuvaya başarıyla katıldınız'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournament-questions/<int:tournament_id>', methods=['GET'])
def get_tournament_questions(tournament_id):
    """Turnuva sorularını getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva bilgilerini al
        cursor.execute('''
            SELECT title, content, start_time, end_time, status
            FROM tournaments WHERE id = ?
        ''', (tournament_id,))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Soruları al
        cursor.execute('''
            SELECT id, question, option_a, option_b, option_c, option_d
            FROM questions WHERE tournament_id = ?
            ORDER BY id
        ''', (tournament_id,))
        
        questions = cursor.fetchall()
        conn.close()
        
        question_list = []
        for question in questions:
            question_list.append({
                'id': question[0],
                'question': question[1],
                'options': [question[2], question[3], question[4], question[5]]
            })
        
        return jsonify({
            'success': True,
            'tournament': {
                'id': tournament_id,
                'title': tournament[0],
                'content': tournament[1],
                'start_time': tournament[2],
                'end_time': tournament[3],
                'status': tournament[4]
            },
            'questions': question_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/answer-question', methods=['POST'])
def answer_question():
    """Soru cevapla"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        required_fields = ['tournament_id', 'question_id', 'selected_option']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva zaman kontrolü
        cursor.execute('''
            SELECT end_time FROM tournaments WHERE id = ?
        ''', (data['tournament_id'],))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        end_time = datetime.fromisoformat(tournament[0].replace('Z', '+00:00'))
        current_time = now_tr()
        
        # Turnuva bitmişse cevap vermeye izin verme
        if current_time > end_time:
            conn.close()
            return jsonify({'error': 'Turnuva süresi dolmuş'}), 400
        
        # Daha önce bu soruyu cevaplamış mı kontrol et
        cursor.execute('''
            SELECT id FROM user_answers 
            WHERE user_id = ? AND tournament_id = ? AND question_id = ?
        ''', (payload['user_id'], data['tournament_id'], data['question_id']))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Bu soruyu zaten cevapladınız'}), 400
        
        # Doğru cevabı kontrol et
        cursor.execute('''
            SELECT correct_option FROM questions WHERE id = ?
        ''', (data['question_id'],))
        
        question = cursor.fetchone()
        if not question:
            conn.close()
            return jsonify({'error': 'Soru bulunamadı'}), 404
        
        is_correct = data['selected_option'] == question[0]
        
        # Cevabı kaydet
        cursor.execute('''
            INSERT INTO user_answers (user_id, tournament_id, question_id, selected_option, is_correct)
            VALUES (?, ?, ?, ?, ?)
        ''', (payload['user_id'], data['tournament_id'], data['question_id'], data['selected_option'], is_correct))
        
        # Skoru güncelle
        cursor.execute('''
            UPDATE tournament_participants 
            SET total_questions = total_questions + 1,
                correct_answers = correct_answers + ?
            WHERE user_id = ? AND tournament_id = ?
        ''', (1 if is_correct else 0, payload['user_id'], data['tournament_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': question[0]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/complete-tournament', methods=['POST'])
def complete_tournament():
    """Turnuvayı tamamla ve final skoru hesapla"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        if not data.get('tournament_id'):
            return jsonify({'error': 'Turnuva ID gereklidir'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Katılım bilgilerini al
        cursor.execute('''
            SELECT total_questions, correct_answers, completed_at
            FROM tournament_participants 
            WHERE user_id = ? AND tournament_id = ?
        ''', (payload['user_id'], data['tournament_id']))
        
        participant = cursor.fetchone()
        if not participant:
            conn.close()
            return jsonify({'error': 'Bu turnuvaya katılmadınız'}), 404
        
        if participant[2]:  # completed_at varsa
            conn.close()
            return jsonify({'error': 'Bu turnuvayı zaten tamamladınız'}), 400
        
        # Final skoru hesapla
        total_questions = participant[0]
        correct_answers = participant[1]
        
        if total_questions == 0:
            conn.close()
            return jsonify({'error': 'Hiç soru cevaplanmamış'}), 400
        
        final_score = round((correct_answers / total_questions) * 100)
        
        # Turnuvayı tamamla
        cursor.execute('''
            UPDATE tournament_participants 
            SET completed_at = ?,
                total_score = ?
            WHERE user_id = ? AND tournament_id = ?
        ''', (now_tr_str(), final_score, payload['user_id'], data['tournament_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'final_score': final_score,
            'total_questions': total_questions,
            'correct_answers': correct_answers
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournament-results/<int:tournament_id>', methods=['GET'])
def get_tournament_results(tournament_id):
    """Turnuva sonuçlarını getir"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva bilgileri
        cursor.execute('''
            SELECT title, start_time, end_time, status
            FROM tournaments WHERE id = ?
        ''', (tournament_id,))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Katılımcı sonuçları
        cursor.execute('''
            SELECT u.first_name, u.last_name, tp.total_score, tp.total_questions, 
                   tp.correct_answers, tp.completed_at
            FROM tournament_participants tp
            JOIN users u ON tp.user_id = u.id
            WHERE tp.tournament_id = ? AND tp.completed_at IS NOT NULL
            ORDER BY tp.total_score DESC, tp.completed_at ASC
        ''', (tournament_id,))
        
        participants = cursor.fetchall()
        conn.close()
        
        participants_list = []
        for i, participant in enumerate(participants):
            # Tamamlama süresini hesapla
            completion_time = "N/A"
            if participant[5]:  # completed_at varsa
                try:
                    completed_time = datetime.fromisoformat(participant[5].replace('Z', '+00:00'))
                    # Basit süre hesaplama (gerçek uygulamada daha detaylı olabilir)
                    completion_time = "Tamamlandı"
                except:
                    completion_time = "N/A"
            
            participants_list.append({
                'rank': i + 1,
                'username': f"{participant[0]} {participant[1]}",
                'total_score': participant[2] or 0,
                'total_questions': participant[3] or 0,
                'correct_answers': participant[4] or 0,
                'completion_time': completion_time
            })
        
        return jsonify({
            'success': True,
            'tournament': {
                'id': tournament_id,
                'title': tournament[0],
                'start_time': tournament[1],
                'end_time': tournament[2],
                'status': tournament[3]
            },
            'participants': participants_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/user-tournament-status/<int:tournament_id>', methods=['GET'])
def get_user_tournament_status(tournament_id):
    """Kullanıcının turnuva durumunu getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva bilgileri
        cursor.execute('''
            SELECT title, start_time, end_time, status
            FROM tournaments WHERE id = ?
        ''', (tournament_id,))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Kullanıcı katılım durumu
        cursor.execute('''
            SELECT total_score, total_questions, correct_answers, completed_at, joined_at
            FROM tournament_participants 
            WHERE user_id = ? AND tournament_id = ?
        ''', (payload['user_id'], tournament_id))
        
        participant = cursor.fetchone()
        conn.close()
        
        current_time = now_tr()
        
        # Zaman kontrolü (daha esnek)
        try:
            start_time = datetime.fromisoformat(tournament[1].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(tournament[2].replace('Z', '+00:00'))
            
            status = {
                'tournament_id': tournament_id,
                'title': tournament[0],
                'start_time': tournament[1],
                'end_time': tournament[2],
                'status': tournament[3],
                'current_time': current_time.isoformat(),
                'has_joined': participant is not None,
                'can_join': start_time <= current_time <= end_time,  # Hem başlangıç hem bitiş zamanını kontrol et
                'can_participate': participant is not None and start_time <= current_time <= end_time,
                'is_completed': participant and participant[3] is not None
            }
        except:
            # Zaman formatı sorunluysa varsayılan değerler
            status = {
                'tournament_id': tournament_id,
                'title': tournament[0],
                'start_time': tournament[1],
                'end_time': tournament[2],
                'status': tournament[3],
                'current_time': current_time.isoformat(),
                'has_joined': participant is not None,
                'can_join': True,  # Varsayılan olarak katılıma izin ver
                'can_participate': participant is not None,
                'is_completed': participant and participant[3] is not None
            }
        
        if participant:
            status.update({
                'total_score': participant[0],
                'total_questions': participant[1],
                'correct_answers': participant[2],
                'completed_at': participant[3],
                'joined_at': participant[4]
            })
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    """Turnuva detaylarını getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva bilgileri
        cursor.execute('''
            SELECT id, title, content, question_count, duration_minutes, start_time, end_time, status
            FROM tournaments WHERE id = ?
        ''', (tournament_id,))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Turnuva soruları
        cursor.execute('''
            SELECT id, question, option_a, option_b, option_c, option_d, correct_option
            FROM questions WHERE tournament_id = ?
            ORDER BY id
        ''', (tournament_id,))
        
        questions = cursor.fetchall()
        conn.close()
        
        questions_list = []
        for question in questions:
            questions_list.append({
                'id': question[0],
                'question': question[1],
                'options': [question[2], question[3], question[4], question[5]],
                'correct_option': question[6]
            })
        
        return jsonify({
            'success': True,
            'tournament': {
                'id': tournament[0],
                'title': tournament[1],
                'content': tournament[2],
                'question_count': tournament[3],
                'duration_minutes': tournament[4],
                'start_time': tournament[5],
                'end_time': tournament[6],
                'status': tournament[7],
                'questions': questions_list
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/update-tournament/<int:tournament_id>', methods=['PUT'])
def update_tournament(tournament_id):
    """Turnuvayı güncelle"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        data = request.get_json()
        
        required_fields = ['title', 'content', 'start_time', 'end_time', 'questions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} alanı gereklidir'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuvayı güncelle
        cursor.execute('''
            UPDATE tournaments 
            SET title = ?, content = ?, start_time = ?, end_time = ?
            WHERE id = ?
        ''', (data['title'], data['content'], data['start_time'], data['end_time'], tournament_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # Eski soruları sil
        cursor.execute('DELETE FROM questions WHERE tournament_id = ?', (tournament_id,))
        
        # Yeni soruları ekle
        for question in data['questions']:
            cursor.execute('''
                INSERT INTO questions (tournament_id, question, option_a, option_b, option_c, option_d, correct_option)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tournament_id, question['question'], question['options'][0], question['options'][1], 
                  question['options'][2], question['options'][3], question['correct_option']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Turnuva başarıyla güncellendi'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournaments/<int:tournament_id>', methods=['DELETE'])
def delete_tournament(tournament_id):
    """Turnuvayı sil"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuvayı sil
        cursor.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        # İlgili soruları da sil
        cursor.execute('DELETE FROM questions WHERE tournament_id = ?', (tournament_id,))
        
        # İlgili katılımları da sil
        cursor.execute('DELETE FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
        
        # İlgili cevapları da sil
        cursor.execute('DELETE FROM user_answers WHERE tournament_id = ?', (tournament_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Turnuva başarıyla silindi'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournament-participant-count/<int:tournament_id>', methods=['GET'])
def get_tournament_participant_count(tournament_id):
    """Turnuvayı tamamlayan kişi sayısını döndür"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuvayı tamamlayan kişi sayısını al (completed_at NULL değil)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM tournament_participants 
            WHERE tournament_id = ? AND completed_at IS NOT NULL
        ''', (tournament_id,))
        
        participant_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'participant_count': participant_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/leaderboard/<int:tournament_id>', methods=['GET'])
def get_leaderboard(tournament_id):
    """Turnuva sıralamasını doğru cevap sayısına göre döndür"""
    try:
        # Token kontrolü (opsiyonel - genel sıralama için)
        auth_header = request.headers.get('Authorization')
        current_user_id = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['user_id']
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass  # Token geçersizse sadece genel sıralama göster
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuvayı tamamlayan kullanıcıları doğru cevap sayısına göre sırala
        cursor.execute('''
            SELECT 
                tp.user_id,
                u.first_name,
                u.last_name,
                tp.correct_answers,
                tp.total_questions,
                tp.total_score,
                tp.completed_at
            FROM tournament_participants tp
            JOIN users u ON tp.user_id = u.id
            WHERE tp.tournament_id = ? AND tp.completed_at IS NOT NULL
            ORDER BY tp.correct_answers DESC, tp.completed_at ASC
            LIMIT 10
        ''', (tournament_id,))
        
        participants = cursor.fetchall()
        
        leaderboard = []
        for i, participant in enumerate(participants):
            user_id, first_name, last_name, correct_answers, total_questions, total_score, completed_at = participant
            
            # Kullanıcı adını oluştur
            username = f"{first_name} {last_name}"
            
            # Sıralama pozisyonu
            rank = i + 1
            
            # Mevcut kullanıcı mı kontrol et
            is_current_user = current_user_id == user_id
            
            leaderboard.append({
                'rank': rank,
                'user_id': user_id,
                'username': username,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'total_score': total_score,
                'completion_time': completed_at,
                'is_current_user': is_current_user
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'tournament_id': tournament_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/global-leaderboard', methods=['GET'])
def get_global_leaderboard():
    """Genel sıralama - tüm turnuvalardaki toplam performansa göre"""
    try:
        # Token kontrolü (opsiyonel)
        auth_header = request.headers.get('Authorization')
        current_user_id = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['user_id']
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Tüm turnuvalardaki toplam performansı hesapla
        cursor.execute('''
            SELECT 
                u.id,
                u.first_name,
                u.last_name,
                SUM(tp.correct_answers) as total_correct,
                SUM(tp.total_questions) as total_questions,
                AVG(tp.total_score) as avg_score,
                COUNT(tp.id) as tournaments_completed
            FROM users u
            JOIN tournament_participants tp ON u.id = tp.user_id
            WHERE tp.completed_at IS NOT NULL
            GROUP BY u.id, u.first_name, u.last_name
            HAVING total_correct > 0
            ORDER BY total_correct DESC, avg_score DESC
            LIMIT 10
        ''')
        
        participants = cursor.fetchall()
        
        leaderboard = []
        for i, participant in enumerate(participants):
            user_id, first_name, last_name, total_correct, total_questions, avg_score, tournaments_completed = participant
            
            username = f"{first_name} {last_name}"
            rank = i + 1
            is_current_user = current_user_id == user_id
            
            leaderboard.append({
                'rank': rank,
                'user_id': user_id,
                'username': username,
                'total_correct_answers': total_correct,
                'total_questions': total_questions,
                'average_score': round(avg_score, 1),
                'tournaments_completed': tournaments_completed,
                'is_current_user': is_current_user
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/tournament-stats/<int:tournament_id>', methods=['GET'])
def get_tournament_stats(tournament_id):
    """Turnuva istatistiklerini döndür"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Turnuva bilgilerini al
        cursor.execute('''
            SELECT start_time, end_time, status
            FROM tournaments
            WHERE id = ?
        ''', (tournament_id,))
        
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Turnuva bulunamadı'}), 404
        
        start_time, end_time, status = tournament
        
        # Toplam katılımcı sayısı
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id)
            FROM tournament_participants
            WHERE tournament_id = ?
        ''', (tournament_id,))
        
        total_participants = cursor.fetchone()[0]
        
        # Tamamlanan turnuvaların istatistikleri
        cursor.execute('''
            SELECT 
                COUNT(*) as completed_count,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                AVG(correct_answers) as avg_correct,
                MAX(correct_answers) as max_correct
            FROM tournament_participants
            WHERE tournament_id = ? AND completed_at IS NOT NULL
        ''', (tournament_id,))
        
        stats = cursor.fetchone()
        completed_count, avg_score, max_score, avg_correct, max_correct = stats
        
        # Ortalama skor hesapla
        average_score = round(avg_score, 1) if avg_score else 0
        highest_score = round(max_score, 1) if max_score else 0
        
        # Kalan süre hesapla
        now = now_tr()
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        if end_datetime > now:
            time_left = end_datetime - now
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            seconds = int(time_left.total_seconds() % 60)
            remaining_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            remaining_time = "00:00:00"
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_participants': total_participants,
                'completed_participants': completed_count,
                'average_score': average_score,
                'highest_score': highest_score,
                'average_correct_answers': round(avg_correct, 1) if avg_correct else 0,
                'max_correct_answers': max_correct if max_correct else 0,
                'remaining_time': remaining_time,
                'tournament_status': status
            },
            'tournament_id': tournament_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/weekly-tournament-calendar', methods=['GET'])
def get_weekly_tournament_calendar():
    """Haftalık turnuva takvimini döndür"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Bu haftanın başlangıç ve bitiş tarihlerini hesapla
        now = now_tr()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)
        
        # Haftalık günler
        days_of_week = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
        
        weekly_calendar = []
        
        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            day_name = days_of_week[i]
            
            # Bu gün için turnuva var mı kontrol et
            cursor.execute('''
                SELECT id, title, status
                FROM tournaments
                WHERE DATE(start_time) = DATE(?)
                ORDER BY start_time ASC
                LIMIT 1
            ''', (current_date.strftime('%Y-%m-%d'),))
            
            tournament = cursor.fetchone()
            
            if tournament:
                tournament_id, tournament_title, tournament_status = tournament
                
                # Bu turnuvanın kazananını bul
                cursor.execute('''
                    SELECT u.first_name, u.last_name, tp.correct_answers, tp.total_score
                    FROM tournament_participants tp
                    JOIN users u ON tp.user_id = u.id
                    WHERE tp.tournament_id = ? AND tp.completed_at IS NOT NULL
                    ORDER BY tp.correct_answers DESC, tp.completed_at ASC
                    LIMIT 1
                ''', (tournament_id,))
                
                winner = cursor.fetchone()
                
                if winner:
                    winner_name, winner_lastname, correct_answers, total_score = winner
                    winner_display = f"{winner_name} {winner_lastname}"
                    winner_score = ""
                else:
                    winner_display = "Henüz kazanan yok"
                    winner_score = ""
                
                # Gün durumunu belirle
                if current_date.date() == now.date():
                    day_status = "today"
                    day_icon = "🔥"
                elif current_date.date() < now.date():
                    day_status = "completed"
                    day_icon = "✓"
                else:
                    day_status = "upcoming"
                    day_icon = "🔒"
                
                weekly_calendar.append({
                    'day_name': day_name,
                    'day_status': day_status,
                    'day_icon': day_icon,
                    'tournament_title': tournament_title,
                    'tournament_status': tournament_status,
                    'winner_name': winner_display,
                    'winner_score': winner_score,
                    'date': current_date.strftime('%Y-%m-%d')
                })
            else:
                # Bu gün için turnuva yok
                if current_date.date() == now.date():
                    day_status = "today"
                    day_icon = "📅"
                elif current_date.date() < now.date():
                    day_status = "completed"
                    day_icon = "✓"
                else:
                    day_status = "upcoming"
                    day_icon = "🔒"
                
                weekly_calendar.append({
                    'day_name': day_name,
                    'day_status': day_status,
                    'day_icon': day_icon,
                    'tournament_title': "Turnuva yok",
                    'tournament_status': "none",
                    'winner_name': "",
                    'winner_score': "",
                    'date': current_date.strftime('%Y-%m-%d')
                })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'weekly_calendar': weekly_calendar,
            'current_week': {
                'start_date': start_of_week.strftime('%Y-%m-%d'),
                'end_date': end_of_week.strftime('%Y-%m-%d')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/user-tournament-wins', methods=['GET'])
def get_user_tournament_wins():
    """Kullanıcının kazandığı turnuvaları getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Kullanıcının 1. olduğu turnuvaları bul - daha basit sorgu
        cursor.execute('''
            SELECT 
                t.id as tournament_id,
                t.title as tournament_title,
                tp.total_score,
                tp.correct_answers,
                tp.total_questions,
                tp.completed_at,
                (
                    SELECT COUNT(*) 
                    FROM tournament_participants tp2 
                    WHERE tp2.tournament_id = t.id 
                        AND tp2.completed_at IS NOT NULL
                ) as total_participants
            FROM tournament_participants tp
            JOIN tournaments t ON tp.tournament_id = t.id
            WHERE tp.user_id = ? 
                AND tp.completed_at IS NOT NULL
                AND tp.correct_answers = (
                    SELECT MAX(correct_answers) 
                    FROM tournament_participants tp2 
                    WHERE tp2.tournament_id = tp.tournament_id 
                        AND tp2.completed_at IS NOT NULL
                )
            ORDER BY tp.completed_at DESC
            LIMIT 4
        ''', (payload['user_id'],))
        
        wins = cursor.fetchall()
        conn.close()
        
        print(f"DEBUG: Kullanıcı {payload['user_id']} için {len(wins)} turnuva kazanımı bulundu")
        
        wins_list = []
        for win in wins:
            tournament_id, tournament_title, total_score, correct_answers, total_questions, completed_at, total_participants = win
            
            print(f"DEBUG: Turnuva {tournament_id} - {tournament_title} - {correct_answers} doğru - {total_participants} katılımcı")
            
            # Tamamlama tarihini formatla
            completion_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            formatted_date = completion_date.strftime('%d %B %Y')
            
            wins_list.append({
                'tournament_id': tournament_id,
                'tournament_title': tournament_title,
                'total_score': total_score,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'completion_date': formatted_date,
                'total_participants': total_participants
            })
        
        return jsonify({
            'success': True,
            'tournament_wins': wins_list,
            'total_wins': len(wins_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/debug-tournament-data', methods=['GET'])
def debug_tournament_data():
    """Debug için turnuva verilerini kontrol et"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Kullanıcının tüm turnuva katılımlarını getir
        cursor.execute('''
            SELECT 
                t.id as tournament_id,
                t.title as tournament_title,
                tp.total_score,
                tp.correct_answers,
                tp.total_questions,
                tp.completed_at,
                tp.joined_at
            FROM tournament_participants tp
            JOIN tournaments t ON tp.tournament_id = t.id
            WHERE tp.user_id = ?
            ORDER BY tp.completed_at DESC
        ''', (payload['user_id'],))
        
        participations = cursor.fetchall()
        
        # Turnuva bazında en yüksek skorları getir
        cursor.execute('''
            SELECT 
                t.id as tournament_id,
                t.title as tournament_title,
                MAX(tp.correct_answers) as max_correct,
                COUNT(tp.id) as total_participants
            FROM tournaments t
            LEFT JOIN tournament_participants tp ON t.id = tp.tournament_id
            WHERE tp.completed_at IS NOT NULL
            GROUP BY t.id, t.title
            ORDER BY t.id DESC
        ''')
        
        tournament_stats = cursor.fetchall()
        
        conn.close()
        
        participations_list = []
        for p in participations:
            participations_list.append({
                'tournament_id': p[0],
                'tournament_title': p[1],
                'total_score': p[2],
                'correct_answers': p[3],
                'total_questions': p[4],
                'completed_at': p[5],
                'joined_at': p[6]
            })
        
        stats_list = []
        for s in tournament_stats:
            stats_list.append({
                'tournament_id': s[0],
                'tournament_title': s[1],
                'max_correct': s[2],
                'total_participants': s[3]
            })
        
        return jsonify({
            'user_participations': participations_list,
            'tournament_stats': stats_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Veritabanındaki turnuva verilerini test et"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Tüm turnuvaları listele
        cursor.execute('SELECT id, title, status FROM tournaments ORDER BY id DESC LIMIT 5')
        tournaments = cursor.fetchall()
        
        # Tüm katılımları listele
        cursor.execute('''
            SELECT tp.id, tp.user_id, tp.tournament_id, tp.correct_answers, tp.total_questions, tp.completed_at, t.title
            FROM tournament_participants tp
            JOIN tournaments t ON tp.tournament_id = t.id
            ORDER BY tp.id DESC LIMIT 10
        ''')
        participations = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'tournaments': [{'id': t[0], 'title': t[1], 'status': t[2]} for t in tournaments],
            'participations': [{
                'id': p[0], 'user_id': p[1], 'tournament_id': p[2], 
                'correct_answers': p[3], 'total_questions': p[4], 
                'completed_at': p[5], 'tournament_title': p[6]
            } for p in participations]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'DB hatası: {str(e)}'}), 500

@app.route('/api/completed-courses', methods=['GET'])
def get_completed_courses():
    """Kullanıcının tamamladığı kursları getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        # Veritabanından tamamlanan kursları getir
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT course_title, completed_at, added_at
            FROM user_courses 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 10
        ''', (payload['user_id'],))
        
        completed_courses = []
        for row in cursor.fetchall():
            course_title, completed_at, added_at = row
            
            # Tarih formatını düzenle
            completed_date = datetime.fromisoformat(completed_at) if completed_at else None
            added_date = datetime.fromisoformat(added_at) if added_at else None
            
            # Ne kadar sürede tamamlandığını hesapla
            duration = None
            if completed_date and added_date:
                duration = completed_date - added_date
                duration_days = duration.days
                duration_hours = duration.seconds // 3600
                
                if duration_days > 0:
                    duration_text = f"{duration_days} gün"
                elif duration_hours > 0:
                    duration_text = f"{duration_hours} saat"
                else:
                    duration_text = "1 saatten az"
            else:
                duration_text = "Bilinmiyor"
            
            # Ne kadar zaman önce tamamlandığını hesapla
            if completed_date:
                now = now_tr()
                time_diff = now - completed_date
                
                if time_diff.days > 0:
                    time_ago = f"{time_diff.days} gün önce"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_ago = f"{hours} saat önce"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    time_ago = f"{minutes} dakika önce"
                else:
                    time_ago = "Az önce"
            else:
                time_ago = "Bilinmiyor"
            
            completed_courses.append({
                'title': course_title,
                'completed_at': completed_at,
                'added_at': added_at,
                'time_ago': time_ago,
                'duration': duration_text
            })
        
        conn.close()
        
        return jsonify({
            'completed_courses': completed_courses
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

@app.route('/api/active-course', methods=['GET'])
def get_active_course():
    """Kullanıcının aktif olarak öğrendiği kursu getir"""
    try:
        # Token kontrolü
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token gereklidir'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token süresi dolmuş'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Geçersiz token'}), 401
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Kullanıcının en son eklediği aktif kursu bul
        cursor.execute('''
            SELECT id, course_title, course_link, roadmap_sections, added_at
            FROM user_courses 
            WHERE user_id = ? AND status = 'active'
            ORDER BY added_at DESC 
            LIMIT 1
        ''', (payload['user_id'],))
        
        course = cursor.fetchone()
        conn.close()
        
        if not course:
            return jsonify({
                'active_course': None,
                'message': 'Henüz aktif bir kursunuz yok'
            }), 200
        
        course_id, course_title, course_link, roadmap_sections, added_at = course
        
        # Roadmap bölümlerini parse et
        roadmap_data = []
        if roadmap_sections:
            try:
                roadmap_data = json.loads(roadmap_sections)
                print(f"DEBUG: Roadmap data parsed: {roadmap_data}")
                print(f"DEBUG: Roadmap data type: {type(roadmap_data)}")
                print(f"DEBUG: Roadmap data length: {len(roadmap_data)}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                print(f"DEBUG: Raw roadmap_sections: {roadmap_sections}")
                roadmap_data = []
        
        # Tamamlanan adım sayısını hesapla
        completed_steps = 0
        total_steps = len(roadmap_data)
        
        if roadmap_data:
            print(f"DEBUG: Processing {total_steps} roadmap steps")
            for i, section in enumerate(roadmap_data):
                print(f"DEBUG: Step {i}: {section}")
                # Hem 'completed' hem de 'isCompleted' hem de 'status' kontrol et
                is_completed = (section.get('completed', False) or 
                              section.get('isCompleted', False) or 
                              section.get('status') == 'completed')
                print(f"DEBUG: Step {i} completed: {is_completed} (status: {section.get('status')})")
                if is_completed:
                    completed_steps += 1
                    print(f"DEBUG: Completed section: {section.get('title', 'Unknown')}")
        
        print(f"DEBUG: Total steps: {total_steps}, Completed: {completed_steps}")
        
        # İlerleme yüzdesini hesapla
        progress_percentage = 0
        if total_steps > 0:
            progress_percentage = round((completed_steps / total_steps) * 100)
        
        print(f"DEBUG: Progress percentage: {progress_percentage}%")
        
        return jsonify({
            'active_course': {
                'id': course_id,
                'title': course_title,
                'link': course_link,
                'progress_percentage': progress_percentage,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'added_at': added_at
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 