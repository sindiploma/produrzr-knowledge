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
    
    def build_hierarchy(self, results: List[Dict]) -> Dict:
        """Build a hierarchical structure from Notion pages/databases"""
        hierarchy = {
            'workspace': {'children': [], 'item': None},
            'by_id': {}
        }
        
        # First pass: index all items by ID
        for item in results:
            item_id = item['id']
            hierarchy['by_id'][item_id] = {
                'item': item,
                'children': [],
                'path': []
            }
        
        # Second pass: build parent-child relationships
        for item in results:
            item_id = item['id']
            parent = item['parent']
            
            if parent['type'] == 'workspace':
                # Top-level item
                hierarchy['workspace']['children'].append(item_id)
                hierarchy['by_id'][item_id]['path'] = [item_id]
            elif parent['type'] == 'page_id':
                parent_id = parent['page_id']
                if parent_id in hierarchy['by_id']:
                    hierarchy['by_id'][parent_id]['children'].append(item_id)
                    # Build path from root
                    parent_path = hierarchy['by_id'][parent_id]['path']
                    hierarchy['by_id'][item_id]['path'] = parent_path + [item_id]
                else:
                    # Parent not accessible, treat as top-level
                    hierarchy['workspace']['children'].append(item_id)
                    hierarchy['by_id'][item_id]['path'] = [item_id]
            elif parent['type'] == 'database_id':
                # Database entry - handle separately
                database_id = parent['database_id']
                if database_id in hierarchy['by_id']:
                    hierarchy['by_id'][database_id]['children'].append(item_id)
                    parent_path = hierarchy['by_id'][database_id]['path']
                    hierarchy['by_id'][item_id]['path'] = parent_path + [item_id]
        
        return hierarchy
    
    def get_page_title(self, page: Dict) -> str:
        """Extract title from a Notion page or database"""
        if page['object'] == 'page':
            title_prop = page['properties'].get('title', {}).get('title', [])
            if title_prop:
                return title_prop[0]['plain_text']
            else:
                # Check if it's a database entry with Name property
                name_prop = page['properties'].get('Name', {}).get('title', [])
                if name_prop:
                    return name_prop[0]['plain_text']
                return 'Untitled Page'
        elif page['object'] == 'database':
            title = page.get('title', [])
            if title:
                return title[0]['plain_text']
            return 'Untitled Database'
        
        return 'Untitled'
    
    def create_directory_structure(self, hierarchy: Dict, output_path: Path):
        """Create directory structure and sync content"""
        
        def sync_item_hierarchical(item_id: str, current_path: Path):
            item_data = hierarchy['by_id'][item_id]
            item = item_data['item']
            title = self.get_page_title(item)
            safe_title = self.sanitize_filename(title)
            
            if item['object'] == 'database':
                # Create directory for database
                db_dir = current_path / safe_title
                db_dir.mkdir(exist_ok=True)
                
                # Sync database content
                self.sync_database_hierarchical(item, db_dir, hierarchy, item_id)
                
                # Sync child pages/databases
                for child_id in item_data['children']:
                    if hierarchy['by_id'][child_id]['item']['parent']['type'] != 'database_id':
                        sync_item_hierarchical(child_id, db_dir)
            
            elif item['object'] == 'page':
                if item['parent']['type'] == 'database_id':
                    # This is a database entry, will be handled by parent database
                    return
                
                # Check if this page has children
                if item_data['children']:
                    # Create directory for page with children
                    page_dir = current_path / safe_title
                    page_dir.mkdir(exist_ok=True)
                    
                    # Sync the page content as README.md
                    self.sync_page_hierarchical(item, page_dir / "README.md")
                    
                    # Sync children
                    for child_id in item_data['children']:
                        sync_item_hierarchical(child_id, page_dir)
                else:
                    # Leaf page - sync as markdown file
                    filename = f"{safe_title}.md"
                    self.sync_page_hierarchical(item, current_path / filename)
        
        # Start with top-level items
        for root_id in hierarchy['workspace']['children']:
            sync_item_hierarchical(root_id, output_path)
    
    def sync_page_hierarchical(self, page: Dict, file_path: Path):
        """Sync a single page to specific file path"""
        page_id = page['id']
        title = self.get_page_title(page)
        
        try:
            content_data = self.get_page_content(page_id)
            blocks = content_data['results']
            
            # Convert blocks to markdown
            markdown_content = f"# {title}\n\n"
            for block in blocks:
                markdown_content += self.block_to_markdown(block)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to specified file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Synced: {title} -> {file_path.name}")
            
        except Exception as e:
            print(f"Error syncing page {title}: {e}")
    
    def sync_database_hierarchical(self, database: Dict, db_dir: Path, hierarchy: Dict, db_id: str):
        """Sync a database with hierarchical structure"""
        db_title = self.get_page_title(database)
        
        try:
            # Get database entries
            entries_data = self.get_database_entries(database['id'])
            entries = entries_data['results']
            
            # Create index file
            index_content = f"# {db_title}\n\n"
            index_content += f"This database contains {len(entries)} entries.\n\n"
            
            if entries:
                index_content += "## Entries\n\n"
                
                for entry in entries:
                    entry_title = self.get_page_title(entry)
                    entry_filename = f"{self.sanitize_filename(entry_title)}.md"
                    index_content += f"- [{entry_title}]({entry_filename})\n"
                    
                    # Sync individual entry
                    self.sync_page_hierarchical(entry, db_dir / entry_filename)
            
            # Save index file
            index_path = db_dir / "README.md"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            print(f"Synced database: {db_title} ({len(entries)} entries)")
            
        except Exception as e:
            print(f"Error syncing database {db_title}: {e}")
    
    def sync_all(self, output_dir: str = "."):
        """Sync all accessible Notion content with hierarchical structure"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Clean up old flat structure if it exists
        old_pages_dir = output_path / "pages"
        old_databases_dir = output_path / "databases"
        if old_pages_dir.exists():
            import shutil
            shutil.rmtree(old_pages_dir)
            print("Removed old flat pages/ directory")
        if old_databases_dir.exists():
            import shutil
            shutil.rmtree(old_databases_dir)
            print("Removed old flat databases/ directory")
        
        # Get all pages and databases
        results = self.search_pages()
        
        pages = [r for r in results if r['object'] == 'page']
        databases = [r for r in results if r['object'] == 'database']
        
        print(f"Found {len(pages)} pages and {len(databases)} databases")
        
        # Build hierarchical structure
        hierarchy = self.build_hierarchy(results)
        
        # Create directory structure and sync content
        self.create_directory_structure(hierarchy, output_path)


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