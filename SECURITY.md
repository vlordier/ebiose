# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Ebiose, please **do not** open a public GitHub issue. Instead, please report it responsibly to the maintainers.

### How to Report

1. **Email**: Contact the maintainers at security@ebiose.com with:
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Suggested fix (if available)

2. **GitHub Security Advisory**: Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)

### What to Expect

- We will acknowledge receipt within 48 hours
- We will work with you to understand and fix the issue
- We will credit you in the security advisory (unless you prefer anonymity)
- We will not publicly disclose the vulnerability until a fix is available

## Security Best Practices

### When Using Ebiose

1. **API Keys**: Never commit API keys to version control
   - Use `.env` files (gitignored)
   - Use environment variables
   - Use secure key management systems

2. **Code Execution**: Be cautious with the CodeNode
   - It executes Python code in a restricted sandbox
   - Only execute trusted code
   - Review the [security test](tests/test_code_node_security.py) for sandbox limitations

3. **Agent Prompts**: Sanitize user input used in agent prompts
   - Avoid prompt injection vulnerabilities
   - Validate and escape user-provided data

4. **Cloud Mode**: When using Ebiose Cloud
   - Keep authentication tokens secure
   - Use HTTPS for all communications
   - Rotate API keys regularly

### Contributing Secure Code

1. **Type Safety**: Use full type hints for better type checking
   - Run `make type-check` before submitting PRs
   - Enable strict mypy checking

2. **Code Review**: All contributions go through review
   - Security-sensitive changes receive extra scrutiny
   - Follow the [CONTRIBUTING.md](CONTRIBUTING.md) guidelines

3. **Dependencies**: Keep dependencies up to date
   - Dependabot automatically checks for updates
   - Review security advisories for dependencies

4. **Testing**: Write tests for security-critical code
   - Include edge cases and error conditions
   - Test both happy path and failure modes

## Security Features

- **Type Checking**: Strict mypy configuration prevents type-related bugs
- **Code Linting**: Ruff enforces code quality and catches common issues
- **Sandbox Execution**: CodeNode runs user code in a restricted environment
- **Input Validation**: Pydantic models validate all inputs
- **Dependency Scanning**: Dependabot monitors for vulnerable dependencies

## Supported Versions

Security updates are provided for:
- Current development version (main branch)
- Latest release

Please upgrade to the latest version to receive security updates.

## Security Advisories

We will publish security advisories for:
- Critical vulnerabilities in Ebiose
- Critical vulnerabilities in directly-used dependencies
- Breaking changes related to security

See [Security Advisories](https://github.com/ebiose-ai/ebiose/security/advisories) for past disclosures.

## Contact

- **Security Concerns**: security@ebiose.com
- **General Support**: support@ebiose.com
- **GitHub Issues**: Only for non-security bugs and feature requests
