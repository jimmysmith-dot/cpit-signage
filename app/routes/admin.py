from urllib.parse import urlparse

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.auth import (
    authentication_configured,
    is_authenticated,
    verify_credentials,
)
from app.services.database import get_all_media, update_media_item

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _safe_next_url(value):
    if not value:
        return None

    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return None

    if not value.startswith('/admin'):
        return None

    return value


@admin_bp.before_request
def require_admin_login():
    if request.endpoint in {'admin.login'}:
        return None

    if not is_authenticated():
        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for('admin.login', next=next_url))

    return None


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if is_authenticated():
        return redirect(url_for('admin.admin'))

    configured = authentication_configured()
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not configured:
            error = 'Studio login has not been configured yet.'
        elif verify_credentials(username, password):
            session.clear()
            session.permanent = True
            session['studio_authenticated'] = True
            session['studio_username'] = username

            next_url = _safe_next_url(request.form.get('next'))
            return redirect(next_url or url_for('admin.admin'))
        else:
            error = 'Invalid username or password.'

    return render_template(
        'login.html',
        error=error,
        configured=configured,
        next_url=_safe_next_url(request.args.get('next')) or '',
    )


@admin_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
def admin():
    media_items = get_all_media()

    return render_template(
        'admin.html',
        media_items=media_items,
        saved=request.args.get('saved') == '1',
    )


@admin_bp.route('/save', methods=['POST'])
def save():
    media_items = get_all_media()

    for item in media_items:
        media_id = item['id']

        duration_value = request.form.get(
            f'duration_{media_id}',
            item['duration'],
        )

        order_value = request.form.get(
            f'order_{media_id}',
            item['sort_order'],
        )

        enabled_value = (
            request.form.get(f'enabled_{media_id}') == 'on'
        )

        try:
            update_media_item(
                media_id=media_id,
                duration=int(duration_value),
                sort_order=int(order_value),
                enabled=enabled_value,
            )
        except (TypeError, ValueError):
            continue

    return redirect(url_for('admin.admin', saved=1))
