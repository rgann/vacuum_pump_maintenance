# Vacuum Pump Maintenance Application

A web application for tracking and managing vacuum pump maintenance.

## Features

- Dashboard with temperature trends and service distribution
- Weekly maintenance logs
- Equipment management
- Maintenance records tracking

## Deployment on Render

This application is configured for deployment on Render's free tier.

### Step-by-Step Deployment Instructions

1. **Create a GitHub Repository**
   - Push all the code to a new GitHub repository
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

5. **Create Web Service**
   - Click "Create Web Service"
   - Render will automatically detect the render.yaml configuration
   - Wait for the build and deployment to complete (this may take a few minutes)

6. **Access Your Application**
   - Once deployment is complete, Render will provide a URL (e.g., https://vacuum-pump-maintenance.onrender.com)
   - Click the URL to access your application

### Troubleshooting

If you encounter any issues during deployment:

1. Check the build logs in the Render dashboard
2. Make sure all required files are included in your repository
3. Verify that the database is properly initialized
4. Check the application logs for any runtime errors

## Local Development

To run this application locally:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Access the application at http://127.0.0.1:5000/

## License

This project is licensed under the MIT License - see the LICENSE file for details.
