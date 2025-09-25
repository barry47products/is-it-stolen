# WhatsApp Business API - Complete Setup Guide

## Why Official API? The Game Changer

### ✅ **Advantages**

- **100% Legitimate**: No risk of bans or violations
- **Enterprise Scale**: Handle millions of messages
- **Rich Features**: Interactive buttons, lists, media, templates
- **Business Verification**: Builds trust with users
- **Analytics**: Detailed insights and metrics
- **Support**: Direct support from Meta
- **Global Reach**: Works in all countries where WhatsApp operates

### ❌ **Considerations**

- **Cost**: Pay per conversation (varies by country)
- **Approval Process**: Takes 2-5 days for business verification
- **Template Reviews**: Message templates need approval (24-48 hours)
- **Phone Number**: Need dedicated number not used with WhatsApp before

## Setup Requirements

### 1. **Meta Business Prerequisites**

#### Step 1: Facebook Business Manager

```text
1. Go to business.facebook.com
2. Create Business Manager account
3. Verify your business (requires documents)
4. Add team members with appropriate roles
```

#### Step 2: WhatsApp Business Account

```text
1. In Business Manager → WhatsApp Accounts
2. Create new WhatsApp Business Account
3. Add display name, category, description
4. Upload business verification documents:
   - Business registration certificate
   - Utility bill or bank statement
   - Tax identification number
```

#### Step 3: Phone Number Setup

```text
Requirements:
- Not previously used with WhatsApp
- Can receive SMS/voice for verification
- Supports your target country codes
- Consider getting a Twilio number
```

## Implementation Options

### Option 1: WhatsApp Cloud API (Recommended for Start)

**Pros:**

- Hosted by Meta (no infrastructure needed)
- Free tier: 1,000 conversations/month
- Quick setup (minutes)
- Automatic updates

**Setup:**

```javascript
// Simple - Just API calls to Meta's servers
const CLOUD_API_URL = "https://graph.facebook.com/v18.0";
const ACCESS_TOKEN = "your-permanent-token";
```

### Option 2: WhatsApp Business API (On-Premise)

**Pros:**

- Full control over infrastructure
- Data stays on your servers
- Custom integrations
- Better for high volume

**Requirements:**

- Docker/Kubernetes cluster
- MySQL/PostgreSQL database
- Redis for caching
- Load balancers

## Pricing Structure (2024)

### Conversation Categories

| Type               | Description                 | Cost (UK) | Cost (US) | Cost (India) |
| ------------------ | --------------------------- | --------- | --------- | ------------ |
| **Utility**        | Transaction updates, alerts | £0.0318   | $0.0058   | ₹0.25        |
| **Authentication** | OTPs, login                 | £0.0265   | $0.0047   | ₹0.20        |
| **Marketing**      | Promotions, offers          | £0.0583   | $0.0124   | ₹0.65        |
| **Service**        | User-initiated support      | £0.0159   | $0.0028   | ₹0.10        |

**Free Tier**: First 1,000 service conversations per month FREE

### Cost Example for "Is It Stolen?"

```text
Monthly Usage Estimate:
- 500 theft reports × £0.0159 = £7.95
- 2000 item checks × £0.0159 = £31.80
- 100 alerts × £0.0318 = £3.18
Total: ~£43/month for 2,600 conversations
```

## Quick Start Guide

### Step 1: Get Access Token

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create App → Business → WhatsApp
3. Add WhatsApp product
4. Get temporary access token
5. Generate permanent token:

```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id=YOUR_APP_ID&
  client_secret=YOUR_APP_SECRET&
  fb_exchange_token=YOUR_TEMPORARY_TOKEN"
```

### Step 2: Configure Webhook

```javascript
// Your webhook endpoint
app.post("/webhook", (req, res) => {
  // Verify webhook (one-time)
  if (req.query["hub.verify_token"] === "your-verify-token") {
    return res.send(req.query["hub.challenge"]);
  }

  // Handle messages
  const { entry } = req.body;
  // Process incoming messages
  res.sendStatus(200);
});
```

### Step 3: Set Webhook URL

```bash
curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/webhook" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "callback_url": "https://your-domain.com/webhook",
    "fields": "messages,message_status",
    "verify_token": "your-verify-token"
  }'
```

## Message Templates Setup

### Required Templates for Is It Stolen

