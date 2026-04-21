# Tool Selection Test Results

**Date:** 2026-04-21
**MCP Server Version:** [commit hash]
**Testing Environment:** Gemini CLI

---

## Test Results Summary

| Category | Total | Correct | Accuracy | Notes |
|----------|-------|---------|----------|-------|
| Risk & Escalation (1-10) | 10 | TBD | TBD% | |
| Health Metrics (11-20) | 10 | TBD | TBD% | |
| Structure/Inventory (21-30) | 10 | TBD | TBD% | |
| Search/Filter (31-40) | 10 | TBD | TBD% | |
| Single Project (41-50) | 10 | TBD | TBD% | |
| Change Tracking (51-60) | 10 | TBD | TBD% | |
| OKR Queries (61-65) | 5 | TBD | TBD% | |
| Ambiguous (66-75) | 10 | TBD | TBD% | |
| Multi-Step (76-80) | 5 | TBD | TBD% | |
| Edge Cases (81-90) | 10 | TBD | TBD% | |
| **TOTAL** | **90** | **TBD** | **TBD%** | |

---

## Category 1: Risk & Escalation (Expected: get_at_risk_projects_report)

### Query #1: "What's at risk?"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** `get_at_risk_projects_report`
- **Match:** ✅
- **Response Quality:** `High`
- **Notes:** `Doesn't consider yellow projects at risk. Should it by default, or should it prompt user if they want to see yellow projects?  "Next Steps: Review Path to Green plans, escalate Tier 1 projects, and check dependencies." at end of the response is not useful`

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** `get_at_risk_projects_report`
- **Match:** ✅
- **Response Quality:** `High`
- **Notes:** `"Next Steps: Review Path to Green plans, escalate Tier 1 projects, and check dependencies." at end of response is not useful`

---

### Query #3: "What needs attention"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** `get_at_risk_projects_report`
- **Match:** ✅
- **Response Quality:** `High`
- **Notes:** `"Next Steps: Review Path to Green plans, escalate Tier 1 projects, and check dependencies." at end of response is not useful`

---

### Query #4: "Give me an escalation report"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** `get_at_risk_projects_report`
- **Match:** ✅
- **Response Quality:** `High`
- **Notes:** `"Next Steps: Review Path to Green plans, escalate Tier 1 projects, and check dependencies." at end of response is not useful`

---

### Query #5: "What should I be worried about?"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #6: "Show me blocked projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #7: "What's at risk in ProdDev?"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---

### Query #2: "Show me red projects"
- **Expected Tool:** `get_at_risk_projects_report`
- **Actual Tool(s):** 
- **Match:** ✅ / ❌
- **Response Quality:** 
- **Notes:** 

---



[Continue for all 90 queries...]

---

## Patterns & Insights

### What Worked Well:
- 

### What Didn't Work:
- 

### Surprising Behaviors:
- 

### Recommendations:
-