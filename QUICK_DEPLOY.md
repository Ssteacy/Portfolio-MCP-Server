# 🚀 Quick Deployment Reference

## One-Time Setup (5 minutes)

1. **Install gcloud CLI** (if not already installed)
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Create GCP Project** (or use existing)
   ```bash
   gcloud projects create pagerduty-portfolio-mcp --name="Portfolio MCP"
   gcloud config set project pagerduty-portfolio-mcp

   # Enable billing (required for Cloud Run)
   # Visit: https://console.cloud.google.com/billing
   ```

---

## Deploy (2 minutes)

1. **Copy deployment files to your project**
   - requirements.txt
   - Dockerfile
   - .dockerignore
   - deploy.sh

2. **Edit deploy.sh**
   ```bash
   # Change this line:
   PROJECT_ID="pagerduty-portfolio-mcp"  # Your actual project ID
   ```

3. **Make executable and run**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Copy the service URL** from output
   ```
   📍 Service URL: https://monday-portfolio-mcp-xxxxx-uc.a.run.app
   ```

---

## Grant Access (30 seconds per user)

```bash
gcloud run services add-iam-policy-binding monday-portfolio-mcp \
  --region=us-central1 \
  --member='user:EMAIL@pagerduty.com' \
  --role='roles/run.invoker'
```

---

## Connect to Gemini (2 minutes)

### Option 1: Google AI Studio (Easiest)
1. Go to https://aistudio.google.com/
2. Settings → Extensions → Add MCP Server
3. Paste your Cloud Run URL
4. Test: "What's the portfolio summary?"

### Option 2: Vertex AI Agent (Production)
1. Go to https://console.cloud.google.com/vertex-ai
2. Agent Builder → Create Agent
3. Add your MCP server URL as a tool
4. Deploy and share

---

## Update After Code Changes

```bash
./deploy.sh  # That's it!
```

---

## Troubleshooting

**Check logs:**
```bash
gcloud run services logs read monday-portfolio-mcp --region=us-central1 --limit=50
```

**Test endpoint:**
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     https://YOUR-SERVICE-URL/health
```

---

## Cost: ~$2.50/month

- Cloud Run: Free tier covers typical usage
- Secret Manager: ~$2.40/month for 40 secrets
- No charges when idle (min instances = 0)

---

## Support

📧 sean.steacy@pagerduty.com
📖 Full guide: DEPLOYMENT_GUIDE.md
