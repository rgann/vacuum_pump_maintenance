# Migrating to Supabase

This document provides instructions for migrating the Vacuum Pump Maintenance application from Render's PostgreSQL database to Supabase.

## Prerequisites

1. A Supabase account (sign up at [supabase.com](https://supabase.com/))
2. A Supabase project created for this application
3. The Supabase connection information (URL, API key, database credentials)

## Setup Steps

### 1. Create a Supabase Project

1. Sign up or log in to [Supabase](https://supabase.com/)
2. Create a new project:
   - Name: `vacuum-pump-maintenance` (or your preferred name)
   - Database Password: Create a secure password
   - Region: Choose the region closest to your users
   - Pricing Plan: Free tier is sufficient for most use cases

### 2. Get Your Connection Information

After creating your project, collect the following information:

1. From the Supabase dashboard, go to "Settings" > "API":
   - **Project URL**: Copy the URL (e.g., `https://abcdefghijklm.supabase.co`)
   - **API Key**: Copy the `anon` public key

2. From "Settings" > "Database":
   - **Host**: The database host (e.g., `db.abcdefghijklm.supabase.co`)
   - **Database Name**: Usually `postgres`
   - **User**: Usually `postgres`
   - **Password**: The database password you set when creating the project
   - **Port**: Usually `5432`

### 3. Configure Environment Variables

Create a `.env` file in the root of your project with the following variables:

```
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_DB_HOST=db.your-project-id.supabase.co
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_PORT=5432

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ALLOWED_EMAIL_DOMAINS=south8technologies.com,south8.com
ADMIN_EMAILS=admin@example.com
```

Replace the placeholder values with your actual Supabase credentials.

### 4. Test the Supabase Connection

Run the test script to verify your Supabase connection:

```bash
python test_supabase.py
```

This script will check:
- If all required environment variables are set
- If the database connection works
- If the Supabase API connection works
- If SQLAlchemy can connect to the database

### 5. Migrate Your Data

Once the connection is verified, run the migration script:

```bash
python migrate_to_supabase.py
```

This script will:
1. Backup your current data to a JSON file
2. Set up the database schema in Supabase
3. Migrate your data to Supabase
4. Verify the migration was successful

### 6. Update Your Deployment

If you're using Render for deployment:

1. Add the Supabase environment variables to your Render service
2. Remove the Render PostgreSQL database service (optional, you can keep it as a backup)
3. Deploy your application

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Check that your IP is allowed in Supabase:
   - Go to "Settings" > "Database" > "Connection Pooling"
   - Add your IP address to the allowed list or enable "Allow all connections"

2. Verify your credentials:
   - Double-check all connection information
   - Make sure you're using the correct password

3. Check Supabase status:
   - Visit the Supabase status page to check for any service disruptions

### Migration Issues

If the migration fails:

1. Check the logs for specific error messages
2. Verify that your backup file was created correctly
3. Try running the migration script with a smaller dataset first
4. Manually create the tables in Supabase if needed

## Benefits of Using Supabase

- **Managed PostgreSQL**: Supabase provides a fully managed PostgreSQL database
- **Authentication**: Built-in authentication services (which you can integrate later)
- **Real-time**: Real-time capabilities for live updates
- **Storage**: File storage capabilities
- **Edge Functions**: Serverless functions for backend logic
- **Free Tier**: Generous free tier for small applications
