import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import requests  # For making HTTP requests
import json

app = Flask(__name__)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure your Gemini API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to generate dynamic content using Gemini API
def generate_dynamic_content(json,context):
    prompt2 = f"str({json}) modify the content of the given json string according to the context {context},return response as purely json string" 
    headers = {
        'Authorization': f'Bearer {GEMINI_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt2,
        'max_tokens': 1500
    }
    response = requests.post('https://api.gemini.com/v1/completions', headers=headers, json=data)
    response_json = response.json()
    return response_json['choices'][0]['text'].strip()

def load_content():
    with open('content.json', 'r') as f:
        content = json.load(f)
    return content

@app.route('/content')
def home():
    content = load_content()  # Load the content from JSON
    newcontent = generate_dynamic_content(str(content),"Ecommerce")
    return newcontent 
    return render_template('template.html', content=content)

@app.route('/')
def index():
    # Get the filenames from query parameters (if available)
    logo_filename = request.args.get('logo', 'default_logo.png')
    image_filename = request.args.get('image', 'default_image.png')

    # Generate dynamic content
    prompt = "Provide a catchy headline for a real estate website."
    dynamic_content = generate_dynamic_content(prompt)

    return render_template('index.html', 
                           logo_filename=logo_filename, 
                           image_filename=image_filename,
                           dynamic_content=dynamic_content)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    message = None
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'logo' not in request.files or 'image' not in request.files:
            message = "No file part"
        else:
            logo = request.files['logo']
            image = request.files['image']

            if logo and allowed_file(logo.filename):
                logo_filename = secure_filename(logo.filename)
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

            if image and allowed_file(image.filename):
                image_filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            # Redirect to the home page and pass the uploaded filenames as query parameters
            message = "Files uploaded successfully"
            return redirect(url_for('index', logo=logo_filename, image=image_filename))

    return render_template('upload.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
