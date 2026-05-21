# Contribution Guide — SmartApply

## Branching Strategy (Git Flow)

| Branch | Purpose |
|---|---|
| `main` | Production — always stable, deployable |
| `develop` | Integration — features merge here before `main` |
| `microservices` | Current active branch — microservices migration |
| `feature/feature-name` | One branch per task/feature |

**Workflow:**
1. Start from `develop` (or `microservices` during current phase)
2. `git checkout -b feature/my-feature`
3. Commit your changes
4. Open PR targeting `develop`

---

## Commit Messages (Conventional Commits)

Format: `<type>(<scope>): <short description>`

**Types:**

| Type | Use for |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code cleanup, no behavior change |
| `chore` | Build, deps, config |
| `style` | Formatting (no logic change) |

**Scopes** (match microservice names):

| Scope | Service |
|---|---|
| `auth` | SmartApplyAuth |
| `pipeline` | SmartApplyPipeline |
| `jobs` | SmartApplyJobs |
| `gmail` | SmartApplyGmail |
| `rag` | SmartApplyRag |
| `gateway` | nginx config |
| `front` | Angular frontend |
| `docker` | docker-compose, Dockerfiles |

Examples:
```
feat(pipeline): add hunter.io domain discovery
fix(gmail): handle expired access token on sync
chore(docker): increase rag memory limit to 512M
docs(rag): document inbox ingestion flow
```

---

## Development Standards

### Naming Conventions
- **Python**: `snake_case` for functions/variables, `PascalCase` for classes
- **TypeScript**: `camelCase` for variables/properties, `PascalCase` for components/services
- **No `any` in TypeScript**
- Code and comments in **English**

### Adding a New Service

1. Create `src/SmartApplyNewService/` mirroring the structure above
2. Add to `docker-compose.yml` with healthcheck and memory limit
3. Add nginx route in `nginx/nginx.conf`
4. Add `.env.example` with required variables
5. Call `create_indexes()` at startup
6. Re-use `app/services/auth/dependency.py` for JWT auth (copy from existing service)

### Security
- Never commit `.env` files, `token.json`, `cv.pdf`
- Never expose API keys in the frontend
- All new env vars must be added to the `.env.example` of the relevant service
- Protected routes must use `Depends(get_current_user)`

### SSE Pattern

Pipeline endpoints stream events. Follow this pattern:

```python
@router.get("/stream")
def my_stream(current_user: User = Depends(get_current_user)):
    def generate():
        for event in my_generator(...):
            yield sse_event(event)
    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)
```

Events must end with `{"type": "done"}`.

---

## Pull Requests

1. **Title**: explicit (`feat(jobs): add LinkedIn RSS source`)
2. **Description**: what changed, how tested, which services affected
3. **Testing**: run `pytest` in the relevant service before opening PR
4. **Cleanup**: delete branch after merge

---

