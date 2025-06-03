Vapor
-------

Doing stuff with Steam. Don't know what yet.

## Getting Started

### Requirements
- Python >= 3.9
- Pip

### Installation
Install the package for development with:
```bash
pip install -e .[dev]
```

### Environment Variables
You'll need to obtain certain API keys and set the following environment variables:

#### Steam WebAPI Key
Acquire a Steam WebAPI Key [here](https://steamcommunity.com/dev) (use `localhost` for the domain name) and set the following environment variable:
```bash
export STEAM_API_KEY="<your api key>"
```
Also, get your Steam ID (the actual ID number, not your username) and set this:
```bash
export STEAM_ID="<your steam id>"
```

