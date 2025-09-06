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
    
    def get_block_children(self, block_id: str) -> List[Dict]:
        """Get child blocks for a block that has children"""
        try:
            url = f'{self.base_url}/blocks/{block_id}/children'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()['results']
        except Exception as e:
            print(f"Error getting children for block {block_id}: {e}")
            return []
    
    def block_to_markdown(self, block: Dict, depth: int = 0) -> str:
        """Convert a Notion block to markdown"""
        block_type = block['type']
        indent = "  " * depth  # For nested content
        
        if block_type == 'paragraph':
            text = self.rich_text_to_markdown(block['paragraph']['rich_text'])
            result = f"{indent}{text}\n\n" if text.strip() else ""
            
        elif block_type == 'heading_1':
            text = self.rich_text_to_markdown(block['heading_1']['rich_text'])
            result = f"{'#' * (1 + depth)} {text}\n\n"
            
        elif block_type == 'heading_2':
            text = self.rich_text_to_markdown(block['heading_2']['rich_text'])
            result = f"{'#' * (2 + depth)} {text}\n\n"
            
        elif block_type == 'heading_3':
            text = self.rich_text_to_markdown(block['heading_3']['rich_text'])
            result = f"{'#' * (3 + depth)} {text}\n\n"
        
        elif block_type == 'toggle':
            # Handle toggle blocks (collapsible sections)
            text = self.rich_text_to_markdown(block['toggle']['rich_text'])
            result = f"{'#' * (3 + depth)} {text}\n\n"  # Treat toggle title as a heading
            
        elif block_type == 'bulleted_list_item':
            text = self.rich_text_to_markdown(block['bulleted_list_item']['rich_text'])
            result = f"{indent}- {text}\n"
            
        elif block_type == 'numbered_list_item':
            text = self.rich_text_to_markdown(block['numbered_list_item']['rich_text'])
            result = f"{indent}1. {text}\n"
            
        elif block_type == 'to_do':
            text = self.rich_text_to_markdown(block['to_do']['rich_text'])
            checked = block['to_do']['checked']
            checkbox = "[x]" if checked else "[ ]"
            result = f"{indent}- {checkbox} {text}\n"
            
        elif block_type == 'quote':
            text = self.rich_text_to_markdown(block['quote']['rich_text'])
            result = f"{indent}> {text}\n\n"
            
        elif block_type == 'callout':
            text = self.rich_text_to_markdown(block['callout']['rich_text'])
            icon = block['callout'].get('icon', {})
            if icon and icon.get('type') == 'emoji':
                emoji = icon.get('emoji', '📌')
                result = f"{indent}> {emoji} {text}\n\n"
            else:
                result = f"{indent}> {text}\n\n"
            
        elif block_type == 'divider':
            result = f"{indent}---\n\n"
            
        elif block_type == 'code':
            text = self.rich_text_to_markdown(block['code']['rich_text'])
            language = block['code'].get('language', '')
            result = f"{indent}```{language}\n{text}\n```\n\n"
            
        elif block_type == 'table':
            result = f"{indent}[Table content - {block['table']['table_width']} columns]\n\n"
            
        elif block_type == 'table_row':
            cells = block['table_row']['cells']
            row_text = " | ".join([self.rich_text_to_markdown(cell) for cell in cells])
            result = f"{indent}| {row_text} |\n"
            
        else:
            # For unsupported block types, try to extract text
            if block_type in block and isinstance(block[block_type], dict):
                block_data = block[block_type]
                if 'rich_text' in block_data:
                    text = self.rich_text_to_markdown(block_data['rich_text'])
                    if text.strip():
                        result = f"{indent}{text}\n\n"
                    else:
                        result = ""
                else:
                    result = f"{indent}[Unsupported block type: {block_type}]\n\n"
            else:
                result = ""
        
        # Handle nested content (children blocks)
        if block.get('has_children', False):
            children = self.get_block_children(block['id'])
            for child in children:
                result += self.block_to_markdown(child, depth + (1 if block_type in ['toggle', 'bulleted_list_item', 'numbered_list_item', 'to_do'] else 0))
        
        return result
    
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
    
    def extract_property_value(self, property_data: Dict) -> str:
        """Extract value from a Notion property based on its type"""
        prop_type = property_data['type']
        
        if prop_type == 'title':
            if property_data['title']:
                return self.rich_text_to_markdown(property_data['title'])
            return ""
        
        elif prop_type == 'rich_text':
            if property_data['rich_text']:
                return self.rich_text_to_markdown(property_data['rich_text'])
            return ""
        
        elif prop_type == 'number':
            return str(property_data['number']) if property_data['number'] is not None else ""
        
        elif prop_type == 'select':
            return property_data['select']['name'] if property_data['select'] else ""
        
        elif prop_type == 'multi_select':
            if property_data['multi_select']:
                return ', '.join([item['name'] for item in property_data['multi_select']])
            return ""
        
        elif prop_type == 'date':
            if property_data['date']:
                start = property_data['date']['start']
                end = property_data['date'].get('end')
                if end:
                    return f"{start} to {end}"
                return start
            return ""
        
        elif prop_type == 'checkbox':
            return "✓" if property_data['checkbox'] else "✗"
        
        elif prop_type == 'url':
            return property_data['url'] if property_data['url'] else ""
        
        elif prop_type == 'email':
            return property_data['email'] if property_data['email'] else ""
        
        elif prop_type == 'phone_number':
            return property_data['phone_number'] if property_data['phone_number'] else ""
        
        elif prop_type == 'people':
            if property_data['people']:
                return ', '.join([person['name'] for person in property_data['people']])
            return ""
        
        elif prop_type == 'files':
            if property_data['files']:
                return ', '.join([file['name'] for file in property_data['files']])
            return ""
        
        elif prop_type == 'status':
            return property_data['status']['name'] if property_data['status'] else ""
        
        elif prop_type == 'formula':
            # Formula results can be different types
            if property_data['formula']:
                formula_type = property_data['formula']['type']
                if formula_type == 'string':
                    return property_data['formula']['string'] or ""
                elif formula_type == 'number':
                    return str(property_data['formula']['number']) if property_data['formula']['number'] is not None else ""
                elif formula_type == 'boolean':
                    return "✓" if property_data['formula']['boolean'] else "✗"
                elif formula_type == 'date':
                    if property_data['formula']['date']:
                        return property_data['formula']['date']['start']
            return ""
        
        elif prop_type == 'relation':
            # For now, just return count of relations
            if property_data['relation']:
                return f"{len(property_data['relation'])} related items"
            return ""
        
        elif prop_type == 'rollup':
            # Rollup can contain various types
            if property_data['rollup'] and property_data['rollup']['array']:
                return f"{len(property_data['rollup']['array'])} items"
            return ""
        
        else:
            # For unsupported property types, try to extract basic info
            return f"[{prop_type}]"
    
    def format_database_entry_properties(self, entry: Dict) -> str:
        """Format all properties of a database entry as markdown"""
        properties = entry['properties']
        content = ""
        
        # Skip the title property as it's used as the main heading
        for prop_name, prop_data in properties.items():
            if prop_data['type'] == 'title':
                continue  # Skip title as it's used as the heading
            
            value = self.extract_property_value(prop_data)
            if value:  # Only include properties with values
                content += f"**{prop_name}:** {value}\n\n"
        
        return content
    
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
            # Start with title
            markdown_content = f"# {title}\n\n"
            
            # If this is a database entry, include its properties
            if page['object'] == 'page' and page['parent']['type'] == 'database_id':
                properties_content = self.format_database_entry_properties(page)
                if properties_content:
                    markdown_content += properties_content
            
            # Get page content (blocks)
            content_data = self.get_page_content(page_id)
            blocks = content_data['results']
            
            # Convert blocks to markdown
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
                # Get database schema to understand properties
                db_properties = database.get('properties', {})
                
                # Create a table showing key properties for all entries
                if len(entries) > 0:
                    # Determine which properties to show in the table (limit to most important ones)
                    key_properties = []
                    for prop_name, prop_config in db_properties.items():
                        if prop_config['type'] in ['title', 'rich_text', 'select', 'url', 'number', 'checkbox', 'date']:
                            key_properties.append(prop_name)
                        if len(key_properties) >= 4:  # Limit to 4 columns for readability
                            break
                    
                    if key_properties:
                        # Create table header
                        header = "| " + " | ".join(key_properties) + " |\n"
                        separator = "|" + "|".join([" --- " for _ in key_properties]) + "|\n"
                        index_content += header + separator
                        
                        # Add table rows
                        for entry in entries:
                            row_values = []
                            for prop_name in key_properties:
                                if prop_name in entry['properties']:
                                    value = self.extract_property_value(entry['properties'][prop_name])
                                    # Truncate long values and escape pipes
                                    value = value.replace('|', '\\|').replace('\n', ' ')[:50]
                                    if len(value) > 47:
                                        value = value[:47] + "..."
                                    row_values.append(value or "-")
                                else:
                                    row_values.append("-")
                            
                            index_content += "| " + " | ".join(row_values) + " |\n"
                        
                        index_content += "\n"
                
                index_content += "## Individual Entries\n\n"
                
                for entry in entries:
                    entry_title = self.get_page_title(entry)
                    entry_filename = f"{self.sanitize_filename(entry_title)}.md"
                    
                    # Add a brief preview of key properties
                    preview = ""
                    if 'Answer' in entry['properties']:
                        answer_value = self.extract_property_value(entry['properties']['Answer'])
                        if answer_value:
                            preview = f" - {answer_value[:100]}{'...' if len(answer_value) > 100 else ''}"
                    elif 'url' in entry['properties']:
                        url_value = self.extract_property_value(entry['properties']['url'])
                        if url_value:
                            preview = f" - {url_value}"
                    
                    index_content += f"- [{entry_title}]({entry_filename}){preview}\n"
                    
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
    from pathlib import Path
    
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
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