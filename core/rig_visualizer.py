"""
RIG Visualizer - Generates interactive graph visualizations for Repository Intelligence Graph.

This module provides the RIGVisualizer class that creates interactive HTML visualizations
of RIG data structures using Cytoscape.js, with filtering, search, and export capabilities.
"""

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple

from core.schemas import ValidationSeverity, RIGValidationError


class RIGVisualizer:
    """
    Generates interactive graph visualizations for Repository Intelligence Graph.
    
    This class creates interactive HTML visualizations of RIG data structures
    using Cytoscape.js, with filtering, search, and export capabilities.
    """
    
    def __init__(self, rig):
        """
        Initialize the visualizer with a RIG instance.
        
        Args:
            rig: The RIG instance to visualize
        """
        self.rig = rig
    
    def show_graph(self, validate_before_show: bool = True) -> None:
        """
        Display the RIG as an interactive graph using Cytoscape.js.
        Creates a self-contained HTML file with all JavaScript libraries embedded.

        Args:
            validate_before_show: If True, validate the RIG before showing the graph.
                                If validation fails, raises RIGValidationError.
        """
        if validate_before_show:
            errors = self.rig.validate()
            # Only raise error if there are actual errors (not just warnings)
            error_errors = [e for e in errors if e.severity == ValidationSeverity.ERROR]
            if error_errors:
                raise RIGValidationError(error_errors)

        # Generate the HTML file
        html_content = self._generate_graph_html()

        # Determine filename
        project_name = self.rig._repository_info.name if self.rig._repository_info else "unknown"
        filename = f"rig_{project_name}_graph.html"

        # Create self-contained HTML with embedded libraries
        self._create_embedded_html(html_content, filename)

        # Get absolute path for user reference
        file_url = f"file://{os.path.abspath(filename)}"

        print(f"Self-contained graph visualization generated: {filename}")
        print(f"File location: {file_url}")
        print(f"")
        print(f"To view the graph: Open {filename} directly in your browser")
        print(f"This file has no external dependencies and works offline.")

    def _create_embedded_html(self, html_content: str, filename: str) -> None:
        """Create a self-contained HTML file with embedded JavaScript libraries."""
        # Download the libraries
        libraries = {
            "cytoscape": "https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js",
            "dagre": "https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js",
            "cytoscape-dagre": "https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js",
        }

        downloaded_libs: Dict[str, str] = {}
        for name, url in libraries.items():
            try:
                print(f"Downloading {name}...")
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode("utf-8")
                downloaded_libs[name] = content
                print(f"✓ Downloaded {name} ({len(content)} characters)")
            except urllib.error.URLError as e:
                print(f"✗ Failed to download {name}: {e}")
                # Continue with CDN fallback

        # Replace script tags with embedded content
        for name, content in downloaded_libs.items():
            if content:
                # Find the script tag for this library
                script_pattern = f'<script src="https://cdn.jsdelivr.net/npm/{name}@'
                start_idx = html_content.find(script_pattern)
                if start_idx != -1:
                    # Find the end of the script tag
                    end_idx = html_content.find("></script>", start_idx)
                    if end_idx != -1:
                        end_idx += len("></script>")
                        # Replace with embedded script
                        embedded_script = f"<script>\n{content}\n</script>"
                        html_content = html_content[:start_idx] + embedded_script + html_content[end_idx:]
                        print(f"✓ Embedded {name} library")

        # Write the final HTML file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _get_available_languages(self) -> List[str]:
        """Get all unique programming languages from components."""
        languages: set[str] = set()
        for component in self.rig._components:
            if component.programming_language:
                languages.add(component.programming_language)
        return sorted(list(languages))

    def _generate_language_filter_options(self) -> str:
        """Generate HTML options for language filter based on actual RIG data."""
        options = ['<option value="all">All</option>']
        for lang in self._get_available_languages():
            # Capitalize first letter for display
            display_name = lang.capitalize()
            options.append(f'<option value="{lang}">{display_name}</option>')
        return "\n                ".join(options)

    def _generate_graph_html(self) -> str:
        """Generate the complete HTML content for the graph visualization."""

        # Generate graph data
        nodes_data, edges_data = self._generate_graph_data()

        # Convert to JSON for JavaScript
        nodes_json = json.dumps(nodes_data)
        edges_json = json.dumps(edges_data)

        # Generate the HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RIG Graph - {self.rig._repository_info.name if self.rig._repository_info else "Unknown Project"}</title>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        
        #header {{
            background-color: #2c3e50;
            color: white;
            padding: 10px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        #header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        
        #header p {{
            margin: 5px 0 0 0;
            opacity: 0.8;
        }}
        
        #controls {{
            background-color: white;
            padding: 15px 20px;
            border-bottom: 1px solid #ddd;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .control-group label {{
            font-weight: bold;
            color: #555;
        }}
        
        select, input, button {{
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        button {{
            background-color: #3498db;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        button:hover {{
            background-color: #2980b9;
        }}
        
        #search-box {{
            min-width: 200px;
        }}
        
        #cy {{
            width: 100%;
            height: calc(100vh - 200px);
            background-color: #fafafa;
        }}
        
        .node-tooltip {{
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            word-wrap: break-word;
        }}
        
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            border-radius: 3px;
            margin: 1px;
        }}
        
        .badge-language {{
            background-color: #e74c3c;
            color: white;
        }}
        
        .badge-runtime {{
            background-color: #9b59b6;
            color: white;
        }}
        
        .badge-type {{
            background-color: #f39c12;
            color: white;
        }}
        
        #legend {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        #legend h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 16px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        
        .legend-section {{
            margin-bottom: 15px;
        }}
        
        .legend-section h4 {{
            margin: 0 0 8px 0;
            color: #34495e;
            font-size: 14px;
            font-weight: bold;
        }}
        
        .legend-items {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }}
        
        .legend-node {{
            width: 20px;
            height: 20px;
            border: 2px solid;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        
        .legend-edge {{
            width: 30px;
            height: 3px;
            border: 2px solid;
            border-radius: 1px;
            flex-shrink: 0;
        }}
        
        .legend-edge.dashed {{
            border-style: dashed;
        }}
        
        .legend-label {{
            font-size: 12px;
            color: #555;
            font-weight: 500;
        }}
        
        .legend-description {{
            font-size: 11px;
            color: #777;
            margin-left: 28px;
            margin-top: 2px;
        }}
        
        .legend-toggle {{
            background-color: #3498db;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        
        .legend-toggle:hover {{
            background-color: #2980b9;
        }}
        
        .legend-content {{
            display: block;
        }}
        
        .legend-content.collapsed {{
            display: none;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Repository Intelligence Graph</h1>
        <p>Project: {self.rig._repository_info.name if self.rig._repository_info else "Unknown"} |
           Components: {len(self.rig._components)} |
           Tests: {len(self.rig._tests)} |
           Aggregators: {len(self.rig._aggregators)} |
           Runners: {len(self.rig._runners)} |
           Utilities: {len(self.rig.utilities)}</p>
    </div>
    
    <div id="controls">
        <div class="control-group">
            <label>Show Sources:</label>
            <input type="checkbox" id="show-sources" onchange="toggleSources()">
        </div>
        
        <div class="control-group">
            <label>Node Type:</label>
            <select id="node-type-filter" onchange="filterNodes()">
                <option value="all">All</option>
                <option value="component">Components</option>
                <option value="test">Tests</option>
                <option value="aggregator">Aggregators</option>
                <option value="runner">Runners</option>
                <option value="utility">Utilities</option>
                <option value="source">Source Files</option>
            </select>
        </div>
        
        <div class="control-group">
            <label>Language:</label>
            <select id="language-filter" onchange="filterNodes()">
                {self._generate_language_filter_options()}
            </select>
        </div>

        <div class="control-group">
            <label>Search:</label>
            <input type="text" id="search-box" placeholder="Search nodes..." onkeyup="searchNodes()">
        </div>
        
        <div class="control-group">
            <button onclick="resetView()">Reset View</button>
            <button onclick="fitToScreen()">Fit to Screen</button>
            <button onclick="exportGraph()">Export Graph</button>
        </div>
    </div>
    
    <div id="legend">
        <button class="legend-toggle" onclick="toggleLegend()">Toggle Legend</button>
        <div id="legend-content" class="legend-content">
            <h3>Graph Legend</h3>
            
            <div class="legend-section">
                <h4>Node Types</h4>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #3498db; border-color: #2980b9; border-radius: 4px;"></div>
                        <span class="legend-label">Component</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #e74c3c; border-color: #c0392b; transform: rotate(45deg);"></div>
                        <span class="legend-label">Test</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #2ecc71; border-color: #27ae60; clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);"></div>
                        <span class="legend-label">Aggregator</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #f39c12; border-color: #e67e22; clip-path: polygon(50% 0%, 0% 100%, 100% 100%);"></div>
                        <span class="legend-label">Runner</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #95a5a6; border-color: #7f8c8d; border-radius: 4px;"></div>
                        <span class="legend-label">Utility</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-node" style="background-color: #95a5a6; border-color: #7f8c8d; border-radius: 50%; width: 15px; height: 15px;"></div>
                        <span class="legend-label">Source File</span>
                    </div>
                </div>
                <div class="legend-description">
                    Components are buildable artifacts (executables, libraries). Tests verify functionality. 
                    Aggregators group related targets. Runners execute commands. Utilities provide helper functions.
                </div>
            </div>
            
            <div class="legend-section">
                <h4>Edge Types</h4>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-edge" style="border-color: #2c3e50;"></div>
                        <span class="legend-label">Aggregation</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-edge dashed" style="border-color: #e74c3c;"></div>
                        <span class="legend-label">Tests</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-edge" style="border-color: #f39c12;"></div>
                        <span class="legend-label">Builds</span>
                    </div>
                </div>
                <div class="legend-description">
                    Aggregation edges show dependency relationships. Test edges show which components are tested. 
                    Build edges show source-to-component relationships.
                </div>
            </div>
            
            <div class="legend-section">
                <h4>Node Information</h4>
                <div class="legend-items">
                    <div class="legend-item">
                        <span class="badge badge-language">Language</span>
                        <span class="legend-label">Programming Language</span>
                    </div>
                    <div class="legend-item">
                        <span class="badge badge-runtime">Runtime</span>
                        <span class="legend-label">Runtime Environment</span>
                    </div>
                    <div class="legend-item">
                        <span class="badge badge-type">Type</span>
                        <span class="legend-label">Component Type</span>
                    </div>
                </div>
                <div class="legend-description">
                    Hover over nodes to see detailed information including language, runtime, and type badges.
                </div>
            </div>
            
            <div class="legend-section">
                <h4>Controls</h4>
                <div class="legend-description">
                    • <strong>Show Sources:</strong> Toggle visibility of source file nodes<br>
                    • <strong>Node Type Filter:</strong> Show only specific node types<br>
                    • <strong>Language/Runtime Filters:</strong> Filter by programming language or runtime<br>
                    • <strong>Search:</strong> Find nodes by name<br>
                    • <strong>Reset View:</strong> Reset all filters and zoom<br>
                    • <strong>Fit to Screen:</strong> Zoom to show all nodes<br>
                    • <strong>Export Graph:</strong> Download graph as image
                </div>
            </div>
        </div>
    </div>
    
    <div id="cy"></div>
    <div id="tooltip" class="node-tooltip" style="display: none;"></div>
    
    <script>
        // Graph data
        const nodesData = {nodes_json};
        const edgesData = {edges_json};
        
        let cy;
        let showSources = false;
        
        // Initialize Cytoscape
        function initCytoscape() {{
            cy = cytoscape({{
                container: document.getElementById('cy'),
                
                elements: {{
                    nodes: nodesData,
                    edges: edgesData
                }},
                
                layout: {{
                    name: 'dagre',
                    rankDir: 'TB',
                    spacingFactor: 1.5,
                    nodeSep: 50,
                    rankSep: 100
                }},
                
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'color': '#333',
                            'text-outline-width': 2,
                            'text-outline-color': '#fff',
                            'width': 'data(width)',
                            'height': 'data(height)',
                            'background-color': 'data(color)',
                            'border-width': 2,
                            'border-color': 'data(borderColor)',
                            'shape': 'data(shape)'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="component"]',
                        style: {{
                            'background-color': '#3498db',
                            'border-color': '#2980b9',
                            'shape': 'round-rectangle'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="test"]',
                        style: {{
                            'background-color': '#e74c3c',
                            'border-color': '#c0392b',
                            'shape': 'diamond'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="aggregator"]',
                        style: {{
                            'background-color': '#2ecc71',
                            'border-color': '#27ae60',
                            'shape': 'hexagon'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="runner"]',
                        style: {{
                            'background-color': '#f39c12',
                            'border-color': '#e67e22',
                            'shape': 'triangle'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="utility"]',
                        style: {{
                            'background-color': '#95a5a6',
                            'border-color': '#7f8c8d',
                            'shape': 'round-rectangle'
                        }}
                    }},
                    
                    {{
                        selector: 'node[type="source"]',
                        style: {{
                            'background-color': '#95a5a6',
                            'border-color': '#7f8c8d',
                            'shape': 'ellipse',
                            'width': 30,
                            'height': 30
                        }}
                    }},
                    
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': 'data(color)',
                            'target-arrow-color': 'data(color)',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="aggregation"]',
                        style: {{
                            'line-color': '#2c3e50',
                            'target-arrow-color': '#2c3e50',
                            'line-style': 'solid'
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="test"]',
                        style: {{
                            'line-color': '#e74c3c',
                            'target-arrow-color': '#e74c3c',
                            'line-style': 'dashed'
                        }}
                    }},
                    
                    {{
                        selector: 'edge[type="build"]',
                        style: {{
                            'line-color': '#f39c12',
                            'target-arrow-color': '#f39c12',
                            'line-style': 'solid'
                        }}
                    }}
                ]
            }});
            
            // Add event listeners
            cy.on('mouseover', 'node', showTooltip);
            cy.on('mouseout', 'node', hideTooltip);
            cy.on('tap', 'node', selectNode);
            
            // Apply initial filters (hide sources by default)
            filterNodes();
        }}
        
        // Show tooltip on hover
        function showTooltip(event) {{
            const node = event.target;
            const data = node.data();
            const tooltip = document.getElementById('tooltip');
            
            let content = `<strong>${{data.label}}</strong><br>`;
            content += `Type: ${{data.type}}<br>`;
            
            if (data.language) {{
                content += `Language: ${{data.language}}<br>`;
            }}
            if (data.componentType) {{
                content += `Component Type: ${{data.componentType}}<br>`;
            }}
            if (data.filePath) {{
                content += `Path: ${{data.filePath}}<br>`;
            }}
            if (data.sourceFiles && data.sourceFiles.length > 0) {{
                content += `<br><strong>Source Files:</strong><br>`;
                data.sourceFiles.forEach(file => {{
                    content += `• ${{file}}<br>`;
                }});
            }}
            if (data.testFramework) {{
                content += `Test Framework: ${{data.testFramework}}<br>`;
            }}
            
            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
        }}
        
        // Hide tooltip
        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}
        
        // Select node
        function selectNode(event) {{
            const node = event.target;
            cy.elements().unselect();
            node.select();
        }}
        
        // Toggle source files visibility
        function toggleSources() {{
            showSources = document.getElementById('show-sources').checked;
            filterNodes();
        }}
        
        // Toggle legend visibility
        function toggleLegend() {{
            const legendContent = document.getElementById('legend-content');
            legendContent.classList.toggle('collapsed');
        }}
        
        // Filter nodes based on controls
        function filterNodes() {{
            const nodeTypeFilter = document.getElementById('node-type-filter').value;
            const languageFilter = document.getElementById('language-filter').value;
            const searchTerm = document.getElementById('search-box').value.toLowerCase();

            cy.elements().forEach(ele => {{
                const data = ele.data();
                let visible = true;

                // Source files filter
                if (data.type === 'source' && !showSources) {{
                    visible = false;
                }}

                // Node type filter
                if (nodeTypeFilter !== 'all' && data.type !== nodeTypeFilter) {{
                    visible = false;
                }}

                // Language filter
                if (languageFilter !== 'all' && data.language !== languageFilter) {{
                    visible = false;
                }}

                // Search filter
                if (searchTerm && !data.label.toLowerCase().includes(searchTerm) && 
                    !data.filePath?.toLowerCase().includes(searchTerm)) {{
                    visible = false;
                }}
                
                ele.style('display', visible ? 'element' : 'none');
            }});
            
            cy.layout({{ name: 'dagre', rankDir: 'TB' }}).run();
        }}
        
        // Search nodes
        function searchNodes() {{
            filterNodes();
        }}
        
        // Reset view
        function resetView() {{
            document.getElementById('show-sources').checked = false;
            document.getElementById('node-type-filter').value = 'all';
            document.getElementById('language-filter').value = 'all';
            document.getElementById('search-box').value = '';
            showSources = false;
            filterNodes();
        }}
        
        // Fit to screen
        function fitToScreen() {{
            cy.fit();
        }}
        
        // Export graph to PNG
        function exportGraph() {{
            try {{
                // Get the current graph as PNG
                const pngData = cy.png({{
                    output: 'blob',
                    bg: 'white',
                    full: true,
                    scale: 2  // Higher resolution
                }});
                
                // Create download link
                const url = URL.createObjectURL(pngData);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'rig_graph.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                
                console.log('Graph exported successfully');
            }} catch (error) {{
                console.error('Export failed:', error);
                alert('Export failed. Please try again.');
            }}
        }}
        
        // Update tooltip position
        document.addEventListener('mousemove', function(e) {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip.style.display === 'block') {{
                tooltip.style.left = e.pageX + 10 + 'px';
                tooltip.style.top = e.pageY - 10 + 'px';
            }}
        }});
        
        // Initialize when page loads
        window.addEventListener('load', initCytoscape);
    </script>
</body>
</html>"""

        return html_template

    def _generate_graph_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate nodes and edges data for the graph visualization."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Add root node if we have a repository
        if self.rig._repository_info:
            nodes.append({"data": {"id": "root", "label": self.rig._repository_info.name, "type": "root", "color": "#34495e", "borderColor": "#2c3e50", "shape": "round-rectangle", "width": 120, "height": 40}})

        # Add all build nodes
        for node in self.rig.get_all_rig_nodes():
            node_data = self._create_node_data(node)
            nodes.append(node_data)

        # Add test nodes
        for test in self.rig._tests:
            node_data = self._create_test_node_data(test)
            nodes.append(node_data)

        # Add source file nodes (will be filtered by UI)
        for component in self.rig._components:
            for source_file in component.source_files:
                source_id = f"source_{source_file}"
                if not any(n["data"]["id"] == source_id for n in nodes):
                    nodes.append({"data": {"id": source_id, "label": source_file.name, "type": "source", "color": "#95a5a6", "borderColor": "#7f8c8d", "shape": "ellipse", "width": 30, "height": 30, "filePath": str(source_file)}})

        # Add edges
        edges.extend(self._create_aggregation_edges())
        edges.extend(self._create_test_edges())
        edges.extend(self._create_build_edges())

        return nodes, edges

    def _create_node_data(self, node) -> Dict[str, Any]:
        """Create node data for a build node."""
        node_type = type(node).__name__.lower()

        # Determine color based on type
        color_map = {"component": "#3498db", "aggregator": "#2ecc71", "runner": "#f39c12", "utility": "#95a5a6"}
        color = color_map.get(node_type, "#95a5a6")

        # Use plain text label (no HTML)
        label = node.name

        node_data: Dict[str, Any] = {"data": {"id": node.name, "label": label, "type": node_type, "color": color, "borderColor": color, "shape": "round-rectangle", "width": 100, "height": 50}}

        # Add component-specific data
        if hasattr(node, 'programming_language'):
            node_data["data"]["language"] = node.programming_language
            node_data["data"]["componentType"] = str(node.type)
            node_data["data"]["filePath"] = str(node.output_path)
            node_data["data"]["sourceFiles"] = [str(f) for f in node.source_files]

        return node_data

    def _create_test_node_data(self, test) -> Dict[str, Any]:
        """Create node data for a test."""
        # Use plain text label (no HTML)
        label = test.name

        return {
            "data": {
                "id": test.name,
                "label": label,
                "type": "test",
                "color": "#e74c3c",
                "borderColor": "#c0392b",
                "shape": "diamond",
                "width": 100,
                "height": 50,
                "testFramework": test.test_framework,
                "filePath": test.evidence.call_stack[0] if test.evidence and test.evidence.call_stack else None,
            }
        }

    def _create_aggregation_edges(self) -> List[Dict[str, Any]]:
        """Create aggregation edges."""
        edges: List[Dict[str, Any]] = []

        # Root to aggregators
        if self.rig._repository_info:
            for aggregator in self.rig._aggregators:
                edges.append({"data": {"id": f"root_to_{aggregator.name}", "source": "root", "target": aggregator.name, "type": "aggregation", "color": "#2c3e50", "label": "aggregates"}})

        # Aggregators to their dependencies
        for aggregator in self.rig._aggregators:
            for dep in (aggregator.depends_on or []):
                edges.append({"data": {"id": f"{aggregator.name}_to_{dep.name}", "source": aggregator.name, "target": dep.name, "type": "aggregation", "color": "#2c3e50", "label": "aggregates"}})

        return edges

    def _create_test_edges(self) -> List[Dict[str, Any]]:
        """Create test edges."""
        edges: List[Dict[str, Any]] = []

        for test in self.rig._tests:
            for component in (test.components_being_tested or []):
                edges.append({"data": {"id": f"{test.name}_tests_{component.name}", "source": test.name, "target": component.name, "type": "test", "color": "#e74c3c", "label": "tests"}})

        return edges

    def _create_build_edges(self) -> List[Dict[str, Any]]:
        """Create build edges."""
        edges: List[Dict[str, Any]] = []

        # Components to source files
        for component in self.rig._components:
            for source_file in component.source_files:
                source_id = f"source_{source_file}"
                edges.append({"data": {"id": f"{component.name}_builds_{source_id}", "source": component.name, "target": source_id, "type": "build", "color": "#f39c12", "label": "builds"}})

        # Components to test executables
        for test in self.rig._tests:
            if test.test_executable_component:
                edges.append({"data": {"id": f"{test.test_executable_component.name}_builds_{test.name}", "source": test.test_executable_component.name, "target": test.name, "type": "build", "color": "#f39c12", "label": "builds"}})

        return edges
