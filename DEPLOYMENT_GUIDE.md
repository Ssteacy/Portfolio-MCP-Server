# Monday.com Portfolio MCP Server - Cloud Run Deployment Guide

## 📋 Prerequisites

1. **Google Cloud Project**
   - Active GCP project with billing enabled
   - Project ID ready (e.g., `pagerduty-portfolio-mcp`)

2. **gcloud CLI installed**
   ```bash
   # Check if installed
   gcloud --version

   # If not installed, visit:
   # https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticated with gcloud**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Your .env file** with all Monday.com credentials

---

## 🚀 Deployment Steps

### Step 1: Prepare Your Project

1. Copy these files to your `monday-portfolio-mcp` project root:
   - `requirements.txt`
   - `Dockerfile`
   - `.dockerignore`
   - `deploy.sh`

2. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```

### Step 2: Configure the Deployment

Edit `deploy.sh` and change:
```bash
PROJECT_ID="your-gcp-project-id"  # Change to your actual GCP project ID
```

Optional configurations:
- `REGION`: Default is `us-central1`
- `MEMORY`: Default is `512Mi` (increase if needed)
- `MIN_INSTANCES`: Set to `1` for always-on (costs more but faster response)
- `MAX_INSTANCES`: Default is `10`

### Step 3: Deploy

```bash
cd monday-portfolio-mcp
./deploy.sh
```

The script will:
1. ✅ Enable required GCP APIs
2. ✅ Create secrets in Secret Manager from your .env file
3. ✅ Build the Docker container
4. ✅ Deploy to Cloud Run
5. ✅ Output the service URL

**Expected output:**
```
✅ Deployment complete!

📍 Service URL: https://monday-portfolio-mcp-xxxxx-uc.a.run.app
```

---

## 🔐 Grant Access to Users

After deployment, grant access to team members:

```bash
# For a specific user
gcloud run services add-iam-policy-binding monday-portfolio-mcp \
  --region=us-central1 \
  --member='user:sean.steacy@pagerduty.com' \
  --role='roles/run.invoker'

# For a Google Group
gcloud run services add-iam-policy-binding monday-portfolio-mcp \
  --region=us-central1 \
  --member='group:leadership@pagerduty.com' \
  --role='roles/run.invoker'

# For a service account (for programmatic access)
gcloud run services add-iam-policy-binding monday-portfolio-mcp \
  --region=us-central1 \
  --member='serviceAccount:gemini-agent@project.iam.gserviceaccount.com' \
  --role='roles/run.invoker'
```

---

## 🤖 Connect to Gemini

### Option A: Google AI Studio (Quick Testing)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **Settings** → **Extensions** → **Add MCP Server**
3. Enter:
   - **Name**: Monday.com Portfolio Intelligence
   - **URL**: Your Cloud Run service URL
   - **Authentication**: Use service account with Cloud Run Invoker role
4. Save and test with a query like "What's the portfolio summary?"

### Option B: Vertex AI Agent Builder (Production)

1. Go to [Vertex AI Console](https://console.cloud.google.com/vertex-ai)
2. Navigate to **Agent Builder** → **Create Agent**
3. Configure:
   - **Agent Name**: Portfolio Intelligence Agent
   - **Tools**: Add your MCP server URL as an extension
   - **Authentication**: Configure service account
4. Deploy the agent
5. Share with users via:
   - Gemini in Google Workspace
   - Custom web app
   - API integration

### Option C: Direct API Integration

Use the Cloud Run URL directly with Gemini API:

```python
import google.generativeai as genai

# Configure Gemini with your MCP server
genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    tools=[{
        "function_declarations": [{
            "name": "monday_portfolio_mcp",
            "description": "Monday.com Portfolio Intelligence",
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string"},
                    "tool": {"type": "string"},
                    "arguments": {"type": "object"}
                }
            }
        }]
    }]
)
```

---

## 🧪 Testing Your Deployment

### Test 1: Health Check

```bash
SERVICE_URL="https://monday-portfolio-mcp-xxxxx-uc.a.run.app"

curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     $SERVICE_URL/health
```

### Test 2: MCP Tool Call

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_portfolio_summary",
    "arguments": {}
  }' \
  $SERVICE_URL/tools/call
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
gcloud run services logs read monday-portfolio-mcp \
  --region=us-central1 \
  --limit=50
```

### View Metrics
```bash
# Open Cloud Console
gcloud run services describe monday-portfolio-mcp \
  --region=us-central1 \
  --format="value(status.url)"
```

Then go to: Cloud Console → Cloud Run → monday-portfolio-mcp → Metrics

---

## 💰 Cost Estimation

**Cloud Run Pricing** (us-central1):
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month, 360,000 GiB-seconds/month

**Example monthly cost** (100 queries/day, avg 2s response):
- Requests: 3,000/month = ~$0.00
- CPU: 3,000 × 2s × 1 vCPU × $0.000024 = $0.14
- Memory: 3,000 × 2s × 0.5 GiB × $0.0000025 = $0.01
- **Total: ~$0.15/month** (within free tier)

**Secret Manager**: $0.06 per secret per month × ~40 secrets = $2.40/month

**Estimated Total: ~$2.50/month**

---

## 🔧 Troubleshooting

### Issue: "Permission denied"
**Solution**: Grant Cloud Run Invoker role to the user/service account

### Issue: "Service unavailable"
**Solution**: Check logs for errors:
```bash
gcloud run services logs read monday-portfolio-mcp --region=us-central1
```

### Issue: "Timeout"
**Solution**: Increase timeout in deploy.sh:
```bash
--timeout 600  # 10 minutes
```

### Issue: "Out of memory"
**Solution**: Increase memory in deploy.sh:
```bash
MEMORY="1Gi"
```

---

## 🔄 Updating the Service

After making code changes:

```bash
# Simply re-run the deployment script
./deploy.sh
```

Cloud Run will:
1. Build a new container
2. Deploy with zero downtime
3. Route traffic to the new version

---

## 🔐 Security Best Practices

✅ **Secrets in Secret Manager** (not in code)
✅ **IAM-based authentication** (no public access)
✅ **VPC connector** (optional, for IP whitelisting)
✅ **Cloud Armor** (optional, for DDoS protection)
✅ **Audit logging** (enabled by default)

---

## 📞 Support

**Issues?** Check:
1. Cloud Run logs: `gcloud run services logs read monday-portfolio-mcp`
2. Secret Manager: Ensure all secrets are created
3. IAM permissions: Verify Cloud Run Invoker role
4. Monday.com API: Test API token separately

**Questions?** Contact: sean.steacy@pagerduty.com

---

## 🎯 Next Steps

1. ✅ Deploy to Cloud Run
2. ✅ Grant access to team members
3. ✅ Connect to Gemini
4. ✅ Test with sample queries
5. ✅ Share with stakeholders
6. ✅ Monitor usage and costs

**Happy querying! 🚀**
