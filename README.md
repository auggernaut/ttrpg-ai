# TTRPG Games Content Generator

Scripts and tools for generating content for [TTRPG Games](https://ttrpg-games.com), the world's best directory of tabletop roleplaying games.

## Overview

This repository contains the content generation scripts and utilities used to create and maintain resources for [ttrpg-games.com](https://ttrpg-games.com). These tools help automate the creation of game descriptions, categories, related games blurbs, and other TTRPG resources.

## Features

- Type a name of a game, it will generate a description, a list of related games, descriptions about why the games are related, which predefined categories it fits into, and a list of possible categories to add to the game.
- Updates game if it already exists in the database
- Option to update all game rows
- Option to update only a single column

## Getting Started

### Prerequisites

- Python 3.8+
- Additional dependencies listed in `requirements.txt`
- Run using local python virtual environment

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ttrpg-ai.git
cd ttrpg-ai
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your OpenAI API key:

```bash
OPENAI_API_KEY=<your-openai-api-key>
```

4. You'll need to set up a Google Cloud account and create a service account with the necessary permissions to access the Google Sheets API. Update `config/constants.py` with your service account key.

5. Export the python path to the project:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/ttrpg-ai"
```

## Usage

```bash
python main.py -h
```


## Related Links

- Main Website: [TTRPG Games](https://ttrpg-games.com)

## Contact

- X/Twitter: [@augustinbralley](https://x.com/augustinbralley)
