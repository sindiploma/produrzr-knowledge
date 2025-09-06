# Produzr Knowledge Base

This repository contains the knowledge base for Produzr, automatically synced from Notion with preserved hierarchical structure.

## Hierarchical Structure

The repository mirrors the exact structure from our Notion workspace:

```
produzr/                    # Main Produzr workspace
├── README.md              # Root page content
├── overview.md            # Platform overview
├── brand.md               # Brand guidelines
├── positioning.md         # Market positioning
├── business-model.md      # Business model details
├── articles/              # Knowledge articles section
│   ├── README.md          # Articles index
│   └── how-to-find-the-perfect-name.md
├── market/                # Market research section
│   ├── README.md          # Market overview
│   ├── macro.md           # Macro trends
│   ├── asociaciones.md    # Industry associations
│   ├── other-apps/        # Competitor analysis
│   │   ├── README.md      # Database index
│   │   ├── sana.md        # Individual competitor
│   │   ├── filmo.md       # Individual competitor
│   │   └── ...
│   └── productoras/       # Production company database
│       └── README.md
├── dudas--preguntas/      # Q&A database
│   ├── README.md          # Q&A index
│   └── untitled-database/ # Q&A entries
│       ├── README.md      # Database index
│       └── [individual Q&A entries].md
├── benchmark/             # Competitive analysis
│   ├── README.md
│   ├── feature_comparison_csv/
│   └── untitled-database/
└── tasks/                 # Task management
    ├── README.md
    └── untitled-database/
```

## Key Features

- **Preserves Notion hierarchy**: Pages with sub-pages become directories with README.md files
- **Database structure**: Notion databases become directories with individual entry files
- **Automatic cleanup**: Removes old flat structure when syncing
- **Consistent naming**: Safe filenames generated from Notion page titles

## Sync Process

### Manual Sync

```bash
# Run sync (reads token from .env automatically)
python3 sync_notion.py

# Still works with command line argument
python3 sync_notion.py YOUR_NOTION_TOKEN
```

## Content Types

- **Individual pages** → `.md` files with page content
- **Pages with children** → directories with `README.md` + child files/folders
- **Notion databases** → directories with:
  - `README.md` - Database index with entry list
  - Individual `.md` files for each database entry

## Navigation

The hierarchical structure makes it easy to:

- Browse content following the same mental model as Notion
- Find related content in the same directory
- Understand parent-child relationships
- Access database entries within their context

All content is automatically converted from Notion's block format to clean markdown with proper headings, lists, links, and formatting preserved.
