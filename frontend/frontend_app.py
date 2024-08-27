from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    """
    This function is the route handler for 
    the root URL ("/") of the web application.
    It returns the rendered HTML template "index.html".

    Parameters:
    None

    Returns:
    str: The rendered HTML content of the "index.html" template.
    """
    return render_template("index.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
