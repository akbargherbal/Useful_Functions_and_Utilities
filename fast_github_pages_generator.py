"""
Fast GitHub Pages Static Site Generator
Generates a working website from your docs in under 20 minutes
"""

import os
import shutil
from pathlib import Path
import markdown
from datetime import datetime


class FastSiteGenerator:
    def __init__(self, source_dir=".", output_dir="docs"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.markdown_extensions = ["toc", "tables", "fenced_code", "codehilite"]

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

    def get_relative_path_to_root(self, current_path):
        """Calculate relative path from current location to root"""
        if current_path == Path("."):
            return "."
        depth = len(current_path.parts)
        return "/".join([".."] * depth) if depth > 0 else "."

    def get_html_template(self):
        """Modern, beautiful HTML template with code highlighting"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --bg-main: #0f172a;
            --bg-card: #1e293b;
            --bg-code: #0f172a;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border: #334155;
            --accent: #06b6d4;
            --success: #10b981;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.7; 
            color: var(--text-primary); 
            background: var(--bg-main);
        }}
        
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }}
        
        .home-btn {{ 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: var(--accent);
            color: white; 
            width: 50px;
            height: 50px;
            border-radius: 50%;
            text-decoration: none; 
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .home-btn:hover {{ 
            background: #0891b2;
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(6, 182, 212, 0.5);
        }}
        
        .breadcrumb {{ 
            background: var(--bg-card);
            padding: 12px 0; 
            margin-bottom: 24px; 
            font-size: 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .breadcrumb a {{ 
            color: var(--accent);
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .breadcrumb a:hover {{ 
            color: var(--primary);
            text-decoration: underline;
        }}
        
        .content {{ 
            background: var(--bg-card);
            padding: 3rem; 
            border-radius: 16px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
        }}
        
        .file-list {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 1.5rem; 
            margin: 2rem 0; 
        }}
        
        .file-item {{ 
            padding: 1.5rem; 
            border: 1px solid var(--border);
            border-radius: 12px; 
            background: var(--bg-main);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .file-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .file-item:hover {{ 
            transform: translateY(-4px); 
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
            border-color: var(--primary);
        }}
        
        .file-item:hover::before {{
            opacity: 1;
        }}
        
        .file-item a {{ 
            color: var(--text-primary);
            text-decoration: none; 
            font-weight: 600; 
            display: block;
            font-size: 1.1rem;
        }}
        
        .file-item a:hover {{ 
            color: var(--primary);
        }}
        
        .file-type {{ 
            font-size: 13px; 
            color: var(--text-secondary);
            margin-top: 8px; 
            font-weight: 500;
        }}
        
        /* Code Blocks */
        pre {{ 
            background: var(--bg-code);
            padding: 1.5rem; 
            border-radius: 12px; 
            overflow-x: auto;
            border: 1px solid var(--border);
            margin: 1.5rem 0;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }}
        
        pre code {{ 
            background: none;
            padding: 0;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.9em;
            line-height: 1.6;
        }}
        
        /* Inline Code */
        code {{ 
            background: var(--bg-code);
            color: var(--accent);
            padding: 3px 8px; 
            border-radius: 6px; 
            font-size: 0.9em;
            font-family: 'Fira Code', 'Consolas', monospace;
            border: 1px solid var(--border);
        }}
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {{ 
            color: var(--text-primary);
            margin: 2rem 0 1rem 0;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        
        h1 {{ 
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            border-bottom: 3px solid var(--primary);
            padding-bottom: 12px;
            margin-bottom: 1.5rem;
        }}
        
        h2 {{ 
            font-size: 2rem;
            color: var(--primary);
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
        }}
        
        h3 {{ 
            font-size: 1.5rem;
            color: var(--accent);
        }}
        
        /* Links */
        a {{ 
            color: var(--accent);
            transition: color 0.2s;
        }}
        
        a:hover {{ 
            color: var(--primary);
        }}
        
        /* Paragraphs */
        p {{
            margin: 1rem 0;
            color: var(--text-secondary);
        }}
        
        /* Lists */
        ul, ol {{
            margin: 1rem 0;
            padding-left: 2rem;
            color: var(--text-secondary);
        }}
        
        li {{
            margin: 0.5rem 0;
        }}
        
        /* Tables */
        table {{ 
            border-collapse: collapse;
            width: 100%;
            margin: 1.5rem 0;
            background: var(--bg-main);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }}
        
        th, td {{ 
            border: 1px solid var(--border);
            padding: 12px 16px;
            text-align: left;
        }}
        
        th {{ 
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: var(--bg-card);
        }}
        
        /* Blockquotes */
        blockquote {{
            border-left: 4px solid var(--primary);
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            background: var(--bg-main);
            border-radius: 0 8px 8px 0;
            color: var(--text-secondary);
            font-style: italic;
        }}
        
        /* Horizontal Rule */
        hr {{
            border: none;
            border-top: 2px solid var(--border);
            margin: 2rem 0;
        }}
        
        .footer {{ 
            text-align: center; 
            padding: 2rem; 
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 3rem; 
            font-size: 14px;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-main);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 6px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--primary);
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .file-list {{ grid-template-columns: 1fr; }}
            .content {{ padding: 1.5rem; }}
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <a href="{home_path}" class="home-btn">🏠</a>
    <div class="container">
        <div class="breadcrumb">
            <div style="padding: 0 20px;">
                {breadcrumb}
            </div>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            Generated on {timestamp} | Made with ❤️ by GitHub Pages Generator
        </div>
    </div>
    <script>
        // Syntax highlighting for code blocks
        document.addEventListener('DOMContentLoaded', (event) => {{
            document.querySelectorAll('pre code').forEach((block) => {{
                hljs.highlightElement(block);
            }});
        }});
    </script>
</body>
</html>"""

    def create_breadcrumb(self, current_path):
        """Create breadcrumb navigation with relative paths"""
        path_to_root = self.get_relative_path_to_root(current_path)

        # Home link is always relative to root
        breadcrumb = f'<a href="{path_to_root}/index.html">🏠 Home</a>'

        if current_path == Path("."):
            return breadcrumb

        parts = current_path.parts
        for i, part in enumerate(parts):
            # Calculate how many levels to go up from current location
            levels_up = len(parts) - i - 1
            if levels_up > 0:
                path = "/".join([".."] * levels_up) + "/index.html"
            else:
                path = "index.html"

            breadcrumb += (
                f' <span style="color: #64748b;">/</span> <a href="{path}">{part}</a>'
            )

        return breadcrumb

    def process_markdown(self, md_path, relative_path):
        """Convert markdown to HTML"""
        with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        md = markdown.Markdown(extensions=self.markdown_extensions)
        html_content = md.convert(content)

        # Calculate path to root for home button
        parent_path = relative_path.parent
        path_to_root = self.get_relative_path_to_root(parent_path)
        home_path = f"{path_to_root}/index.html"

        # Create breadcrumb
        breadcrumb = self.create_breadcrumb(parent_path)

        # Generate HTML
        html = self.get_html_template().format(
            title=md_path.stem,
            breadcrumb=breadcrumb,
            content=html_content,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            home_path=home_path,
        )

        return html

    def create_directory_listing(self, dir_path, relative_path):
        """Create directory listing page with relative paths"""
        files = []
        dirs = []

        for item in sorted(dir_path.iterdir()):
            if item.name.startswith(".") or item.name == self.output_dir.name:
                continue

            if item.is_dir():
                # Relative path to subdirectory
                dirs.append(
                    {
                        "name": item.name,
                        "path": f"{item.name}/index.html",
                        "type": "📁 Directory",
                    }
                )
            elif item.suffix.lower() in [".md", ".txt"]:
                # Relative path to file
                files.append(
                    {
                        "name": item.name,
                        "path": f"{item.stem}.html",
                        "type": f"📄 {item.suffix.upper()} File",
                    }
                )

        # Create content
        title = relative_path.name if relative_path.name else "Documentation"
        content = f"<h1>📚 {title.replace('_', ' ').replace('-', ' ').title()}</h1>"
        content += f"<p style='color: #94a3b8; margin-bottom: 2rem;'>Browse through the available documentation files and folders.</p>"

        if dirs or files:
            content += '<div class="file-list">'

            # Directories first
            for dir_info in dirs:
                content += f"""
                <div class="file-item">
                    <a href="{dir_info['path']}">{dir_info['name']}/</a>
                    <div class="file-type">{dir_info['type']}</div>
                </div>"""

            # Then files
            for file_info in files:
                content += f"""
                <div class="file-item">
                    <a href="{file_info['path']}">{file_info['name']}</a>
                    <div class="file-type">{file_info['type']}</div>
                </div>"""

            content += "</div>"
        else:
            content += (
                '<p style="color: #64748b;">No files found in this directory.</p>'
            )

        # Calculate path to root for home button
        path_to_root = self.get_relative_path_to_root(relative_path)
        home_path = f"{path_to_root}/index.html"

        breadcrumb = self.create_breadcrumb(relative_path)

        html = self.get_html_template().format(
            title=relative_path.name if relative_path.name else "Home",
            breadcrumb=breadcrumb,
            content=content,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            home_path=home_path,
        )

        return html

    def generate_site(self):
        """Generate the complete static site"""
        print("🚀 Starting fast site generation...")

        # Clean output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir()

        # Create .nojekyll file for GitHub Pages
        (self.output_dir / ".nojekyll").touch()

        # Process all directories and files
        for root, dirs, files in os.walk(self.source_dir):
            root_path = Path(root)

            # Calculate relative path
            if root_path == self.source_dir:
                relative_path = Path(".")
            else:
                relative_path = root_path.relative_to(self.source_dir)

            # Skip hidden directories and output directory
            if any(
                part.startswith(".") or part == self.output_dir.name
                for part in relative_path.parts
            ):
                continue

            # Skip the output directory itself
            if root_path == self.output_dir or self.output_dir in root_path.parents:
                continue

            output_dir_path = (
                self.output_dir / relative_path
                if relative_path != Path(".")
                else self.output_dir
            )
            output_dir_path.mkdir(parents=True, exist_ok=True)

            # Process markdown and text files
            for file in files:
                if file.startswith("."):
                    continue

                file_path = root_path / file
                rel_file_path = (
                    relative_path / file if relative_path != Path(".") else Path(file)
                )

                if file.lower().endswith((".md", ".txt")):
                    try:
                        html_content = self.process_markdown(file_path, rel_file_path)
                        output_file = output_dir_path / f"{Path(file).stem}.html"

                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(html_content)

                        print(f"✅ {rel_file_path}")
                    except Exception as e:
                        print(f"⚠️ Error processing {rel_file_path}: {e}")

            # Create directory listing
            try:
                dir_html = self.create_directory_listing(root_path, relative_path)
                index_file = output_dir_path / "index.html"

                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(dir_html)

                print(f"📂 {relative_path}/")
            except Exception as e:
                print(f"⚠️ Error creating directory listing for {relative_path}: {e}")

        print(f"\n🎉 Site generated successfully in '{self.output_dir}'!")
        print(f"📊 Ready for GitHub Pages deployment")


def main():
    """Main execution"""
    import sys

    # Check for required dependency
    try:
        import markdown
    except ImportError:
        print("❌ Error: 'markdown' package not found!")
        print("📦 Install it with: pip install markdown")
        sys.exit(1)

    # Parse arguments
    source_dir = "."
    output_dir = "docs"

    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    generator = FastSiteGenerator(source_dir, output_dir)
    generator.generate_site()

    print(
        """
🚀 DEPLOYMENT INSTRUCTIONS:
1. git add docs/
2. git commit -m "Add documentation site"
3. git push origin main
4. Go to GitHub repo Settings → Pages
5. Set source to "Deploy from a branch"
6. Select "main" branch and "/docs" folder
7. Save and wait ~5 minutes

Your site will be live at: https://yourusername.github.io/yourrepo/
"""
    )


if __name__ == "__main__":
    main()
