# Support

Before I investigate a report, I ask the reporter to read
[my Unraid guide](docs/UNRAID.md), search existing issues, and inspect the
container logs.

I use [GitHub Issues](https://github.com/2CrAzYTV/multi-coin-paper-daytrader/issues)
for reproducible bugs and concrete improvements. I do not provide investment,
financial, legal, or tax advice.

I ask reporters never to attach a `.env`, API key, registry token, or complete
database. I normally need only sanitised output from:

```bash
docker inspect paper-trading-bot \
  --format 'Image={{.Config.Image}} Status={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker logs --tail=100 paper-trading-bot
```

I ask the reporter to remove secrets and personal data before posting the
output. I handle security reports only through [SECURITY.md](SECURITY.md).
