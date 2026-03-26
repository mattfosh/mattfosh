# CLAUDE.md

## Repository Overview

This is a **GitHub profile repository** (`mattfosh/mattfosh`). Its sole purpose is to display a profile README on the [mattfosh GitHub profile page](https://github.com/mattfosh). The `README.md` file in the root is rendered automatically by GitHub as the profile landing page.

## Repository Structure

```
.
└── README.md    # GitHub profile README (the only content file)
```

There are no source code files, build systems, tests, CI/CD pipelines, or dependencies. This is a content-only repository.

## Key File

- **README.md** - GitHub-flavored Markdown profile page containing:
  - About Me section (interests: OKM, Backstage TechDocs, Notion, Zero Trust SASE)
  - Tech Stack badges (Python, PowerShell, Nim, AWS, Azure, Cloudflare, Docker, Kubernetes, Terraform, Ansible, and more)
  - GitHub Stats widgets (stats, streak, top languages)
  - Random Dev Quote widget
  - Visit counter

## Tech Stack (owner's skills, not repo dependencies)

The profile highlights expertise in:
- **Languages**: Python, PowerShell, Nim, Markdown
- **Cloud**: AWS, Azure, Cloudflare
- **Infrastructure**: Docker, Kubernetes, Terraform, Ansible
- **Databases**: MySQL, MS SQL Server, Redis
- **Observability**: Grafana, Prometheus, ElasticSearch, SonarQube
- **Tools**: GitHub Actions, Bitbucket, Jira, Confluence, Notion, Postman

## Development Conventions

- **Branch strategy**: `main` is the default branch on GitHub
- **Commit style**: Short descriptive messages (e.g., "Enhance README with personal and tech stack details")
- **Formatting**: The README uses GitHub-flavored Markdown with shield.io badges and external widget embeds

## Guidelines for AI Assistants

1. **Do not break badge formatting** - The tech stack section uses inline shield.io badge images. Preserve the exact badge URL format when editing.
2. **Do not remove external widgets** - Stats cards and quote widgets are intentional profile features.
3. **Preserve the HTML comment block** - The commented-out template near the top is standard for profile repos.
4. **Keep it concise** - This is a profile page, not documentation. Changes should be brief and visually appealing.
5. **Test Markdown rendering** - Since this renders on GitHub's profile page, ensure any changes are valid GitHub-flavored Markdown.