#### 1. Welcome Message

```yaml
Name: welcome_stolen_check
Category: UTILITY
Languages: en_GB, en_US
Body: |
  Welcome to Is It Stolen, {{1}}! 

  Report stolen items or check if something is stolen.
  Your Report ID: {{2}}

  Reply MENU for options.
```

#### 2. Match Alert

```yaml
Name: match_alert_notification
Category: UTILITY
Languages: en_GB, en_US
Body: |
  🚨 ALERT: Someone checked an item matching your stolen report!

  Report ID: {{1}}
  Item checked: {{2}}
  Time: {{3}}

  This could be a lead for recovery. Contact local police.
```

#### 3. Recovery Confirmation

```yaml
Name: item_recovered
Category: UTILITY
Languages: en_GB, en_US
Body: |
  ✅ Great news! Your item ({{1}}) has been marked as recovered.

  Thank you for using Is It Stolen.
```

### Submit Templates for Approval

1. Go to Business Manager → WhatsApp → Message Templates
2. Create new template
3. Fill in details and variables
4. Submit for review
5. Wait 24-48 hours for approval

## Testing Your Integration

### Test Mode Setup

```javascript
// Use test numbers before going live
const TEST_NUMBERS = [
  "+1 555 093 3679", // US test number
  "+44 7700 900123", // UK test number
];

// Test without sending real messages
const testMode = process.env.NODE_ENV === "development";
```

### Testing Checklist

- [ ] Webhook receives messages
- [ ] Can send text messages
- [ ] Interactive buttons work
- [ ] Lists display correctly
- [ ] Media uploads/downloads work
- [ ] Templates send successfully
- [ ] Rate limiting works
- [ ] Error handling tested

## Best Practices

### 1. **Message Windows**

- **24-hour window**: After user messages, you can reply freely for 24 hours
- **After 24 hours**: Must use approved templates
- **Keep conversations going**: Send engaging content to maintain window

### 2. **Template Strategy**

```javascript
// Check if within 24-hour window
const isWithin24Hours = (lastMessageTime) => {
  const hoursSince = (Date.now() - lastMessageTime) / 3600000;
  return hoursSince < 24;
};

// Use appropriate method
if (isWithin24Hours(session.lastMessage)) {
  await sendRegularMessage(phone, text);
} else {
  await sendTemplate(phone, "reminder_template");
}
```

### 3. **Quality Rating**

- Monitor your quality rating in Business Manager
- Low quality = higher costs + limits
- Maintain quality by:
  - Not spamming
  - Honouring opt-outs
  - Relevant messaging only
  - Quick response times

### 4. **Opt-in Management**

```javascript
// Store user preferences
const userPreferences = {
  phone: "+447700900123",
  optedIn: true,
  categories: ["theft_alerts", "recovery_updates"],
  quietHours: { start: 22, end: 8 },
  language: "en_GB",
};

// Check before sending
async function canSendMessage(phone, messageType) {
  const user = await getUserPreferences(phone);

  if (!user.optedIn) return false;
  if (!user.categories.includes(messageType)) return false;

  const hour = new Date().getHours();
  if (hour >= user.quietHours.start || hour < user.quietHours.end) {
    return false; // Respect quiet hours
  }

  return true;
}
```

## Deployment Options

### 1. **Heroku/Railway (Simple)**

```yaml
# app.json
{
  "name": "Is It Stolen Bot",
  "env":
    {
      "WHATSAPP_TOKEN": { "required": true },
      "WHATSAPP_PHONE_ID": { "required": true },
      "MONGODB_URI": { "required": true },
      "WEBHOOK_VERIFY_TOKEN": { "generator": "secret" },
    },
  "addons": ["mongolab:sandbox"],
}
```

### 2. **AWS/GCP (Scalable)**

```yaml
# docker-compose.yml
version: "3.8"
services:
  bot:
    build: .
    environment:
      - WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
      - DATABASE_URL=mongodb://mongo:27017/isitstolen
    depends_on:
      - mongo
      - redis

  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 3. **Kubernetes (Enterprise)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-bot
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: bot
          image: isitstolen:latest
          env:
            - name: WHATSAPP_TOKEN
              valueFrom:
                secretKeyRef:
                  name: whatsapp-secrets
                  key: token
```

## Monitoring & Analytics

### Key Metrics to Track

