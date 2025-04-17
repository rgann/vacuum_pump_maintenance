# Vacuum Pump Maintenance Application

A web application for tracking and managing vacuum pump maintenance.

## Features

- Dashboard with temperature trends and service distribution
- Weekly maintenance logs
- Equipment management
- Maintenance records tracking
- Google OAuth authentication
- Arcade-style UI with high score board for pump owners

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python with Flask
- **Database**: PostgreSQL (hosted on Supabase)
- **Authentication**: Google OAuth
- **Deployment**: Render

## Deployment on Render with Supabase

This application is configured for deployment on Render's free tier with a Supabase database.

### Step 1: Set Up Supabase

1. **Create a Supabase Account**
   - Go to [supabase.com](https://supabase.com) and sign up for a free account
   - Verify your email address

2. **Create a New Project**
   - Create a new project in Supabase
   - Note down your project URL and API key
   - Get your database connection information from the Settings > Database page

3. **Populate the Database**
   - Update your `.env` file with your Supabase credentials
   - Run the population script: `python populate_supabase.py`

### Step 2: Set Up Google OAuth

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Set up OAuth credentials
   - Add authorized redirect URIs:
     - `https://your-render-app-name.onrender.com/authorize`
     - `http://localhost:5000/authorize` (for local development)

### Step 3: Deploy to Render

1. **Create a GitHub Repository**
   - Push all the code to a GitHub repository
   - Make sure to include all the files created for deployment

2. **Sign Up for Render**
   - Go to [render.com](https://render.com) and sign up for a free account
   - Verify your email address

3. **Create a New Web Service**
   - From the Render dashboard, click "New +" and select "Web Service"
   - Connect your GitHub account if you haven't already
   - Select the repository containing this application

4. **Configure the Web Service**
   - Name: vacuum-pump-maintenance (or any name you prefer)
   - Environment: Python
   - Region: Choose the one closest to your users
   - Branch: main (or your default branch)
   - Build Command: The render.yaml file will handle this
   - Start Command: The render.yaml file will handle this
   - Plan: Free

5. **Set Environment Variables**
   - In the Render dashboard, go to your web service
   - Click on "Environment" in the left sidebar
   - Add the following environment variables:
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your Supabase API key
     - `SUPABASE_DB_HOST`: Your Supabase database host
     - `SUPABASE_DB_NAME`: Usually "postgres"
     - `SUPABASE_DB_USER`: Usually "postgres.your-project-id"
     - `SUPABASE_DB_PASSWORD`: Your database password
     - `SUPABASE_DB_PORT`: Usually "6543"
     - `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
     - `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
     - `ALLOWED_EMAIL_DOMAINS`: south8technologies.com,south8.com
     - `ADMIN_EMAILS`: Your admin email addresses

6. **Create Web Service**
   - Click "Create Web Service"
   - Render will automatically detect the render.yaml configuration
   - Wait for the build and deployment to complete (this may take a few minutes)

7. **Access Your Application**
   - Once deployment is complete, Render will provide a URL (e.g., https://vacuum-pump-maintenance.onrender.com)
   - Click the URL to access your application

### Troubleshooting

If you encounter any issues during deployment:

1. Check the build logs in the Render dashboard
2. Make sure all required environment variables are set correctly
3. Verify that the Supabase database is properly configured and populated
4. Check the application logs for any runtime errors
5. Test the Supabase connection: `python test_supabase.py`

## Local Development

To run this application locally:

1. Clone the repository
2. Create a `.env` file with the required environment variables
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `flask run`
5. Access the application at http://127.0.0.1:5000/

## License

This project is proprietary and confidential.
