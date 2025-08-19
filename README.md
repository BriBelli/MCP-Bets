# BetAIPredict

A hyper-personalized betting oracle that predicts, educates, engages, and monetizes users intelligently with AI-powered insights and secure authentication.

## 🚀 Features

- **🔐 Auth0 Authentication** - Secure user login and registration
- **🤖 AI-Powered Predictions** - OpenAI integration for betting insights
- **📱 Modern React Frontend** - TypeScript-based responsive UI
- **🐍 Python Flask Backend** - RESTful API with OpenAI service
- **🔒 Secure Environment Management** - Industry-standard secret handling

## 📁 Project Structure

```
BetAIPredict/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── openai_service.py      # OpenAI integration
│   ├── requirements.txt       # Python dependencies
│   └── README.md             # Backend documentation
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main React component with Auth0
│   │   ├── index.tsx         # Auth0Provider setup
│   │   └── services/
│   │       └── openaiApi.ts  # Frontend API client
│   ├── .env.local           # Frontend environment variables
│   ├── package.json         # Node.js dependencies
│   └── README.md            # Frontend documentation
└── README.md                # This file
```

## 🛠️ Setup Instructions

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- Auth0 Account
- OpenAI API Key

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd BetAIPredict
```

### 2. Environment Variables Setup

#### Frontend Environment Variables
Create `frontend/.env.local`:
```bash
# Auth0 Configuration (Safe for browser)
REACT_APP_AUTH0_DOMAIN=your-auth0-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your_auth0_client_id
REACT_APP_AUTH0_AUDIENCE=your_api_identifier

# Application Settings
PORT=3000
```

#### Backend Environment Variables
Add to your `~/.zshrc` (or shell profile):
```bash
# Sensitive secrets - NEVER commit these
export OPENAI_API_KEY="your_openai_api_key"
export AUTH0_SECRET="your_32_byte_secret"
export AUTH0_CLIENT_SECRET="your_auth0_client_secret"
```

Then reload your shell:
```bash
source ~/.zshrc
```

### 3. Authentication (Already Configured!)

✅ **Auth0 is already set up and configured for this project!** You don't need to create your own Auth0 account.

The project uses:
- **Domain**: `dev-iep8px1emd3ipkkp.us.auth0.com` 
- **Client ID**: `3Z6o8Yvey48FOeGHILCr9czwJ6iHuQpQ`

**For basic development, only add to `~/.zshrc`:**
```bash
# Required for OpenAI functionality
export OPENAI_API_KEY="your_openai_api_key"
```

**Additional secrets (only needed for backend Auth0 integration):**
```bash
# Only add these if implementing backend token validation
export AUTH0_SECRET="your_32_byte_secret" 
export AUTH0_CLIENT_SECRET="your_auth0_client_secret"
```

**Generate AUTH0_SECRET (if needed):**
```bash
openssl rand -hex 32
```

> 💡 **For Team Leads**: If you need to create a new Auth0 application or modify settings, see the [Auth0 Setup Guide](#auth0-setup-for-team-leads) below.

### 4. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
```
Server runs on `http://localhost:5000`

### 5. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start React development server
npm start
```
Application runs on `http://localhost:3000`

## 🔒 Security Notes

- **Environment Variables**: Sensitive secrets are stored in `~/.zshrc`, not in project files
- **Git Security**: `.env.local` contains only safe, non-secret values
- **Auth0 Integration**: Secure authentication flow with JWT tokens
- **API Protection**: Backend endpoints can be protected with Auth0 middleware

## 🎯 Usage

1. **Access the Application**: Open `http://localhost:3000`
2. **Authentication**: Click "Login" or "Sign Up" to authenticate via Auth0
3. **AI Predictions**: Once logged in, use the OpenAI prompt interface
4. **User Profile**: View your Auth0 user profile and logout

## 🔧 Development

### Available Scripts (Frontend)
- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests

### Available Scripts (Backend)
- `python app.py` - Start Flask server
- `pip install -r requirements.txt` - Install dependencies

## 📚 Technology Stack

- **Frontend**: React 19, TypeScript, Auth0 React SDK
- **Backend**: Python Flask, OpenAI API
- **Authentication**: Auth0 (OAuth 2.0 / OpenID Connect)
- **Build Tools**: Create React App, Node.js
- **Environment**: Industry-standard environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Set up your environment variables following the setup guide
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

---

## 🔧 Auth0 Setup for Team Leads

<details>
<summary>Click to expand - Only needed if creating new Auth0 application</summary>

If you need to create a new Auth0 application or modify existing settings:

### 1. Create Auth0 Application
- Go to [Auth0 Dashboard](https://manage.auth0.com/)
- Create a new Single Page Application
- Note your Domain and Client ID

### 2. Configure Application URLs
- **Allowed Callback URLs**: `http://localhost:3000/`
- **Allowed Logout URLs**: `http://localhost:3000/`
- **Allowed Web Origins**: `http://localhost:3000/`

### 3. Update Environment Variables
Update the values in `frontend/.env.local`:
```bash
REACT_APP_AUTH0_DOMAIN=your-new-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your_new_client_id
```

</details>
