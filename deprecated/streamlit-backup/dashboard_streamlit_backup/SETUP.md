# Cognitive Insights Dashboard Setup

## Prerequisites

To enable AI-powered cognitive insights, you need to configure an OpenAI API key.

## Setup Steps

### 1. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the API key (starts with `sk-...`)

### 2. Configure Environment Variables

Create a `.env` file in the project root directory with:

```bash
# OpenAI API Key (Required for AI insights)
OPENAI_API_KEY=your_openai_api_key_here

# Trading Configuration
OFFLINE_MODE=false
LOG_LEVEL=INFO
```

### 3. Install Dependencies

Make sure OpenAI package is installed:

```bash
pip install openai
```

### 4. Restart Dashboard

After configuration, restart the dashboard:

```bash
python dashboard/main.py
```

## Features Available

### With OpenAI API Key (Hybrid Mode)
- ✅ AI-powered market sentiment analysis
- ✅ Real-time trading insights 
- ✅ Strategy recommendations
- ✅ Risk analysis and predictions
- ✅ Performance insights
- ✅ System health monitoring

### Without API Key (Offline Mode)
- ⚠️ Limited mock data
- ⚠️ No real AI analysis
- ⚠️ Basic system monitoring only

## Troubleshooting

### "OpenAI package not installed"
```bash
pip install openai
```

### "OpenAI API Key: Missing"
1. Check your `.env` file exists in project root
2. Verify API key is correctly set
3. Restart the dashboard

### "Cognitive system is currently offline"
This is normal if:
- GCP cognitive system is not available
- System will automatically use hybrid mode with OpenAI
- AI insights will still work via OpenAI API

## Security Notes

- Never commit your `.env` file to version control
- Keep your API key secure and private
- Monitor your OpenAI usage and billing 