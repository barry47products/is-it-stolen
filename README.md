# Is It Stolen?

A WhatsApp Business API service that allows users to report stolen items and check if items are stolen. This service helps with theft recovery and prevention by creating a community-driven database of stolen goods.

## Features

- **Report Stolen Items**: Users can report stolen items via WhatsApp with details and photos
- **Check Item Status**: Check if an item might be stolen before purchasing
- **Real-time Alerts**: Get notified when someone checks an item matching your stolen report
- **Recovery Tracking**: Mark items as recovered when found
- **Multi-language Support**: Available in multiple languages
- **GDPR Compliant**: Full data protection and privacy controls

## How It Works

1. **Report**: Users send details of stolen items via WhatsApp
2. **Database**: Items are stored in a searchable database
3. **Check**: Potential buyers can check if items are stolen
4. **Alert**: Original owners get notified of potential matches
5. **Recovery**: Items can be marked as recovered

## Cost Estimate

Based on WhatsApp Business API pricing (UK rates):

- **500 theft reports** × £0.0159 = £7.95
- **2,000 item checks** × £0.0159 = £31.80
- **100 alerts** × £0.0318 = £3.18
- **Total**: ~£43/month for 2,600 conversations

*First 1,000 service conversations per month are FREE*

## Setup Requirements

### Prerequisites

1. Facebook Business Manager account
2. WhatsApp Business Account (verified)
3. Dedicated phone number (not previously used with WhatsApp)
4. Business verification documents

### Implementation Options

#### Option 1: WhatsApp Cloud API (Recommended)
- Hosted by Meta
- Free tier: 1,000 conversations/month
- Quick setup
- No infrastructure needed

#### Option 2: WhatsApp Business API (On-Premise)
- Full control over infrastructure
- Data stays on your servers
- Better for high volume
- Requires Docker/Kubernetes setup

## Message Templates

The service uses approved WhatsApp message templates for:

- Welcome messages
- Theft match alerts
- Recovery confirmations
- Status updates

Templates must be submitted to Meta for approval (24-48 hours).

## Documentation

Comprehensive setup documentation is available in [`docs/whatsapp-business-setup.md`](docs/whatsapp-business-setup.md), including:

- Complete WhatsApp Business API setup guide
- Pricing breakdown by country
- Template examples
- Testing procedures
- Deployment options
- Compliance requirements
- Troubleshooting guide

## Getting Started

1. **Business Setup**
   - Create Facebook Business Manager account
   - Apply for WhatsApp Business Account
   - Get verification documents ready

2. **Technical Setup**
   - Deploy webhook endpoint
   - Configure WhatsApp API credentials
   - Set up database for storing reports

3. **Go Live**
   - Create and submit message templates
   - Test with team members
   - Launch to users

## Legal Considerations

- Users must confirm all reports are truthful
- False reports may result in legal action
- Data is shared with law enforcement when required
- GDPR compliant with data deletion options
- 12-month data retention policy

## Support

For technical support and questions:
- Check the [troubleshooting guide](docs/whatsapp-business-setup.md#troubleshooting)
- WhatsApp Business Support: business.whatsapp.com/contact
- Developer Support: developers.facebook.com/support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Important**: This service uses the official WhatsApp Business API, ensuring 100% compliance with WhatsApp's terms of service and providing enterprise-grade reliability and scale.