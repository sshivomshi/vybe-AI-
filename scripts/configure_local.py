"""Create a private local configuration without printing credentials."""
from pathlib import Path
import secrets

path=Path('.env')
if not path.exists():
    path.write_text(Path('.env.example').read_text().replace('replace-with-a-long-random-token',secrets.token_urlsafe(48)))
    print('Created .env with a random sync token. This file is gitignored.')
else:
    print('Keeping existing .env.')
