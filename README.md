# Moodle Notification System

This project is an automated system for monitoring courses on an Moodle and sending notifications about any changes, additions, or removals of course content. The system logs in to the Moodle, retrieves course details, compares the current state with the previous state, and sends notifications if any changes are detected.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Functions](#functions)
- [Deploying on Hugging Face Spaces](#deploying-on-hugging-face-spaces)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/KenKout/moodle_notification.git
   cd moodle_notification
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root directory of the project and add the following variables:

   ```sh
   USERNAME=your_moodle_username
   PASSWORD=your_moodle_password
   URL_LOGIN=https://lms.hcmut.edu.vn/
   URL_CAS=https://sso.hcmut.edu.vn/cas/login?service=
   TYPE_SSO=CAS
   MONGODB_URI=mongodb://localhost:27017/
   WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
   TIME_SLEEP=300
   ```

## Configuration

- **USERNAME**: Your Moodle username.
- **PASSWORD**: Your Moodle password.
- **URL_LOGIN**: The login URL for your Moodle.
- **URL_CAS**: The CAS URL for single sign-on (SSO) if applicable.
- **TYPE_SSO**: The type of SSO used (e.g., 'CAS').
- **MONGODB_URI**: The MongoDB URI for storing course data.
- **WEBHOOK_URL**: The Discord webhook URL for sending notifications.
- **TIME_SLEEP**: The time interval (in seconds) between each check for course updates.

## Usage

1. **Run the script:**

   ```sh
   python main.py
   ```

2. **Monitoring and Notifications:**

   The script will log in to the Moodle, retrieve course details, and compare them with the previous state. If any changes are detected, it will send notifications via the specified Discord webhook.

## Functions

### `main.py`

- **MOODLE_NOTI class**:
  - `__init__`: Initializes the session and course details.
  - `login_sso`: Handles SSO login.
  - `login_moodle`: Handles Moodle login.
  - `get_course`: Retrieves the list of courses.
  - `get_course_detail(courseid)`: Retrieves details for a specific course.
  - `process_data(data)`: Processes course data into a structured format.

- **refresh_course(lms)**: Continuously refreshes course data at specified intervals.

### `helper.py`

- **convert_html_to_text(html_content)**: Converts HTML content to plain text.
- **diff_compare(old, new, is_module=False)**: Compares old and new course data to detect changes.
- **upload_data(data)**: Uploads data to MongoDB.
- **get_data(query=None)**: Retrieves data from MongoDB.
- **update_data(data)**: Updates data in MongoDB.
- **send_notification(data)**: Sends notifications via Discord webhook.

## Deploying on Hugging Face Spaces

This project can be deployed on Hugging Face Spaces for free hosting. Follow these steps to deploy:

1. **Create a Hugging Face account:**
   If you don't have one, sign up at [https://huggingface.co/](https://huggingface.co/).

2. **Create a new Space:**
   - Go to [https://huggingface.co/spaces](https://huggingface.co/spaces) and click on "Create new Space".
   - Choose "Docker" as the SDK.
   - Give your Space a name and set the visibility as desired.

3. **Configure the Space:**
   - In the Space settings, add the following environment variables:
     - USERNAME
     - PASSWORD
     - URL_LOGIN
     - URL_CAS
     - TYPE_SSO
     - MONGODB_URI
     - WEBHOOK_URL
     - TIME_SLEEP
   - Ensure these variables are set to the appropriate values for your setup.

4. **Upload the project files:**
   - Use the Hugging Face web interface or git to upload your project files to the Space.
   - Make sure to include the Dockerfile, requirements.txt, and all necessary Python files.

5. **Build and deploy:**
   - Hugging Face will automatically detect the Dockerfile and build the container.
   - Once the build is complete, your app will be deployed and accessible via the provided URL.

6. **Access your app:**
   - Your app will now be running and accessible through the Hugging Face Spaces URL.
   - You can monitor the logs and manage your app through the Hugging Face interface.

## Contributing

1. **Fork the repository.**
2. **Create a new branch:**

   ```sh
   git checkout -b feature-branch
   ```

3. **Make your changes.**
4. **Commit your changes:**

   ```sh
   git commit -m 'Add some feature'
   ```

5. **Push to the branch:**

   ```sh
   git push origin feature-branch
   ```

6. **Submit a pull request.**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.