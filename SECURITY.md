# Security Policy

## Reporting Security Vulnerabilities

Audio Pollinations takes security seriously. If you discover a security vulnerability in this project, please **do not** create a public GitHub issue. Instead, please follow these steps:

1. **Email the maintainers** at your earliest convenience with details of the vulnerability
2. **Include the following information:**
   - Type of vulnerability (e.g., code injection, authentication bypass, DoS, etc.)
   - Location of the vulnerability in the codebase
   - Detailed steps to reproduce the issue
   - Potential impact and severity
   - Any suggested fixes (if available)

3. **Allow reasonable time** for the maintainers to investigate and patch the vulnerability before public disclosure

## Security Best Practices

### For Users

When deploying Audio Pollinations, please follow these security best practices:

#### 1. Environment Variables
- **Never commit `.env` files to version control**
- Store sensitive credentials (API tokens, keys) in environment variables
- Use `.env.example` as a template without sensitive data
- Rotate API tokens regularly

#### 2. Docker Deployment
- Use the official NVIDIA CUDA base image (`nvidia/cuda:12.4.0-runtime-ubuntu22.04`)
- Keep Docker images updated
- Run containers with minimal privileges
- Isolate GPU access using `CUDA_VISIBLE_DEVICES`
- Use resource limits in `docker-compose.yml`

#### 3. API Security
- Run behind a reverse proxy (nginx, Traefik)
- Enable HTTPS/TLS for all communications
- Implement rate limiting to prevent abuse
- Use authentication/authorization for API endpoints
- Validate and sanitize all user inputs
- Add CORS configuration as needed

#### 4. Model Security
- Models are downloaded from trusted sources (OpenAI Whisper, Hugging Face)
- Verify model checksums when possible
- Keep models in `/app/model_cache` with restricted permissions
- Monitor for model updates and security patches

#### 5. Audio Data Handling
- Audio files are processed in isolated temporary directories (`/tmp/higgs/`)
- Sensitive audio data should not be stored longer than necessary
- Implement data retention policies
- Encrypt audio data in transit (HTTPS/TLS)
- Consider GDPR/CCPA compliance for user audio data

### For Developers

#### 1. Dependencies
- **Frozen versions:** All Python dependencies are pinned to specific versions in `requirements.txt`
- **Regular updates:** Monitor for security updates in dependencies
- **Use `pip-audit`** to check for known vulnerabilities:
  ```bash
  pip install pip-audit
  pip-audit
  ```
- **Review dependencies:** Regularly review `requirements.txt` for unnecessary packages

#### 2. Code Review
- All contributions must go through code review
- Security-sensitive changes require additional scrutiny
- Use static analysis tools (e.g., `ruff`, `pylint`)
- Test all input validation thoroughly

#### 3. CUDA/GPU Security
- GPU memory is not isolated between processes
- Sensitive data in GPU memory may be accessible to other processes
- Use `CUDA_VISIBLE_DEVICES` to restrict GPU access
- Clear GPU memory after inference: `torch.cuda.empty_cache()`

#### 4. Logging
- Never log sensitive information (API keys, audio data, PII)
- Use `loguru` with appropriate log levels
- Implement log rotation to prevent disk space issues
- Sanitize logs before sharing

#### 5. Input Validation
- Validate all user inputs (text, audio files, API payloads)
- Enforce file size limits:
  - Audio input: Maximum 1.5 minutes (90 seconds)
  - Voice cloning: 5-8 seconds
  - Text: No hard limit (reasonable length enforced by token limits)
- Validate MIME types and file formats
- Reject malformed requests

### 3. Known Limitations

#### GPU Memory
- Models are loaded once per process to reduce memory duplication
- Running multiple concurrent operations may exceed GPU VRAM
- Implement queue-based processing for high concurrency
- Monitor GPU memory with `nvidia-smi`

#### Model Inference
- Faster-Whisper is used for transcription (99 language support)
- ChatterboxTurboTTS is used for speech synthesis
- Neither model is guaranteed to be 100% accurate
- Test with your specific use cases before production

#### Concurrency
- Flask app runs with 30 workers, model server runs 1 worker
- Configure based on GPU VRAM and expected load
- Monitor thread pool executor for queue bottlenecks

### 4. Data Privacy

- **No data is sent externally** (except API calls to configured endpoints like Pollinations)
- Audio data is processed locally on your infrastructure
- Generated audio is stored in `/app/genAudio` (configure retention)
- Temporary files in `/tmp/higgs/` should be cleaned up regularly

### 5. HTTPS/TLS Configuration

For production deployments, configure TLS termination at your reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Checklist for Deployment

- [ ] Environment variables are not in version control (`.env` in `.gitignore`)
- [ ] Docker image is built from official base images
- [ ] API is behind a reverse proxy with HTTPS/TLS
- [ ] Rate limiting is configured
- [ ] Authentication/authorization is enforced
- [ ] Input validation is implemented
- [ ] Logging does not contain sensitive information
- [ ] GPU access is restricted with `CUDA_VISIBLE_DEVICES`
- [ ] Resource limits are set in docker-compose
- [ ] Regular backups of generated audio are in place
- [ ] Data retention policy is documented
- [ ] Security updates are monitored and applied

## Dependencies Security

### Key Dependencies

- **torch**: Deep learning framework (PyTorch)
- **faster-whisper**: Speech-to-text transcription
- **chatterbox-tts**: Text-to-speech synthesis
- **flask**: Web framework
- **gunicorn**: WSGI HTTP server
- **numpy/scipy**: Scientific computing

All versions are frozen in `requirements.txt` to ensure reproducible, auditable builds.

### Monitoring

Subscribe to security advisories:
- [PyPI Security Advisories](https://pypi.org/)
- [GitHub Security Alerts](https://docs.github.com/en/code-security)
- Project-specific notifications

## Incident Response

If a security issue is discovered:

1. **Assessment:** Determine severity and scope
2. **Containment:** Implement immediate fixes if available
3. **Notification:** Alert users of the vulnerability and recommended actions
4. **Release:** Publish security patches promptly
5. **Post-mortem:** Document lessons learned

## Version Support

- **Latest version**: Fully supported with security updates
- **Previous versions**: Critical security updates only
- **Older versions**: No support; users encouraged to upgrade

## License

This security policy is part of the Audio Pollinations project, released under the GNU General Public License v3.0 (GPL-3.0).

---

**Last Updated:** February 4, 2026  
**Maintainer:** Elixpo Team  
**Questions?** Please reach out to the maintainers via secure channels.
