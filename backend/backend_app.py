from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime

SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

app = Flask(__name__)
CORS(app)
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Master Blog API'
    }
)

app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
app.config['JWT_SECRET_KEY'] = 'MySecretKey'
jwt = JWTManager(app)

users = {}
POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post.", "author": "Author One", "date": "2023-01-01"},
    {"id": 2, "title": "Second post", "content": "This is the second post.", "author": "Author Two", "date": "2023-02-01"},
]


def generate_new_id():
    if POSTS:
        return max(post['id'] for post in POSTS) + 1
    else:
        return 1


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if username in users:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    users[username] = hashed_password

    return jsonify({"message": "User registered successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_password = users.get(username)
    if not hashed_password or not check_password_hash(hashed_password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@jwt_required()
@app.route('/api/posts', methods=['GET'])
def get_posts():
    sort_field = request.args.get('sort')
    sort_direction = request.args.get('direction')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    if sort_field:
        if sort_field not in ['title', 'content', 'author', 'date']:
            return jsonify({"error": "Invalid sort field. Must be 'title', 'content', 'author', or 'date'."}), 400
        if sort_direction not in ['asc', 'desc']:
            return jsonify({"error": "Invalid sort direction. Must be 'asc' or 'desc'."}), 400
        reverse = sort_direction == 'desc'
        sorted_posts = sorted(POSTS, key=lambda post: post[sort_field], reverse=reverse)
    else:
        sorted_posts = POSTS

    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = sorted_posts[start:end]

    return jsonify(paginated_posts)


@jwt_required()
@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.get_json()

    if not data or 'title' not in data or 'content' not in data or 'author' not in data or 'date' not in data:
        missing_fields = []
        if 'title' not in data:
            missing_fields.append('title')
        if 'content' not in data:
            missing_fields.append('content')
        if 'author' not in data:
            missing_fields.append('author')
        if 'date' not in data:
            missing_fields.append('date')
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    try:
        datetime.strptime(data['date'], '%Y-%m-%d')  # Validate date format
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    new_post_id = generate_new_id()
    new_post = {
        "id": new_post_id,
        "title": data['title'],
        "content": data['content'],
        "author": data['author'],
        "date": data['date']
    }
    POSTS.append(new_post)

    return jsonify(new_post), 201


@jwt_required()
@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    post = next((post for post in POSTS if post['id'] == id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404

    POSTS.remove(post)
    return jsonify({"message": f"Post with id {id} has been deleted successfully."}), 200


@jwt_required()
@app.route('/api/posts/<int:id>', methods=['PUT'])
def update_post(id):
    data = request.get_json()
    post = next((post for post in POSTS if post['id'] == id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404

    post['title'] = data.get('title', post['title'])
    post['content'] = data.get('content', post['content'])
    post['author'] = data.get('author', post['author'])
    post['date'] = data.get('date', post['date'])

    return jsonify(post), 200


@jwt_required()
@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    title_query = request.args.get('title')
    content_query = request.args.get('content')
    author_query = request.args.get('author')
    date_query = request.args.get('date')

    filtered_posts = POSTS
    if title_query:
        filtered_posts = [post for post in filtered_posts if title_query.lower() in post['title'].lower()]
    if content_query:
        filtered_posts = [post for post in filtered_posts if content_query.lower() in post['content'].lower()]
    if author_query:
        filtered_posts = [post for post in filtered_posts if author_query.lower() in post['author'].lower()]
    if date_query:
        filtered_posts = [post for post in filtered_posts if date_query in post['date']]

    return jsonify(filtered_posts), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
