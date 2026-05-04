# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | ✅ Active support |
| < 2.0   | ❌ Not supported |

We provide security updates for the latest minor version only. Please upgrade to stay protected.

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, **please do NOT open a public issue**.

### Reporting Process

1. **Email**: Send details to the security team at the email address listed in the repository's `.github/SECURITY.md` or open a [GitHub Security Advisory](https://github.com/KingdeGuo/paper-agent/security/advisories/new).

2. **Include**:
   - Type of vulnerability
   - Steps to reproduce
   - Affected versions
   - Potential impact
   - Suggested fix (if any)

3. **Response Timeline**:
   - **48 hours**: Initial acknowledgment
   - **7 days**: Assessment and mitigation plan
   - **14 days**: Fix released (depending on severity)

### What to Expect

- We will acknowledge receipt within 48 hours
- We will provide a timeline for the fix
- We will credit you in the release notes (if desired)
- We will notify you when the fix is deployed

## Security Best Practices for Deployments

### Production Checklist

- [ ] Change the default `PAPER_AGENT_SECRET_KEY` to a random value
- [ ] Use PostgreSQL with a strong password
- [ ] Enable Redis with password authentication
- [ ] Configure CORS origins to your domain only
- [ ] Use HTTPS with a valid TLS certificate
- [ ] Enable rate limiting (built-in for auth endpoints)
- [ ] Regularly update dependencies
- [ ] Monitor audit logs for suspicious activity

### Password Policy

- Minimum 8 characters
- Hashed with PBKDF2-SHA256 + random salt (600,000 iterations)
- JWT tokens expire after 24 hours

## Disclosure Policy

- We will disclose vulnerabilities after releasing a fix
- We will credit researchers who follow responsible disclosure
- We aim for coordinated disclosure whenever possible
