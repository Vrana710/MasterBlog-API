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
    { 
     "id": 1,
     "title": "First post", 
     "content": "This is the first post.", 
     "author": "Author One", 
     "date": "2023-01-01"
     },
    {
        "id": 2, 
        "title": "Second post", 
        "content": "This is the second post.", 
        "author": "Author Two", 
        "date": "2023-02-01"
        },
]


def generate_new_id():
    """
    Generates a new unique identifier for blog posts.

    This function checks the existing blog posts in 
    the 'POSTS' list and generates a new unique identifier.
    If the 'POSTS' list is not empty, it finds the 
    maximum existing identifier and increments it by 1.
    If the 'POSTS' list is empty, it returns 1 as the first identifier.

    Returns:
    int: The new unique identifier for a blog post.
    """
    if POSTS:
        return max(post['id'] for post in POSTS) + 1
    else:
        return 1


@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user.

    This function handles the POST request to the '/register' endpoint. 
    It expects a JSON payload containing
    'username' and 'password' fields. It validates the input, 
    checks if the username already exists, and
    hashes the password before storing the user in the 'users' dictionary.

    Parameters:
    - data (dict): The JSON payload containing 'username' and 'password' fields.

    Returns:
    - JSON response with a success message or an error message and HTTP status code.
    """
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
    """
    Authenticates a user and generates an access token for subsequent API requests.

    This function handles the POST request to the '/login' endpoint. It expects a JSON      payload containing
    'username' and 'password' fields. It validates the input, 
    checks if the username and password match
    the stored credentials, and generates an access token using 
    JWT if the credentials are valid.

    Parameters:
    - data (dict): The JSON payload containing 'username' and 'password' fields.

    Returns:
    - JSON response with an 'access_token' field if the credentials are valid.
    - JSON response with an 'error' field and 
      HTTP status code 400 if the 'username' or 'password' is missing.
    - JSON response with an 'error' field and 
      HTTP status code 401 if the credentials are invalid.
    """
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
    """
    Retrieves a paginated list of blog posts, optionally sorted by 
    a specified field and direction.

    Parameters:
    - sort_field (str): The field to sort the blog posts by. 
      Must be one of 'title', 'content', 'author', or 'date'.
      If not provided, the posts will be returned in their original order.
    - sort_direction (str): The direction to sort the blog posts. 
      Must be 'asc' for ascending order or 'desc' for descending order.
      If not provided, the posts will be sorted in ascending order.
    - page (int): The page number to retrieve. Default is 1.
    - per_page (int): The number of blog posts per page. Default is 10.

    Returns:
    - JSON response containing a list of paginated blog posts.
    """
    sort_field = request.args.get('sort')
    sort_direction = request.args.get('direction')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    if sort_field:
        if sort_field not in ['title', 'content', 'author', 'date']:
            return jsonify(
                    {
                    "error": "Invalid sort field. Must be 'title', 'content', 'author', or 'date'."
                    }
                ), 400
        if sort_direction not in ['asc', 'desc']:
            return jsonify(
                {
                    "error": "Invalid sort direction. Must be 'asc' or 'desc'."
                    }
                ), 400
        reverse = sort_direction == 'desc'
        sorted_posts = sorted(POSTS, 
                              key=lambda post: post[sort_field], 
                              reverse=reverse)
    else:
        sorted_posts = POSTS

    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = sorted_posts[start:end]

    return jsonify(paginated_posts)


@jwt_required()
@app.route('/api/posts', methods=['POST'])
def add_post():
    """
    Adds a new blog post to the 'POSTS' list.

    This function handles the POST request to the '/api/posts' endpoint. 
    It expects a JSON payload containing the 
    fields 'title', 'content', 'author', and 'date'. 
    The function validates the input, checks for 
    missing fields, validates the date format, 
    generates a new unique identifier for 
    the blog post, creates a new post dictionary, 
    and appends it to the 'POSTS' list.

    Parameters:
    - data (dict): The JSON payload containing the 
    fields 'title', 'content', 'author', and 'date'.

    Returns:
    - JSON response containing the newly created blog post 
    with HTTP status code 201 if the post is added successfully.
    - JSON response with an 'error' field and 
    HTTP status code 400 if any required fields are 
    missing or the date format is invalid.
    """
    data = request.get_json()

    if (not data or 'title' 
        not in data or 'content' 
        not in data or 'author' 
        not in data or 'date' 
        not in data):
        missing_fields = []
        if 'title' not in data:
            missing_fields.append('title')
        if 'content' not in data:
            missing_fields.append('content')
        if 'author' not in data:
            missing_fields.append('author')
        if 'date' not in data:
            missing_fields.append('date')
        return jsonify(
            {
                "error": f"Missing fields: {', '.join(missing_fields)}"
                }
            ), 400

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
    """
    Deletes a blog post with the specified ID.

    This function handles the DELETE request to the '/api/posts/<id>' endpoint.
    It finds the blog post with the specified 'id' in the 'POSTS' list,
    removes it from the list, and returns a success message as a JSON response.

    Parameters:
    - id (int): The unique identifier of the blog post to delete.

    Returns:
    - JSON response with a success message and 
    HTTP status code 200 if the post is found and deleted successfully.
    - JSON response with an 'error' field and 
    HTTP status code 404 if the post is not found.
    """
    post = next((post for post in POSTS if post['id'] == id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404

    POSTS.remove(post)
    return jsonify(
        {
            "message": f"Post with id {id} has been deleted successfully."
            }
        ), 200


@jwt_required()
@app.route('/api/posts/<int:id>', methods=['PUT'])
def update_post(id):
    """
    Updates an existing blog post with the provided data.

    This function handles the PUT request to the '/api/posts/<id>' endpoint. 
    It expects a JSON payload containing
    updated fields for the blog post. 
    The function finds the blog post with the specified 'id' in the 'POSTS' list,
    updates the fields with the provided data, 
    and returns the updated blog post as a JSON response.

    Parameters:
    - id (int): The unique identifier of the blog post to update.

    Returns:
    - JSON response containing the updated blog post 
    if the post is found and updated successfully.
    - JSON response with an 'error' field and 
    HTTP status code 404 if the post is not found.
    """
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
    """
    Searches for blog posts based on provided search criteria.

    This function handles the GET request to the '/api/posts/search' endpoint. 
    It retrieves search criteria
    from the query parameters and filters 
    the blog posts based on the provided criteria. 
    The function returns
    a JSON response containing the filtered blog posts.

    Parameters:
    - title_query (str): The title to search for. 
    If provided, the function filters the blog posts based on the title.
    - content_query (str): The content to search for. 
    If provided, the function filters the blog posts based on the content.
    - author_query (str): The author to search for. 
    If provided, the function filters the blog posts based on the author.
    - date_query (str): The date to search for. 
    If provided, the function filters the blog posts based on the date.

    Returns:
    - JSON response containing a list of filtered blog posts.
    """
    title_query = request.args.get('title')
    content_query = request.args.get('content')
    author_query = request.args.get('author')
    date_query = request.args.get('date')

    filtered_posts = POSTS
    if title_query:
        filtered_posts = [post for post 
                          in filtered_posts 
                          if title_query.lower() in post['title'].lower()]
    if content_query:
        filtered_posts = [post for post 
                          in filtered_posts 
                          if content_query.lower() in post['content'].lower()]
    if author_query:
        filtered_posts = [post for post 
                          in filtered_posts 
                          if author_query.lower() in post['author'].lower()]
    if date_query:
        filtered_posts = [post for post 
                          in filtered_posts 
                          if date_query in post['date']]

    return jsonify(filtered_posts), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
