# GitHub publication

Requested visibility: **public**. Intended name: `social-growth-agent`. Account owner was not supplied and no connected GitHub capability was confirmed during preparation. Do not invent a hosted repository URL.

The local source distribution excludes original attachments, raw third-party captures, SQLite databases, caches, secrets and Git history. Review `docs/delivery.md` before publishing: this is a planning package and demo, not a complete production implementation.

## Publish when GitHub CLI is available and authenticated

From the repository root:

```powershell
gh auth status
gh repo create social-growth-agent --public --source . --remote origin --push
```

If publishing under an organization, use its explicit owner/name and confirm write access. If a remote already exists, inspect it rather than replacing it. Do not paste tokens into chat or source files. A connected GitHub integration can also publish through its supported workflow once its account is confirmed.

## Project organization

Use milestones P0–P10. Feature issues retain original IDs; labels include phase, family, planned, provider-blocked, demo-only and verified-sandbox. A project board uses Backlog → Spec ready → Building → Verification → Done, with blocked as a flag. Run `python scripts/export_issues.py` to generate a reviewable JSON issue backlog locally; it does not send anything to GitHub. Import only after review to avoid creating 257 noisy issues prematurely.

CI runs backend tests, catalogue validation and JS syntax. It cannot certify provider integrations that do not exist. Add production checks as modules ship. Branch protection should require these checks and review before merging. Choose licensing explicitly; a public repository alone is not an open-source license.
