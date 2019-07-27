# github-ssh-auth

Automatically provision SSH authorized_keys to your user by scraping a GitHub organisation (optional team).

## Setup
- If you're on Debian, you will need some more packages:
```bash
sudo apt install python3
```
- Also, upgrade your system. An outdated libssl will cause pain.
```bash
sudo apt update && sudo apt upgrade
```

The following script will:

- Make a virtualenv and install dependencies from [requirements.txt](requirements.txt)
- Setup a systemd-user-service `github-ssh-auth.service`
- Setup a timer which refreshes authorized_keys every 30 minutes

```bash
./setup.sh
```

- Edit `config.yml`
  - Create an access token
  - Set your organization and team
  - optionally, add fallback ssh keys which will always be added

# License
GPLv3. Other licenses available upon request.
