import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import base64
from models import Comment, db, User, Complex, PropertyType, PaymentType, DiscountObject
from services import DataSyncService
import utils

# Create blueprints
dashboard_bp = Blueprint('dashboard', __name__)
admin_bp = Blueprint('admin', __name__)
api_bp = Blueprint('api', __name__)
# filters_bp = Blueprint('filters', __name__)

# Add a helper function at the top of the file to handle prefix in URLs

# Check if app is behind proxy
behind_proxy = os.getenv('BEHIND_PROXY', 'false').lower() == 'true'
prefix = '/discount-system' if behind_proxy else ''

def get_prefix_url(path):
    """Add the correct prefix to a URL path depending on whether app is behind proxy"""
    if not path.startswith('/'):
        path = '/' + path
    return prefix + path

def decode_header_full_name(request):
    """
    Декодирует base64-закодированное полное имя из заголовков запроса
    
    Args:
        request: Объект запроса Flask с заголовками
        
    Returns:
        str: Декодированное полное имя или оригинальное значение, если не закодировано
    """
    # Получаем закодированное имя и флаг кодировки
    encoded_full_name = request.headers.get('X-User-Full-Name', '')
    encoding = request.headers.get('X-User-Full-Name-Encoding', '')
    
    print(f"Received full name header: {encoded_full_name}, encoding: {encoding}")
    
    if encoding == 'base64' and encoded_full_name:
        try:
            # Декодируем base64
            decoded_bytes = base64.b64decode(encoded_full_name)
            decoded_name = decoded_bytes.decode('utf-8')
            print(f"Decoded name: '{decoded_name}'")
            return decoded_name
        except Exception as e:
            print(f"Error decoding full name: {e}")
            return encoded_full_name  # Возвращаем как есть, если декодирование не удалось
    else:
        return encoded_full_name  # Не закодировано или нет указания кодировки

def get_current_user():
    """Get current user information from request headers"""
    # Получение имени пользователя из заголовка аутентификации
    username = request.headers.get('X-User-Name')
    # Поиск пользователя в базе данных
    user = User.query.filter_by(login=username).first()
    
    is_admin = request.headers.get('X-User-Admin', 'false').lower() == 'true'
    full_name = decode_header_full_name(request)

    role_str = request.headers.get('X-User-Roles')
    roles = str.split(role_str, ',')
    role=''

    if 'discount-user' in roles or 'user' in roles:
        role = 'user'
    if 'discount-rop' in roles or 'rop' in roles:
        role = 'rop' 
    if 'admin' in roles or 'discount-admin' in roles:
        role = 'admin'
    if user:
        if user.role != 'admin' and is_admin:
            user.role = 'admin'
            db.session.commit()
    print(f"User found: {user}, is_admin: {is_admin}")
    # Если пользователь не найден, но у него есть доступ через шлюз (т.е. заголовок X-User-Name присутствует),
    # создаем нового пользователя в базе данных
    if not user and username:
        # Получаем дополнительную информацию из заголовков и декодируем Base64 если нужно
        full_name = decode_header_full_name(request)
        
        # Создаем нового пользователя с декодированным полным именем
        user = User(
            login=username,
            full_name=full_name,
            role=role
        )
        db.session.add(user)
        
    if user and ( user.full_name!=full_name):
        user.full_name = full_name
    if user and (user.role != role):
        user.role = role
    try:
        db.session.commit()  # This should set the user.id
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {str(e)}")
    return user

@admin_bp.app_template_filter('format_comment')
def format_comment(text):
    # Define patterns to recognize section headers and entries
    import re
    
    # Add line breaks before section headers
    text = re.sub(r'(Изменение максимальных скидок)', r'\n\1', text)
    
    # Add line breaks before project entries
    text = re.sub(r'([A-Za-zА-Яа-я\'\d-]+\s[A-Za-zА-Яа-я\'\d-]+(?:\s\(\d\))?\s*-)', r'\n\1', text)
    
    # Handle special cases for project names with numbers
    text = re.sub(r'\n\n', r'\n', text)
    
    # Remove leading newline if present
    if text.startswith('\n'):
        text = text[1:]
        
    return text

# Dashboard routes
@dashboard_bp.route('/')
def index():
    current_user = get_current_user()
    complexes = Complex.query.all()
    property_types = PropertyType.query.all()
    payment_types = PaymentType.query.all()
    comment=Comment.query.order_by(Comment.created_at.desc()).first()
    return render_template('dashboard/index.html', 
                         complexes=complexes, 
                         property_types=property_types,
                         payment_types=payment_types,
                         current_user=current_user,
                         comment=comment)

# Admin routes for data management
@admin_bp.route('/upload-excel', methods=['GET', 'POST'])
def upload_excel():
    current_user = get_current_user()
    if request.method == 'POST' and current_user.role == 'admin':
        if 'excel_file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['excel_file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        try:
            sync_service = DataSyncService()
            sync_service.sync_from_upload(file)
            flash('Data updated successfully!', 'success')
            return redirect(get_prefix_url('/'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('admin/upload.html', columns = os.getenv('EXCEL_COLUMNS').split(','), sheet = os.getenv('EXCEL_SHEET_NAME'), current_user=current_user)


@admin_bp.route('/upload-comment', methods=['POST'])
def upload_comment():
    current_user = get_current_user()
    if request.method == 'POST' and current_user.role == 'admin':
        comment_text = request.form.get('comment_text', '').strip()
        if not comment_text:
            flash('Comment cannot be empty', 'error')
            return redirect(request.referrer or get_prefix_url('/'))
        
        try:
            new_comment = Comment(text=comment_text)
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding comment: {str(e)}', 'error')
    
    return redirect(request.referrer or get_prefix_url('/'))

# API routes for getting discount data
@api_bp.route('/api/discounts')
def get_discounts():
    current_user = get_current_user()
    complex_id = request.args.get('complex_id', type=int)
    type_id = request.args.get('type_id', type=int)
    payment_type_id = request.args.get('payment_type_id', type=int)
    
    if not all([complex_id, type_id, payment_type_id]):
        return jsonify({'error': 'Missing parameters'}), 400
        
    discount = DiscountObject.query.filter_by(
        complex_id=complex_id,
        type_id=type_id,
        payment_type_id=payment_type_id
    ).first()
    
    # Return 0 values if no discount found instead of 404
    return jsonify({
        'mpp_discount': round(discount.mpp_discount*100, 2) if discount else 0,
        'opt_discount': round(discount.opt_discount*100, 2) if discount else 0,
        'kd_discount': round(discount.kd_discount*100, 2) if discount else 0,
    })
    
def init_app(app):
    """Register all blueprints with the app"""
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/')
    app.register_blueprint(api_bp)
