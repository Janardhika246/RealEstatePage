import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai  # Import the Gemini API SDK
import json
import requests

app = Flask(__name__)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure your Gemini API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

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


def search_pexels(query, per_page=1):
    # Get your Pexels API key from the environment variable
    api_key = os.getenv('PEXELS_API_KEY')
    
    # Define the endpoint and headers
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}"
    headers = {
        "Authorization": api_key
    }

    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Return the URL of the first image (large size)
        data=response.json()  # Return the JSON response
        if data['photos']:
            print(data['photos'][0])
            return data['photos'][0]['src']['original']
        else:
            return None  # No image found
    else:
        return {"error": f"Failed to fetch images. Status code: {response.status_code}"}

# Function to search for images on Pexels
def search_image_on_pexels(query):
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    params = {
        'query': query,
        'per_page': 1  # We only want one image for now
    }
    response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Return the URL of the first image (large size)
        if data['photos']:
            return data['photos'][0]['src']['large']
        else:
            return None  # No image found
    else:
        return None  # Error occurred during the request

# Load the content from a JSON file
def load_content():
    with open('content.json', 'r') as f:
        content = json.load(f) 
    return content


@app.route('/sample')
def sample():
    return render_template("sample.html")

@app.route('/content',methods=['GET'])
def home():
    content = load_content()  # Load the content from JSON
    context=request.args.get('context')

    # Dynamically set the context in the prompt based on the URL
    prompt = f"Modify the content of the following JSON: {content}, in the context of {context}, response should be a pure JSON string, that can be directly parsed into a JSON object, avoid including any additional text content outside the JSON string"
    
    new_content = generate_dynamic_content(prompt)
    
    try:
        # Convert the string response to a JSON object
        new_content_json = json.loads(new_content)

        for section in new_content_json.get('sections', []):
            if 'feature_name' in section:
                image_url = search_pexels(section['feature_name'])
                if image_url:
                    section['feature_image_src'] = image_url  # Replace the image URL with Pexels image

        # Assume the feature name is stored in the 'feature_name' field of your JSON
        feature_name = new_content_json.get('feature_name', 'nature')  # Default to 'nature' if feature_name not found
        print(feature_name)

        # Fetch the image URL from Pexels
        image_url = search_pexels(feature_name)
        print(image_url)

        # Add the image URL to the content JSON for rendering in the template
        new_content_json['image_url'] = image_url if image_url else 'default_image.png'  # Default image if no image found

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse generated content as JSON.", "response": new_content})

    # Pass the new content JSON to the template, including the image URL
    return render_template('template.html', content=new_content_json)
    # return new_content_json
  
# Home endpoint with input form
@app.route('/')
def input_form():
    return render_template('input_form.html')

# @app.route('/')
# def index():
#     # Get the filenames from query parameters (if available)
#     logo_filename = request.args.get('logo', 'default_logo.png')
#     image_filename = request.args.get('image', 'default_image.png')

#     # Generate dynamic content
#     prompt = "Provide a catchy headline for a real estate website."
#     dynamic_content = generate_dynamic_content(prompt)

#     return render_template('index.html', 
#                            logo_filename=logo_filename, 
#                            image_filename=image_filename,
#                            dynamic_content=dynamic_content)

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
                logo_filename = "QRealtor Logo.png"
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

            if image and allowed_file(image.filename):
                image_filename = secure_filename("QRealtor_hero.png")
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            # Redirect to the home page and pass the uploaded filenames as query parameters
            message = "Files uploaded successfully"
            return redirect(url_for('home'))

    return render_template('input_form.html',message=message)

if __name__ == '__main__':
    app.run(debug=True)
