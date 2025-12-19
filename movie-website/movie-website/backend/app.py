from flask import Flask, send_file, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import json
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

# ==================== CONFIGURATION ====================
UPLOAD_FOLDER = 'movies'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'webm'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== DATABASE FUNCTIONS ====================

def init_database():
    """Initialize database if needed"""
    try:
        from database import init_database as db_init
        db_init()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database init warning: {e}")

def get_movie_download_link(title, language, quality):
    """Get movie download link from database"""
    try:
        from database import get_movie_download_link as db_search
        return db_search(title, language, quality)
    except Exception as e:
        print(f"Database search error: {e}")
        return None

def add_movie_to_db(movie_data):
    """Add movie to database"""
    try:
        from database import add_movie
        return add_movie(movie_data)
    except Exception as e:
        print(f"Database add error: {e}")
        raise e

def get_all_movies_from_db():
    """Get all movies from database"""
    try:
        from database import get_all_movies
        return get_all_movies()
    except Exception as e:
        print(f"Database get all error: {e}")
        return []

def delete_movie_from_db(movie_id):
    """Delete movie from database"""
    try:
        from database import delete_movie
        return delete_movie(movie_id)
    except Exception as e:
        print(f"Database delete error: {e}")
        raise e

# ==================== ROUTES ====================

# Serve HTML pages
@app.route('/')
def index():
    return send_file('../static/index.html')

@app.route('/dashboard')
def dashboard():
    return send_file('../static/dashboard.html')

@app.route('/download')
def download():
    return send_file('../static/download.html')

@app.route('/admin')
def admin():
    return send_file('../static/admin.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/search')
def search_movie():
    """Search for movies in database"""
    title = request.args.get('title', '').strip()
    lang = request.args.get('lang', 'tamil')
    quality = request.args.get('quality', '720p')
    
    print(f"🔍 API Search: '{title}', lang={lang}, quality={quality}")
    
    # Check sample movies first
    sample_movies = {
        'sample': {
            'available': True,
            'movie': {
                'title': 'Sample Video',
                'year': 2023,
                'quality': quality.upper(),
                'size': '1.2GB',
                'language': lang
            },
            'download_link': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
        },
        'test': {
            'available': True,
            'movie': {
                'title': 'Test Video',
                'year': 2023,
                'quality': quality.upper(),
                'size': '1GB',
                'language': lang
            },
            'download_link': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4'
        }
    }
    
    title_lower = title.lower()
    for key, movie in sample_movies.items():
        if key in title_lower:
            return jsonify(movie)
    
    # Search in database
    result = get_movie_download_link(title, lang, quality)
    
    if result and result.get('available'):
        return jsonify(result)
    else:
        return jsonify({
            'available': False,
            'message': f'Movie "{title}" not found in database.'
        })

# ==================== ADMIN API ENDPOINTS ====================

@app.route('/api/admin/movies', methods=['GET'])
def get_all_movies():
    """Get all movies for admin panel"""
    try:
        movies = get_all_movies_from_db()
        return jsonify(movies)
    except Exception as e:
        print(f"Error getting movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/upload', methods=['POST'])
def admin_upload_movie():
    """Handle movie upload from admin panel"""
    try:
        print("📤 Received upload request")
        
        # Get form data
        title = request.form.get('title', '').strip()
        year = request.form.get('year', '2024')
        description = request.form.get('description', '')
        poster = request.form.get('poster', '')
        language = request.form.get('language', 'tamil')
        qualities_json = request.form.get('qualities', '[]')
        
        file = request.files.get('file')
        
        # Validation
        if not title:
            return jsonify({'success': False, 'error': 'Movie title is required'}), 400
        
        if not file:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed. Allowed: MP4, AVI, MKV, MOV, WEBM'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        print(f"💾 Saving file to: {filepath}")
        file.save(filepath)
        
        # Parse qualities
        try:
            qualities = json.loads(qualities_json)
            if not isinstance(qualities, list):
                qualities = [{'code': '720p', 'name': '720p HD', 'size': '1GB'}]
        except:
            qualities = [{'code': '720p', 'name': '720p HD', 'size': '1GB'}]
        
        # Prepare movie data
        movie_data = {
            'title': title,
            'year': int(year) if str(year).isdigit() else 2024,
            'description': description,
            'poster_url': poster,
            'language': language,
            'qualities': []
        }
        
        # Create download URLs
        for quality in qualities:
            movie_data['qualities'].append({
                'code': quality.get('code', '720p'),
                'name': quality.get('name', '720p HD'),
                'size': quality.get('size', '1GB'),
                'file_path': unique_filename,
                'download_url': f'/api/movies/{unique_filename}'
            })
        
        # Save to database
        try:
            movie_id = add_movie_to_db(movie_data)
            print(f"✅ Movie saved to database. ID: {movie_id}")
            
            return jsonify({
                'success': True,
                'movie_id': movie_id,
                'message': f'Movie "{title}" uploaded successfully!',
                'download_url': f'/api/movies/{unique_filename}',
                'file_info': {
                    'filename': unique_filename,
                    'size': os.path.getsize(filepath),
                    'qualities': len(qualities)
                }
            })
            
        except Exception as db_error:
            # Clean up file if database fails
            if os.path.exists(filepath):
                os.remove(filepath)
            
            print(f"❌ Database error: {db_error}")
            return jsonify({
                'success': False, 
                'error': f'Database error: {str(db_error)}'
            }), 500
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/movies/<int:movie_id>', methods=['DELETE'])
def admin_delete_movie(movie_id):
    """Delete a movie"""
    try:
        print(f"🗑️  Deleting movie ID: {movie_id}")
        
        # Get file paths before deleting from database
        file_paths = delete_movie_from_db(movie_id)
        
        # Delete physical files
        deleted_files = []
        for file_path in file_paths:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_files.append(file_path)
                print(f"🗑️  Deleted file: {filepath}")
        
        return jsonify({
            'success': True, 
            'message': 'Movie deleted successfully',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== FILE SERVING ====================

@app.route('/api/movies/<filename>')
def serve_movie(filename):
    """Serve movie files"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# ==================== UTILITY ENDPOINTS ====================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NetBox Movie API',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'GET /api/search': 'Search movies',
            'GET /api/admin/movies': 'Get all movies (admin)',
            'POST /api/admin/upload': 'Upload movie (admin)',
            'DELETE /api/admin/movies/<id>': 'Delete movie (admin)',
            'GET /api/movies/<filename>': 'Download movie file'
        }
    })

@app.route('/api/test')
def test_api():
    """Test API endpoint"""
    return jsonify({
        'message': 'API is working!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Endpoint not found', 'status': 404}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error', 'status': 500}), 500

# ==================== START SERVER ====================
if __name__ == '__main__':
    # Initialize database
    init_database()
    
    print("\n" + "=" * 60)
    print("🚀 NETBOX MOVIE WEBSITE - STARTING SERVER")
    print("=" * 60)
    print(f"📁 Project root: {os.path.abspath('..')}")
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🌐 Host: http://localhost:5000")
    print(f"📡 API: http://localhost:5000/api/search")
    print(f"👑 Admin: http://localhost:5000/admin")
    print("\n📋 Available Pages:")
    print("  • http://localhost:5000/              - Login")
    print("  • http://localhost:5000/dashboard     - Dashboard")  
    print("  • http://localhost:5000/download      - Download")
    print("  • http://localhost:5000/admin         - Admin Panel")
    print("=" * 60)
    print("\n✅ Server is running! Press Ctrl+C to stop.\n")