```javascript
const metrics = {
  // Message metrics
  messagesSent: 0,
  messagesReceived: 0,
  messagesFailed: 0,

  // Business metrics
  reportsCreated: 0,
  itemsChecked: 0,
  matchesFound: 0,
  itemsRecovered: 0,

  // User metrics
  activeUsers: new Set(),
  newUsers: 0,
  returningUsers: 0,

  // Performance
  avgResponseTime: 0,
  webhookLatency: 0,

  // Quality
  userBlocks: 0,
  reportedSpam: 0,
};

// Track in real-time
async function trackMetric(metric, value = 1) {
  metrics[metric] += value;

  // Send to analytics service
  await analytics.track({
    event: metric,
    value: value,
    timestamp: Date.now(),
  });
}
```

### WhatsApp Analytics Dashboard

```javascript
// Get insights from WhatsApp API
async function getAnalytics() {
  const response = await axios.get(
    `${META_API_URL}/${WHATSAPP_BUSINESS_ID}/analytics`,
    {
      params: {
        start: "2024-01-01",
        end: "2024-01-31",
        granularity: "daily",
        metrics: ["messages_sent", "messages_delivered", "cost"],
      },
      headers: {
        Authorization: `Bearer ${ACCESS_TOKEN}`,
      },
    }
  );

  return response.data;
}
```

## Compliance & Legal

### GDPR Compliance

```javascript
// Data deletion request handler
app.post("/privacy/delete", async (req, res) => {
  const { phone } = req.body;

  // Delete all user data
  await StolenItem.deleteMany({ reporterPhone: phone });
  await CheckHistory.deleteMany({ checkerPhone: phone });
  await UserAnalytics.deleteOne({ phone });

  // Notify WhatsApp
  await whatsapp.sendMessage(
    phone,
    "Your data has been completely removed from our system."
  );

  res.json({ success: true });
});
```

### Terms of Service Template

```text
By using Is It Stolen on WhatsApp:

1. You confirm all reports are truthful
2. False reports may result in legal action
3. We share data with law enforcement when required
4. You consent to receiving service messages
5. Data retained for 12 months per legal requirements

To opt-out: Send "STOP"
To delete data: Send "DELETE"
```

## Troubleshooting

### Common Issues

#### Webhook Not Receiving Messages

```bash
# Test webhook is accessible
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check webhook subscription
curl -G "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/webhook" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Template Message Rejected

- Check variable count matches
- Ensure no promotional content in utility templates
- Verify language codes
- Remove emojis if category doesn't allow

#### Rate Limiting Errors

```javascript
// Implement exponential backoff
async function sendWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.response?.status === 429) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw error;
      }
    }
  }
}
```

## Migration Path

### From Unofficial to Official API

1. **Phase 1**: Set up official API in parallel
2. **Phase 2**: Migrate new users to official API
3. **Phase 3**: Send migration notice to existing users
4. **Phase 4**: Bulk migrate remaining users
5. **Phase 5**: Deprecate old system

```javascript
// Migration script
async function migrateUsers() {
  const users = await OldSystem.getAllUsers();

  for (const user of users) {
    // Send migration notice via old system
    await oldWhatsApp.send(user.phone,
      'We're upgrading! Please save this new number: +44XXXXXXX'
    );

    // Wait for user to message new number
    // Then migrate their data
  }
}
```

## Support Resources

### Official Documentation

- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp)
- [Cloud API Reference](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)

### Community

- [WhatsApp Business API Community](https://www.facebook.com/groups/whatsapp.business.api)
- [Stack Overflow - whatsapp-business-api tag](https://stackoverflow.com/questions/tagged/whatsapp-business-api)

### Getting Help

- Business Support: business.whatsapp.com/contact
- Developer Support: developers.facebook.com/support
- Rate Limit Increases: Through Business Manager

---

## Next Steps

1. **Create Facebook Business account** (10 minutes)
2. **Apply for WhatsApp Business** (2-5 days for approval)
3. **Get phone number** (immediate with Twilio)
4. **Deploy webhook endpoint** (1 hour)
5. **Create message templates** (24-48 hours for approval)
6. **Test with team** (1-2 days)
7. **Launch!** 🚀

Remember: The official API is the only legitimate way to build a production WhatsApp bot. While it requires more setup, it provides reliability, scale, and compliance that unofficial methods cannot match.
