import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai  # Import the Gemini API SDK
import json

app = Flask(__name__)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure your Gemini API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to generate dynamic content using Gemini API
def generate_dynamic_content(prompt):
    try:
        # Use the Gemini API to generate content
        model = genai.GenerativeModel('gemini-1.5-flash',
                              # Set the `response_mime_type` to output JSON
                              generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)

        # Check if the response contains the text attribute
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            return "Error: No content generated."

    except Exception as e:
        return f"Error: {str(e)}"

# Load the content from a JSON file
def load_content():
    with open('content.json', 'r') as f:
        content = json.load(f)
    return content



@app.route('/content/<context>')
def home(context):
    content = load_content()  # Load the content from JSON
    
    # Dynamically set the context in the prompt based on the URL
    prompt = f"Modify the content of the following JSON: {content}, in the context of {context}, response should be a pure JSON string, that can be directly parsed into a JSON object, avoid including any additional text content outside the JSON string"
    
    new_content = generate_dynamic_content(prompt)
    
    try:
        # Convert the string response to a JSON object
        new_content_json = json.loads(new_content)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse generated content as JSON.", "response": new_content})

    return render_template('template.html', content=new_content_json)

  


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
