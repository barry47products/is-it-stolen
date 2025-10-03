# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email `security@example.com` (or create a private security advisory on GitHub) instead of opening a public issue.

## Secure Configuration

### Environment Variables

**NEVER commit `.env` files with real credentials to the repository.**

The repository includes:

- `.env.example` - Template with placeholder values (safe to commit)
- `.env.test` - Test environment with dummy credentials (safe to commit)
- `.env` - **YOUR local file** with real credentials (**NEVER commit!**)

### Database Security

#### Local Development

The `docker-compose.yml` includes default credentials for **local development only**:

- Username: `isitstolen_user`
- Password: `local_dev_password_only`

These are intentionally weak and clearly marked as development-only.

#### Production Deployment

**REQUIRED ACTIONS** before deploying to production:

1. **Change all default passwords immediately**
2. **Use strong, randomly generated passwords** (minimum 32 characters)
3. **Store credentials in secure secret management**:

   - AWS: Use AWS Secrets Manager or Parameter Store
   - Azure: Use Azure Key Vault
   - GCP: Use Secret Manager
   - Self-hosted: Use Vault by HashiCorp

4. **Use environment-specific configuration**:

   ```bash
   # Production
   export DATABASE_URL="postgresql://prod_user:$(cat /run/secrets/db_password)@db-host:5432/isitstolen"
   ```

5. **Enable SSL/TLS for database connections**:

   ```bash
   DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
   ```

6. **Restrict network access**:
   - Use VPC/private networks
   - Implement IP allowlisting
   - Use security groups/firewall rules

### WhatsApp API Credentials

WhatsApp credentials in `.env.test` are placeholders only. For production:

1. **Obtain real credentials** from [Meta for Developers](https://developers.facebook.com/apps)
2. **Store in secret management** (never in code or `.env` files)
3. **Rotate tokens regularly** (every 90 days recommended)
4. **Use webhook verify tokens** with high entropy (32+ characters)

### Security Checklist for Production

- [ ] Changed all default passwords
- [ ] Using secret management (AWS Secrets Manager, etc.)
- [ ] Database connections use SSL/TLS
- [ ] Network access restricted via firewall/security groups
- [ ] Environment variables set via secure deployment pipeline
- [ ] `.env` files excluded from version control
- [ ] API tokens rotated regularly
- [ ] Monitoring and alerting configured
- [ ] Regular security audits scheduled

## Development Best Practices

### Do ✅

- Use `.env.example` as a template
- Store real credentials in `.env` (which is gitignored)
- Use dummy/test credentials in test files
- Document required environment variables
- Use type-safe configuration (Pydantic Settings)

### Don't ❌

- Commit `.env` files with real credentials
- Hardcode passwords in source code
- Use default/weak passwords in production
- Share credentials via Slack/email/chat
- Commit API keys or access tokens

## Additional Resources

- [OWASP Configuration Security](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [12-Factor App: Config](https://12factor.net/config)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
