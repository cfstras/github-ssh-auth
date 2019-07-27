# github-ssh-auth

Automatically provision SSH authorized_keys to your user by scraping a GitHub organisation (optional team).

## Setup
- If you're on Debian, you will need some more packages:
```bash
apt install python3
```

- Enable lingering services for your user:
```bash
sudo loginctl enable-linger $USER
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
