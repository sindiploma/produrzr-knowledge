#!/usr/bin/env python3
"""
Notion to Knowledge Base Sync Script

This script fetches content from Notion using the API and converts it to markdown
files for the knowledge base repository.
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, List, Any

class NotionSync:
    def __init__(self, notion_token: str):
        self.token = notion_token
        self.headers = {
            'Authorization': f'Bearer {notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.notion.com/v1'
        
    def search_pages(self) -> List[Dict]:
        """Search for all accessible pages and databases"""
        url = f'{self.base_url}/search'
        response = requests.post(url, headers=self.headers, json={})
        response.raise_for_status()
        return response.json()['results']
    
    def get_page_content(self, page_id: str) -> Dict:
        """Get blocks/content for a specific page"""
        url = f'{self.base_url}/blocks/{page_id}/children'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_database_entries(self, database_id: str) -> Dict:
        """Get entries from a database"""
        url = f'{self.base_url}/databases/{database_id}/query'
        response = requests.post(url, headers=self.headers, json={})
        response.raise_for_status()
        return response.json()
    
    def block_to_markdown(self, block: Dict) -> str:
        """Convert a Notion block to markdown"""
        block_type = block['type']
        
        if block_type == 'paragraph':
            text = self.rich_text_to_markdown(block['paragraph']['rich_text'])
            return f"{text}\n\n"
        
        elif block_type == 'heading_1':
            text = self.rich_text_to_markdown(block['heading_1']['rich_text'])
            return f"# {text}\n\n"
        
        elif block_type == 'heading_2':
            text = self.rich_text_to_markdown(block['heading_2']['rich_text'])
            return f"## {text}\n\n"
        
        elif block_type == 'heading_3':
            text = self.rich_text_to_markdown(block['heading_3']['rich_text'])
            return f"### {text}\n\n"
        
        elif block_type == 'bulleted_list_item':
            text = self.rich_text_to_markdown(block['bulleted_list_item']['rich_text'])
            return f"- {text}\n"
        
        elif block_type == 'numbered_list_item':
            text = self.rich_text_to_markdown(block['numbered_list_item']['rich_text'])
            return f"1. {text}\n"
        
        elif block_type == 'divider':
            return "---\n\n"
        
        elif block_type == 'code':
            text = self.rich_text_to_markdown(block['code']['rich_text'])
            language = block['code'].get('language', '')
            return f"```{language}\n{text}\n```\n\n"
        
        else:
            # For unsupported block types, just return the plain text if available
            if block_type in block and 'rich_text' in block[block_type]:
                text = self.rich_text_to_markdown(block[block_type]['rich_text'])
                return f"{text}\n\n"
            return ""
    
    def rich_text_to_markdown(self, rich_text: List[Dict]) -> str:
        """Convert Notion rich text to markdown"""
        if not rich_text:
            return ""
        
        result = ""
        for text_obj in rich_text:
            content = text_obj['plain_text']
            annotations = text_obj['annotations']
            
            if annotations['bold']:
                content = f"**{content}**"
            if annotations['italic']:
                content = f"*{content}*"
            if annotations['code']:
                content = f"`{content}`"
            if annotations['strikethrough']:
                content = f"~~{content}~~"
            
            if text_obj.get('href'):
                content = f"[{content}]({text_obj['href']})"
            
            result += content
        
        return result
    
    def sanitize_filename(self, title: str) -> str:
        """Convert page title to safe filename"""
        # Remove or replace invalid characters
        filename = title.lower()
        filename = filename.replace(' ', '-')
        filename = ''.join(c for c in filename if c.isalnum() or c in '-_')
        return filename[:50]  # Limit length
    
    def sync_page(self, page: Dict, output_dir: Path):
        """Sync a single page to markdown file"""
        page_id = page['id']
        
        # Get page title
        if page['object'] == 'page':
            title_prop = page['properties'].get('title', {}).get('title', [])
            if title_prop:
                title = title_prop[0]['plain_text']
            else:
                title = 'Untitled'
        else:
            title = 'Database'
        
        # Get page content
        try:
            content_data = self.get_page_content(page_id)
            blocks = content_data['results']
            
            # Convert blocks to markdown
            markdown_content = f"# {title}\n\n"
            for block in blocks:
                markdown_content += self.block_to_markdown(block)
            
            # Save to file
            filename = f"{self.sanitize_filename(title)}.md"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Synced: {title} -> {filename}")
            
        except Exception as e:
            print(f"Error syncing page {title}: {e}")
    
    def sync_database(self, database: Dict, output_dir: Path):
        """Sync a database to markdown files"""
        database_id = database['id']
        
        # Get database title
        title = database.get('title', [])
        if title:
            db_title = title[0]['plain_text']
        else:
            db_title = 'Untitled Database'
        
        try:
            # Create directory for database
            db_dir = output_dir / self.sanitize_filename(db_title)
            db_dir.mkdir(exist_ok=True)
            
            # Get database entries
            entries_data = self.get_database_entries(database_id)
            entries = entries_data['results']
            
            # Create index file
            index_content = f"# {db_title}\n\n"
            index_content += f"This database contains {len(entries)} entries.\n\n"
            index_content += "## Entries\n\n"
            
            for entry in entries:
                # Get entry title
                title_prop = entry['properties'].get('Name', {}).get('title', [])
                if title_prop:
                    entry_title = title_prop[0]['plain_text']
                else:
                    entry_title = f"Entry {entry['id'][:8]}"
                
                entry_filename = f"{self.sanitize_filename(entry_title)}.md"
                index_content += f"- [{entry_title}]({entry_filename})\n"
                
                # Sync individual entry
                self.sync_page(entry, db_dir)
            
            # Save index file
            index_path = db_dir / "README.md"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            print(f"Synced database: {db_title} ({len(entries)} entries)")
            
        except Exception as e:
            print(f"Error syncing database {db_title}: {e}")
    
    def sync_all(self, output_dir: str = "."):
        """Sync all accessible Notion content"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Get all pages and databases
        results = self.search_pages()
        
        pages = [r for r in results if r['object'] == 'page']
        databases = [r for r in results if r['object'] == 'database']
        
        print(f"Found {len(pages)} pages and {len(databases)} databases")
        
        # Sync pages
        if pages:
            pages_dir = output_path / "pages"
            pages_dir.mkdir(exist_ok=True)
            
            for page in pages:
                # Skip pages that are part of databases
                if page['parent']['type'] != 'database_id':
                    self.sync_page(page, pages_dir)
        
        # Sync databases
        if databases:
            databases_dir = output_path / "databases"
            databases_dir.mkdir(exist_ok=True)
            
            for database in databases:
                self.sync_database(database, databases_dir)


if __name__ == "__main__":
    import sys
    
    # Get Notion token from environment or command line
    notion_token = os.environ.get('NOTION_TOKEN')
    if not notion_token and len(sys.argv) > 1:
        notion_token = sys.argv[1]
    
    if not notion_token:
        print("Error: Notion token required")
        print("Usage: python sync_notion.py [NOTION_TOKEN]")
        print("Or set NOTION_TOKEN environment variable")
        sys.exit(1)
    
    # Initialize syncer
    syncer = NotionSync(notion_token)
    
    # Sync all content
    try:
        syncer.sync_all()
        print("Sync completed successfully!")
    except Exception as e:
        print(f"Sync failed: {e}")
        sys.exit(1)